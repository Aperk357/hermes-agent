"""Length-continuation budget exhaustion must fail over to the governed fallback chain.

When ``finish_reason == "length"`` survives all 4 continuation attempts, the turn ended
unconditionally with "Response remained truncated after 4 continuation attempts" — the
ceiling exit never asked whether a fallback provider was armed. A configured chain could
rescue a turn that hit a transport or content-filter failure, but not one that merely ran
out of *output budget*.

The content-filter path (``_content_filter_fallback``) already had the right shape, with
one difference that drives the design: content-filter output is poisoned, so it is rolled
back. Text truncated by the output ceiling is *good, already-paid-for* text, so the
fallback must SEE it (or it restarts the answer and the finalizer's join emits it twice)
— which means the continuation trail is kept, exactly as a recovered continuation keeps
it, and never rewritten.

Both invariant tests drive the real ``run_conversation`` loop, resolve the fallback
through the real provider-resolution chain, and persist to a real temp ``HERMES_HOME``
so the reload assertions read bytes that actually round-tripped through the session DB.
No provider is contacted: credentials are dummies and the socket layer is blocked.
"""

from __future__ import annotations

import os
import re
import socket
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from hermes_constants import FINISH_REASON_LENGTH
from run_agent import AIAgent

# --- isolation ------------------------------------------------------------
# The credential pool ingests provider keys from the environment ("Ingested
# OPENROUTER_API_KEY ... this enables OpenRouter spend"). tests/conftest.py's autouse
# `_hermetic_environment` already blanks credential-shaped vars; the scrub below repeats
# it deliberately, and the socket block is what actually proves no provider call occurs.

_LIVE_CREDENTIAL_RE = re.compile(
    r"^(?:[A-Z0-9_]*(?:API_KEY|APIKEY|AUTH_TOKEN|ACCESS_TOKEN|SECRET_KEY|_TOKEN)"
    r"|AWS_(?:ACCESS_KEY_ID|SECRET_ACCESS_KEY|SESSION_TOKEN))$"
)
_DUMMY_CREDENTIALS = {
    "OPENROUTER_API_KEY": "dummy-openrouter-key-not-a-real-credential",
    "NOUS_API_KEY": "dummy-nous-key-not-a-real-credential",
    "OPENAI_API_KEY": "dummy-openai-key-not-a-real-credential",
    "ANTHROPIC_API_KEY": "dummy-anthropic-key-not-a-real-credential",
}


class _NetworkAccessInTest(AssertionError):
    """Raised if anything under test tries to open a socket."""


@pytest.fixture(autouse=True)
def _isolated_from_live_providers(monkeypatch):
    for name in [k for k in os.environ if _LIVE_CREDENTIAL_RE.match(k)]:
        monkeypatch.delenv(name, raising=False)
    for name, value in _DUMMY_CREDENTIALS.items():
        monkeypatch.setenv(name, value)

    def _blocked(*_args, **_kwargs):
        raise _NetworkAccessInTest("This test must not reach the network or a provider.")

    # Every HTTP client in the stack bottoms out on one of these.
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


def test_the_isolation_is_real_not_decorative():
    """Control for the guard itself: it must be seen to fire, and to see a live value."""
    with pytest.raises(_NetworkAccessInTest):
        socket.create_connection(("openrouter.ai", 443))

    live = {k: v for k, v in os.environ.items()
            if _LIVE_CREDENTIAL_RE.match(k) and not v.startswith("dummy-")}
    assert not live, f"live provider credentials visible to this test: {sorted(live)}"
    os.environ["GROQ_API_KEY"] = "gsk-live-looking-value"          # detector not vacuous
    try:
        assert any(_LIVE_CREDENTIAL_RE.match(k) and not v.startswith("dummy-")
                   for k, v in os.environ.items())
    finally:
        del os.environ["GROQ_API_KEY"]


# --- fixtures -------------------------------------------------------------

PRIMARY_MODEL = "primary/model"
FALLBACK_MODEL = "fallback/model"
FALLBACK = {"provider": "openrouter", "model": FALLBACK_MODEL,
            "base_url": "https://openrouter.ai/api/v1"}
#: 3 continuation attempts then the ceiling on the 4th — see ``_continue_text``.
CEILING_ATTEMPTS = 4
FRAGMENTS = ["part0 ", "part1 ", "part2 ", "part3 "]
COMPLETION = "and the fallback finished it."
ASK = "write something long"
CEILING_ERROR = "Response remained truncated after 4 continuation attempts"


def _make_agent(fallback_chain, session_db=None):
    with (
        patch("model_tools.get_tool_definitions", return_value=[]),
        patch("model_tools.check_toolset_requirements", return_value={}),
        patch("agent.process_bootstrap.OpenAI", return_value=MagicMock()),
    ):
        agent = AIAgent(
            api_key="dummy-primary-key-abcdef12",
            base_url="https://openrouter.ai/api/v1",
            provider="openrouter",
            model=PRIMARY_MODEL,
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            fallback_model=fallback_chain,
            session_db=session_db,
        )
        agent.client = MagicMock()
        return agent


def _response(text, finish_reason):
    message = SimpleNamespace(
        content=text, tool_calls=None, reasoning_content=None,
        role="assistant", refusal=None, annotations=None, audio=None, function_call=None,
    )
    return SimpleNamespace(
        id="resp", model="mock", usage=None,
        choices=[SimpleNamespace(index=0, message=message, finish_reason=finish_reason)],
    )


def _run_turn(agent, *, fallback_completes=True, resolve_for_real=True):
    """One real turn: the ceiling on the primary, then the fallback's reply.

    Persistence is NOT patched — it writes to the temp ``HERMES_HOME`` that
    ``tests/conftest.py`` redirects — and with ``resolve_for_real`` the fallback is
    resolved through the real provider-resolution chain rather than a stubbed client.
    """
    scripted = [_response(f, FINISH_REASON_LENGTH) for f in FRAGMENTS]
    if fallback_completes:
        scripted.append(_response(COMPLETION, "stop"))
    seen_models, sent_contexts = [], []

    def fake_api_call(api_kwargs):
        seen_models.append(agent.model)
        sent_contexts.append([
            (m.get("role"), m.get("content"))
            for m in api_kwargs.get("messages", []) if isinstance(m, dict)
        ])
        return scripted[min(len(seen_models), len(scripted)) - 1]

    # Spy, not stub: the real `try_activate_fallback` still runs (and still owns route
    # selection); we only record the reason it was given.
    agent._observed_failover_reasons = []
    _real_activate = agent._try_activate_fallback

    def _spy_activate(reason=None):
        agent._observed_failover_reasons.append(reason)
        return _real_activate(reason)

    stack = [
        patch.object(agent, "_try_activate_fallback", side_effect=_spy_activate),
        patch.object(agent, "_interruptible_api_call", side_effect=fake_api_call),
        patch.object(agent, "_save_trajectory"),
        patch.object(agent, "_cleanup_task_resources"),
        patch("agent.model_metadata.get_model_context_length", return_value=200000),
    ]
    if not resolve_for_real:
        stack.append(patch("agent.auxiliary_client.resolve_provider_client",
                           return_value=(None, None)))
    with patch("agent.process_bootstrap.OpenAI", return_value=MagicMock()):
        for ctx in stack:
            ctx.__enter__()
        try:
            result = agent.run_conversation(ASK)
        finally:
            for ctx in reversed(stack):
                ctx.__exit__(None, None, None)
    return result, seen_models, sent_contexts


def _roles(messages):
    return [m.get("role") for m in messages if isinstance(m, dict) and m.get("role")]


def _wire_pairs(messages):
    """(role, content) for every row — the bytes a provider actually sees."""
    return [(m.get("role"), m.get("content")) for m in messages
            if isinstance(m, dict) and m.get("role")]


def _is_subsequence(needle, haystack):
    """True when every element of ``needle`` occurs in ``haystack``, in order."""
    it = iter(haystack)
    return all(item in it for item in needle)


def _assert_ordered_once(haystack, needles, what):
    positions = []
    for needle in needles:
        assert haystack.count(needle) == 1, (
            f"{needle!r} appears {haystack.count(needle)}x in {what}; expected exactly once"
        )
        positions.append(haystack.find(needle))
    assert positions == sorted(positions), f"{what} has the prefix out of order: {positions}"


class TestGovernedFailoverPreservesPaidOutput:
    def test_prefix_survives_into_fallback_context_answer_and_reloaded_session(self, tmp_path):
        """The paid prefix reaches the next provider, the caller, and the session DB —
        exactly once and in order in each — and history is never rewritten to do it.

        The append-only assertion is the load-bearing one: rewriting already-transmitted
        rows to tidy the transcript breaks prompt-cache byte stability (``agent/AGENTS.md``:
        "Never alter past context ... the ONLY context mutation is compression").
        """
        from hermes_state import SessionDB

        db = SessionDB(db_path=tmp_path / "session.db")
        agent = _make_agent([FALLBACK], session_db=db)
        result, seen_models, sent_contexts = _run_turn(agent)

        assert result.get("error") != CEILING_ERROR
        assert agent._fallback_activated is True, "the real resolution chain must activate"
        assert agent.model == FALLBACK_MODEL
        assert seen_models == [PRIMARY_MODEL] * CEILING_ATTEMPTS + [FALLBACK_MODEL]

        # 1. The fallback's OWN request carries the prefix, once, in order, and asks it to
        #    continue rather than leaving it to prefill an assistant row.
        fallback_ctx = sent_contexts[-1]
        _assert_ordered_once(
            "".join(str(c or "") for r, c in fallback_ctx if r == "assistant"),
            [f.strip() for f in FRAGMENTS], "the fallback's context",
        )
        assert fallback_ctx[-1][0] == "user"
        sent_roles = [r for r, _ in fallback_ctx]
        assert not [(a, b) for a, b in zip(sent_roles, sent_roles[1:])
                    if a == b and a != "tool"], f"same-role rows sent in a row: {sent_roles}"

        # 2. Every already-transmitted request is a byte-for-byte PREFIX of the next one.
        for older, newer in zip(sent_contexts, sent_contexts[1:]):
            assert newer[:len(older)] == older, (
                "an already-transmitted row changed between calls — prompt-cache "
                "byte stability is broken"
            )

        # 3. The returned answer stitches prefix + completion, once each, in order.
        _assert_ordered_once(
            result["final_response"], [f.strip() for f in FRAGMENTS] + [COMPLETION],
            "the returned answer",
        )

        # 4. Reload from the session DB that was really written to disk.
        reloaded = db.get_messages(agent.session_id)
        assert reloaded, "the turn must have persisted rows to the session DB"
        reloaded_assistant = "".join(
            str(m.get("content") or "") for m in reloaded
            if (m.get("role") if isinstance(m, dict) else None) == "assistant"
        )
        _assert_ordered_once(
            reloaded_assistant, [f.strip() for f in FRAGMENTS] + [COMPLETION],
            "the reloaded session transcript",
        )
        # Persistence must not have invented adjacency either.
        rl_roles = _roles(reloaded)
        assert not [(a, b) for a, b in zip(rl_roles, rl_roles[1:])
                    if a == b == "assistant"], f"adjacent assistant rows persisted: {rl_roles}"
        # 5. What was stored relates to what the caller got: every persisted row appears
        #    in the live transcript, with the same content, in the same relative order.
        #    (Persistence drops ephemeral scaffolding, so this is a subsequence, not
        #    equality — but a dropped, reordered or rewritten row still fails it.)
        live_pairs = _wire_pairs(result["messages"])
        reloaded_pairs = _wire_pairs(reloaded)
        assert reloaded_pairs, "no durable rows to compare"
        assert _is_subsequence(reloaded_pairs, live_pairs), (
            "persisted rows are not an ordered subsequence of the live transcript: "
            f"persisted={reloaded_pairs} live={live_pairs}"
        )
        # The comparison above is only meaningful if it can fail: perturb one stored row.
        tampered = [(r, (c or "") + "!") if i == len(reloaded_pairs) - 1 else (r, c)
                    for i, (r, c) in enumerate(reloaded_pairs)]
        assert not _is_subsequence(tampered, live_pairs), (
            "the live<->reloaded comparison cannot detect a changed row"
        )

        # 6. Failover on an output ceiling must NOT arm the primary's rate-limit cooldown:
        #    the primary was not throttled, it ran out of output budget.
        from agent.chat_completion_helpers import _RATE_LIMIT_FAILOVER_REASONS
        from agent.error_classifier import FailoverReason

        assert FailoverReason.output_ceiling not in _RATE_LIMIT_FAILOVER_REASONS, (
            "an output ceiling is not a rate limit; classing it as one arms the "
            "primary's exponential backoff and gates its recovery next turn"
        )
        assert agent._observed_failover_reasons, "no failover decision was recorded"
        assert agent._observed_failover_reasons[0] is FailoverReason.output_ceiling, (
            "the failover must name why it happened; got "
            f"{agent._observed_failover_reasons[0]!r}. The reason drives cooldown "
            "arming and chain-exhaustion handling, so it is not decoration."
        )
        assert getattr(agent, "_rate_limit_backoff_count", 0) == 0, (
            "the primary's exponential cooldown was armed by an output-ceiling failover"
        )
        assert not getattr(agent, "_rate_limited_until", 0), (
            "the primary was put in rate-limit cooldown by an output-ceiling failover"
        )


class TestGovernedFailoverRespectsAuthorityAndAccounting:
    def test_refused_activation_degrades_and_billed_attempts_are_not_refunded(self):
        """``try_activate_fallback`` is the sole authority, and valid output is not rebated.

        A refused activation switched no provider, so re-issuing would replay the ceiling
        against the same backend — the turn must end with the paid text instead. And the
        ceiling attempts that produced that text were billed, so unlike
        ``restart_with_rebuilt_messages`` (``api_call_count -= 1``; budget refund) this
        path must leave the accounting alone.
        """
        # -- accounting: the failover run must cost exactly ONE call more than the
        #    identical run that gives up at the ceiling. A refund would erase that.
        failing_over = _make_agent([FALLBACK])
        fo_budget = failing_over.iteration_budget.remaining
        fo_result, fo_calls, _ = _run_turn(failing_over)

        gives_up = _make_agent([])          # no chain: same 4 ceiling attempts, no failover
        gu_budget = gives_up.iteration_budget.remaining
        gu_result, gu_calls, _ = _run_turn(gives_up)

        assert len(fo_calls) - len(gu_calls) == 1, "the failover makes exactly one more call"
        # No refund. The failover spends TWO loop iterations for that one extra call
        # (one reaches preflight without calling, then the call itself) and neither is
        # rebated, so the failover run counts exactly 2 more than the give-up run.
        # Reinstating `restart_with_rebuilt_messages` — or calling
        # `iteration_budget.refund()` — rebates one and makes this 1.
        assert fo_result["api_calls"] >= len(fo_calls), (
            "api_calls fell below the number of provider calls actually made — refunded"
        )
        assert fo_result["api_calls"] - gu_result["api_calls"] == 2, (
            "the extra billed call was refunded out of api_calls"
        )
        assert ((fo_budget - failing_over.iteration_budget.remaining)
                - (gu_budget - gives_up.iteration_budget.remaining)) == 2, (
            "the extra billed call was refunded out of the iteration budget"
        )

        # -- refused activation: armed chain, unresolvable provider --
        refused = _make_agent([FALLBACK])
        r2, seen2, _c2 = _run_turn(refused, resolve_for_real=False)

        assert seen2 == [PRIMARY_MODEL] * CEILING_ATTEMPTS, "restarted after a refusal"
        assert refused._fallback_activated is not True
        assert r2.get("error") == CEILING_ERROR
        assert r2.get("partial") is True
        for fragment in FRAGMENTS:
            assert fragment.strip() in r2["final_response"], "the partial must survive"
