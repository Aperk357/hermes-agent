"""Integration test: agent_init.py's _fallback_chain construction actually
consults agent/route_capacity_advisor.py, and a failing advisor never breaks
agent construction. Exercises the real init_agent() code path (same mocking
pattern as test_init_fallback_on_exhausted_pool.py), not a standalone unit
test of the advisor module alone -- this is INTEGRATION_PROOF that the wiring
in agent_init.py actually calls the advisor, not just that the advisor works
in isolation.
"""
import pytest
from unittest.mock import patch, MagicMock

from run_agent import AIAgent
from agent.route_capacity_advisor import get_route_capacity_advisor, reset_route_capacity_advisor


def _make_tool_defs():
    return [{"type": "function", "function": {"name": "web_search",
             "description": "search", "parameters": {"type": "object", "properties": {}}}}]


def _mock_client(api_key="primary-key-1234567890", base_url="https://primary.example.com/v1"):
    c = MagicMock()
    c.api_key = api_key
    c.base_url = base_url
    c._default_headers = None
    return c


FALLBACK_CHAIN = [
    {"provider": "nvidia", "model": "nemotron"},
    {"provider": "alibaba-coding-plan", "model": "qwen3.6-plus"},
]


def _construct_agent():
    primary = _mock_client()
    with patch("agent.auxiliary_client.resolve_provider_client", return_value=(primary, "primary-model")), \
         patch("run_agent.get_tool_definitions", return_value=_make_tool_defs()), \
         patch("run_agent.check_toolset_requirements", return_value={}), \
         patch("run_agent.OpenAI", return_value=MagicMock()):
        return AIAgent(
            provider="tencent-token-plan",
            model="primary-model",
            api_key=None,
            base_url=None,
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            fallback_model=[dict(entry) for entry in FALLBACK_CHAIN],
        )


def setup_function(_fn):
    reset_route_capacity_advisor()


def test_advisor_is_off_by_default_chain_never_touched():
    """The single most important safety property from the regression this
    slice caused: with HERMES_ROUTE_CAPACITY_ADVISOR_ENABLED unset, the
    advisor must never be consulted or registered against, no matter how
    loaded it is -- full-suite test isolation and unmodified existing
    production behavior both depend on this default."""
    advisor = get_route_capacity_advisor()
    advisor.record_assignment("existing-session-1", "nvidia", "nemotron")
    advisor.record_assignment("existing-session-2", "nvidia", "nemotron")

    with patch.dict("os.environ", {}, clear=False):
        import os as _os
        _os.environ.pop("HERMES_ROUTE_CAPACITY_ADVISOR_ENABLED", None)
        agent = _construct_agent()

    assert agent._fallback_chain == FALLBACK_CHAIN, "default-off must leave the chain untouched even under heavy advisor load"
    assert advisor.current_load("nvidia", "nemotron") == 2, "default-off must not register this session either"


def test_fallback_chain_reordered_when_head_is_concentrated_and_enabled():
    """Pre-load the advisor so the configured head (nvidia/nemotron) already
    has 2+ live sessions on it -- the new session's agent_init.py call should
    come out with the less-loaded entry promoted to the front, but ONLY when
    explicitly opted in."""
    advisor = get_route_capacity_advisor()
    advisor.record_assignment("existing-session-1", "nvidia", "nemotron")
    advisor.record_assignment("existing-session-2", "nvidia", "nemotron")

    with patch.dict("os.environ", {"HERMES_ROUTE_CAPACITY_ADVISOR_ENABLED": "1"}):
        agent = _construct_agent()

    assert agent._fallback_chain[0] == {"provider": "alibaba-coding-plan", "model": "qwen3.6-plus"}, (
        "a concentrated head with a less-loaded alternative available must be reordered by the advisor"
    )
    # Permutation only -- nothing invented or dropped.
    assert sorted(agent._fallback_chain, key=lambda e: e["provider"]) == sorted(FALLBACK_CHAIN, key=lambda e: e["provider"])


def test_fallback_chain_unchanged_when_no_concentration_and_enabled():
    """Enabled, but no prior assignments -- the advisor must leave config's own order alone."""
    with patch.dict("os.environ", {"HERMES_ROUTE_CAPACITY_ADVISOR_ENABLED": "1"}):
        agent = _construct_agent()
    assert agent._fallback_chain == FALLBACK_CHAIN


def test_agent_construction_succeeds_when_advisor_raises_and_enabled():
    """The single most important safety property: a broken/raising advisor
    must NEVER prevent agent construction, and the chain must fall back to
    exactly what config specified -- even when the feature is turned on."""
    with patch.dict("os.environ", {"HERMES_ROUTE_CAPACITY_ADVISOR_ENABLED": "1"}), \
         patch("agent.route_capacity_advisor.get_route_capacity_advisor", side_effect=RuntimeError("advisor exploded")):
        agent = _construct_agent()
    assert agent._fallback_chain == FALLBACK_CHAIN, "a raising advisor must degrade to the unmodified config-built chain, not break init"


def test_new_session_gets_registered_with_the_advisor_when_enabled():
    """After construction, the session's chosen head should be visible to the
    advisor for a SUBSEQUENT session's reorder decision -- this is the other
    half of the wiring (record_assignment, not just advise_order) -- only
    when explicitly opted in."""
    with patch.dict("os.environ", {"HERMES_ROUTE_CAPACITY_ADVISOR_ENABLED": "1"}):
        agent = _construct_agent()
    advisor = get_route_capacity_advisor()
    assert advisor.current_load("nvidia", "nemotron") == 1, "agent_init.py must register the constructed session's head assignment when enabled"
    assert agent.session_id in advisor._assignments
