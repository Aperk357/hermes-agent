"""Route-lease adapter opt-in flag: flag-off is a byte-for-byte no-op,
flag-on actually invokes RouteLeaseManager.allocate_lease() and layers its
decision onto runtime kwargs.
"""
import asyncio

import pytest

from gateway import run as run_mod
from agent.route_lease_manager import (
    AllocationResult,
    RouteLease,
    reset_route_lease_manager,
)


@pytest.fixture(autouse=True)
def _reset_singleton(monkeypatch):
    # run_mod keeps its own module-level singleton separate from
    # agent.route_lease_manager's; reset both so tests don't leak state.
    monkeypatch.setattr(run_mod, "_route_lease_manager_singleton", None)
    reset_route_lease_manager()
    yield
    monkeypatch.setattr(run_mod, "_route_lease_manager_singleton", None)
    reset_route_lease_manager()


def test_flag_off_is_a_noop(monkeypatch):
    """HERMES_ROUTE_LEASE_ENABLED unset (default) -> runtime_kwargs unchanged,
    and the manager singleton is never constructed."""
    monkeypatch.delenv("HERMES_ROUTE_LEASE_ENABLED", raising=False)

    called = {"count": 0}
    monkeypatch.setattr(
        run_mod,
        "_get_route_lease_manager",
        lambda: called.__setitem__("count", called["count"] + 1),
    )

    original = {"provider": "config-provider", "api_key": "k", "base_url": "u"}
    result = run_mod._maybe_apply_route_lease("session-123", dict(original))

    assert result == original
    assert called["count"] == 0, "manager must not be constructed when flag is off"


def test_flag_off_explicitly_false(monkeypatch):
    monkeypatch.setenv("HERMES_ROUTE_LEASE_ENABLED", "false")
    original = {"provider": "config-provider"}
    result = run_mod._maybe_apply_route_lease("session-123", dict(original))
    assert result == original


def test_flag_on_no_session_key_is_noop(monkeypatch):
    """Even with the flag on, no session_key -> no-op (can't allocate a
    lease without a session identity)."""
    monkeypatch.setenv("HERMES_ROUTE_LEASE_ENABLED", "true")
    original = {"provider": "config-provider"}
    result = run_mod._maybe_apply_route_lease(None, dict(original))
    assert result == original


def test_flag_on_invokes_allocate_and_overlays_kwargs(monkeypatch):
    """Flag on + session_key -> RouteLeaseManager.allocate_lease() is called,
    and a successful lease overlays provider/model onto runtime_kwargs."""
    monkeypatch.setenv("HERMES_ROUTE_LEASE_ENABLED", "true")

    fake_lease = RouteLease(
        session_id="session-abc",
        route_id="test-route-1",
        provider="test-provider",
        model_id="test-model",
        capability_class="general",
        assigned_at=0,
        lease_expires_at=2**62,
    )
    fake_result = AllocationResult(
        success=True,
        lease=fake_lease,
        route_id="test-route-1",
        provider="test-provider",
        model_id="test-model",
        reason="allocated",
    )

    calls = {"allocate_lease": []}

    class _FakeManager:
        async def allocate_lease(self, session_id, **kwargs):
            calls["allocate_lease"].append(session_id)
            return fake_result

    monkeypatch.setattr(run_mod, "_get_route_lease_manager", lambda: _FakeManager())

    original = {"provider": "config-provider", "model": "config-model", "api_key": "k"}
    result = run_mod._maybe_apply_route_lease("session-abc", dict(original))

    assert calls["allocate_lease"] == ["session-abc"], (
        "RouteLeaseManager.allocate_lease() must be invoked when the flag is on"
    )
    assert result["provider"] == "test-provider"
    assert result["model"] == "test-model"
    assert result["route_lease_route_id"] == "test-route-1"
    # api_key untouched — adapter only overlays provider/model/route id.
    assert result["api_key"] == "k"
