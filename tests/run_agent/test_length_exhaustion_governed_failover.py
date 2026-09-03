"""Causal controls for HERMES_LENGTH_EXHAUSTION_GOVERNED_FAILOVER_V1 (R5).

Incident: Hermes surfaces ``Response remained truncated after 4 continuation
attempts`` and the turn dies there, even when an authorised fallback route is
configured and available.

Traced cause (agent/conversation_loop.py, length-exhaustion ceiling exit): once
the bounded continuation budget is spent, the loop ``return``s unconditionally.
It never consults the fallback chain, so no governed failover decision is ever
made for this class of failure.

The precedent for the correct shape already exists in the same function: the
content-filter branch (#32421) escalates via ``_try_activate_fallback()``, rolls
history back to the last clean assistant turn, unmarks the continuation
scaffolding and resets the counters. Its own comment records that the loop
"used to give up with 'Response remained truncated after 3 continuation
attempts' and never consult the fallback chain".

The difference R5 must preserve: a content filter is content-deterministic, so
that branch escalates BEFORE burning retries. Length exhaustion is not —
continuations are genuinely productive — so failover belongs strictly AFTER the
bounded budget is spent.

These tests are deterministic: no provider tokens, no long generation.
``_try_activate_fallback`` is patched, so the canonical selection authority is
observed, never re-implemented here.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from hermes_constants import PARTIAL_STREAM_STUB_ID, FINISH_REASON_LENGTH


# Budget is 4 continuation attempts; a 5th length response hits the ceiling.
LENGTH_RESPONSES_TO_EXHAUST_BUDGET = 5


@pytest.fixture()
def loop_agent():
    from run_agent import AIAgent
    with (
        patch("run_agent.get_tool_definitions", return_value=[]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        a = AIAgent(
            api_key="test-key-1234567890",
            base_url="https://openrouter.ai/api/v1",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
        a.client = MagicMock()
        a._cached_system_prompt = "You are helpful."
        a._use_prompt_caching = False
        a.compression_enabled = False
        a.save_trajectories = False
        return a


def _length_stub(content):
    """A truncated response: finish_reason=length, NOT content-filtered.

    Deliberately carries no ``_content_filter_terminated`` tag — that is the
    adjacent path and must not be what rescues this one.
    """
    from tests.run_agent.test_run_agent import _mock_assistant_msg
    return SimpleNamespace(
        id=PARTIAL_STREAM_STUB_ID,
        model="test/model",
        choices=[SimpleNamespace(
            index=0,
            message=_mock_assistant_msg(content=content),
            finish_reason=FINISH_REASON_LENGTH,
        )],
        usage=None,
    )


def _run(agent, message):
    with (
        patch.object(agent, "_persist_session"),
        patch.object(agent, "_save_trajectory"),
        patch.object(agent, "_cleanup_task_resources"),
    ):
        return agent.run_conversation(message)


def _arm_fallback(agent, calls, *, succeeds=True):
    """Install a counting stand-in for the canonical activation helper."""
    agent._fallback_chain = [
        {"provider": "openrouter", "model": "anthropic/claude-sonnet-4.7"},
    ]
    agent._fallback_index = 0

    def _fake_activate(reason=None):
        calls["n"] += 1
        if not succeeds:
            return False
        agent._fallback_index = len(agent._fallback_chain)
        return True

    return patch.object(agent, "_try_activate_fallback", side_effect=_fake_activate)


class TestLengthExhaustionGovernedFailover:

    def test_ceiling_activates_governed_fallback_exactly_once(self, loop_agent):
        """CORE CONTROL (RED on the unmodified tree).

        Budget exhausted + an authorised fallback available must produce
        exactly ONE governed failover decision. Today it produces zero and the
        turn terminates with the truncation error.
        """
        from tests.run_agent.test_run_agent import _mock_response

        recovery = _mock_response(
            content="Completed on the fallback provider.", finish_reason="stop",
        )
        loop_agent.client.chat.completions.create.side_effect = [
            *[_length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)],
            recovery,
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write me a very long document")

        assert calls["n"] == 1, (
            "Length exhaustion with an authorised fallback available must make "
            "exactly one governed failover decision. "
            f"Got {calls['n']}."
        )
        assert result.get("error") != (
            "Response remained truncated after 4 continuation attempts"
        ), "The turn must not terminate on the truncation error when a fallback exists."

    def test_budget_remaining_does_not_failover_early(self, loop_agent):
        """NEGATIVE CONTROL A — continuations are productive; do not escalate
        before the bounded budget is actually spent."""
        from tests.run_agent.test_run_agent import _mock_response

        loop_agent.client.chat.completions.create.side_effect = [
            _length_stub("first part "),
            _mock_response(content="and the rest.", finish_reason="stop"),
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write something")

        assert calls["n"] == 0, (
            "A single truncation with budget remaining must continue, not fail "
            "over. Escalating here would burn the fallback on a recoverable turn."
        )
        assert result["completed"] is True

    def test_no_authorised_alternate_fails_closed(self, loop_agent):
        """NEGATIVE CONTROL B — with no fallback available the existing
        terminal behaviour must be preserved exactly. Fail closed, never open."""
        loop_agent.client.chat.completions.create.side_effect = [
            _length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)
        ]
        loop_agent._fallback_chain = []
        loop_agent._fallback_index = 0
        calls = {"n": 0}
        with patch.object(loop_agent, "_try_activate_fallback",
                          side_effect=lambda reason=None: calls.__setitem__("n", calls["n"] + 1) or False):
            result = _run(loop_agent, "write me a very long document")

        assert result.get("partial") is True
        assert result.get("error") == (
            "Response remained truncated after 4 continuation attempts"
        ), "With no authorised alternate the turn must still terminate fail-closed."

    def test_failed_activation_is_bounded_and_terminal(self, loop_agent):
        """NEGATIVE CONTROL E — if activation itself declines (pin forbids
        substitution, chain exhausted, route in cooldown), the turn must end
        terminally and must NOT retry activation in a loop."""
        loop_agent.client.chat.completions.create.side_effect = [
            _length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls, succeeds=False):
            result = _run(loop_agent, "write me a very long document")

        assert calls["n"] <= 1, (
            f"Activation must be attempted at most once at the ceiling; got {calls['n']}. "
            "More than one is unbounded retry / recursive dispatch."
        )
        assert result.get("partial") is True, (
            "A declined activation must fall through to the existing terminal "
            "behaviour, not fail open and not recurse."
        )

    def test_rollback_leaves_no_duplicate_assistant_fragments(self, loop_agent):
        """NEGATIVE CONTROL F — the rollback must not leave continuation
        scaffolding or duplicated partial text in history."""
        from tests.run_agent.test_run_agent import _mock_response

        recovery = _mock_response(
            content="Completed on the fallback provider.", finish_reason="stop",
        )
        loop_agent.client.chat.completions.create.side_effect = [
            *[_length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)],
            recovery,
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write me a very long document")

        msgs = result["messages"]
        leftovers = [
            m for m in msgs
            if isinstance(m, dict)
            and (m.get("_length_continuation_fragment")
                 or m.get("_length_continuation_nudge"))
        ]
        assert not leftovers, (
            f"Continuation scaffolding survived the failover rollback: {leftovers}"
        )

    def test_session_identity_preserved_across_failover(self, loop_agent):
        """NEGATIVE CONTROL G — failover must not fork or reset session identity."""
        from tests.run_agent.test_run_agent import _mock_response

        before = getattr(loop_agent, "session_id", None)
        recovery = _mock_response(
            content="Completed on the fallback provider.", finish_reason="stop",
        )
        loop_agent.client.chat.completions.create.side_effect = [
            *[_length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)],
            recovery,
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            _run(loop_agent, "write me a very long document")

        assert getattr(loop_agent, "session_id", None) == before, (
            "Governed failover must preserve session/correlation identity."
        )

    def test_rollback_unmarks_scaffolding_when_no_partial_text_exists(self, loop_agent):
        """NEGATIVE CONTROL F2 — kills the 'skip the unmark' mutant.

        F alone did not: when partial text exists, the rollback to the last
        clean assistant turn already discards the marked messages, so dropping
        the explicit unmark loop changed nothing observable. Here every
        truncated fragment is EMPTY, so no rollback happens and the continuation
        nudges are the only marked messages left. If the unmark is skipped they
        survive into the fallback request and re-truncate every later turn.
        """
        from tests.run_agent.test_run_agent import _mock_response

        recovery = _mock_response(
            content="Completed on the fallback provider.", finish_reason="stop",
        )
        loop_agent.client.chat.completions.create.side_effect = [
            *[_length_stub("") for _ in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)],
            recovery,
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write me a very long document")

        assert calls["n"] == 1
        leftovers = [
            m for m in result["messages"]
            if isinstance(m, dict)
            and (m.get("_length_continuation_fragment")
                 or m.get("_length_continuation_nudge"))
        ]
        assert not leftovers, (
            "Continuation scaffolding must be unmarked explicitly, not merely as "
            f"a side effect of the rollback. Survivors: {leftovers}"
        )

    def test_fallback_provider_gets_a_fresh_continuation_budget(self, loop_agent):
        """NEGATIVE CONTROL H — kills the 'leave the counter dirty' mutant.

        After failover the new provider must start with a full continuation
        budget. If the counter carries over at 4, the very first truncation on
        the fallback route hits the ceiling immediately, with no alternate left
        — so the failover buys nothing and the turn still dies partial.
        """
        from tests.run_agent.test_run_agent import _mock_response

        recovery = _mock_response(
            content="Finished after one continuation on the fallback.",
            finish_reason="stop",
        )
        loop_agent.client.chat.completions.create.side_effect = [
            *[_length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)],
            _length_stub("fallback part 1 "),   # needs a fresh budget to survive
            recovery,
        ]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write me a very long document")

        assert calls["n"] == 1
        assert result["completed"] is True, (
            "The fallback provider must receive a fresh continuation budget; a "
            "carried-over counter re-hits the ceiling on its first truncation."
        )
        assert result.get("partial") is not True

    def test_fallback_first_response_is_not_intercepted_by_stale_continuation_flag(self, loop_agent):
        """NEGATIVE CONTROL I — kills the 'leave restart_with_length_continuation
        dirty' mutant (independent-review finding, not in the original mutation
        table above).

        ``_retry.restart_with_length_continuation`` is set True by the sibling
        continuation branch on each of the (up to 4) pre-ceiling truncations,
        but — unlike ``restart_with_rebuilt_messages``, ``restart_with_compressed_
        messages`` and ``restart_with_redirected_messages`` — it was never reset
        at its own consumption site. Before the governed-failover branch existed,
        that staleness was unreachable: budget exhaustion without a fallback just
        returned. This branch is what first makes a subsequent outer-loop
        iteration reachable after the flag was set earlier in the same turn.

        If the branch does not also clear the flag, the very first response from
        the fallback provider — even a completely clean, immediate success with
        no truncation at all — would be misread by the stale check as still
        needing a continuation retry, discarding the good response and issuing
        an unnecessary extra API call instead of returning it.

        This control uses a fallback response that is unambiguously terminal
        (``finish_reason="stop"``, real content) and asserts both the API-call
        count and the returned content, not just ``completed``: an extra
        superfluous call after the real one is only visible by counting calls,
        not by re-checking ``completed`` — the original core control does not
        catch this.
        """
        from tests.run_agent.test_run_agent import _mock_response

        recovery = _mock_response(
            content="Completed on the fallback provider.", finish_reason="stop",
        )
        scripted = [
            *[_length_stub(f"part {i} ") for i in range(LENGTH_RESPONSES_TO_EXHAUST_BUDGET)],
            recovery,
        ]
        loop_agent.client.chat.completions.create.side_effect = scripted
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write me a very long document")

        assert loop_agent.client.chat.completions.create.call_count == len(scripted), (
            "The fallback provider's clean, immediate success must be accepted "
            "as-is — a stale restart_with_length_continuation flag would discard "
            f"it and issue at least one more call. Expected exactly {len(scripted)} "
            f"API calls, got {loop_agent.client.chat.completions.create.call_count}."
        )
        assert result["completed"] is True
        assert result["final_response"] == "Completed on the fallback provider."

    def test_content_filter_path_still_escalates_first_pass(self, loop_agent):
        """Guards the adjacent precedent against regression: a content-filtered
        stub must STILL escalate on the first pass with zero retries burned.
        R5 must not collapse the two paths into one."""
        from tests.run_agent.test_run_agent import _mock_assistant_msg, _mock_response

        filter_stub = SimpleNamespace(
            id=PARTIAL_STREAM_STUB_ID,
            model="minimax/MiniMax-M2.7",
            choices=[SimpleNamespace(
                index=0,
                message=_mock_assistant_msg(content="Writing the file..."),
                finish_reason=FINISH_REASON_LENGTH,
            )],
            usage=None,
            _dropped_tool_names=["write_file"],
            _content_filter_terminated=True,
        )
        recovery = _mock_response(
            content="Done on the fallback provider.", finish_reason="stop",
        )
        loop_agent.client.chat.completions.create.side_effect = [filter_stub, recovery]
        calls = {"n": 0}
        with _arm_fallback(loop_agent, calls):
            result = _run(loop_agent, "write me a long file")

        assert calls["n"] == 1
        assert result["final_response"] == "Done on the fallback provider."
