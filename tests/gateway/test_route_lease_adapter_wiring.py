"""Tests for the opt-in RouteLeaseManager wiring in gateway/run.py.

Proves:
  1. Flag OFF (default): _maybe_apply_route_lease() and _release_route_lease()
     are no-ops — runtime_kwargs pass through unchanged, no manager is built.
  2. Flag ON: _maybe_apply_route_lease() actually calls
     RouteLeaseManager.allocate_lease() and layers its decision onto the
     returned runtime kwargs.
"""

from __future__ import annotations

import asyncio

import gateway.run as run_module
from agent.route_lease_manager import AllocationResult, RouteLease


def _fresh_route_lease_state(monkeypatch):
    """Reset the module-level singleton and env var between tests."""
    monkeypatch.setattr(run_module, "_route_lease_manager_singleton", None)
    monkeypatch.delenv(run_module._ROUTE_LEASE_ENABLED_ENV, raising=False)


def test_flag_off_is_a_pure_noop(monkeypatch):
    """With the flag unset (default), _maybe_apply_route_lease must return
    runtime_kwargs completely unchanged, and must never construct a
    RouteLeaseManager (proving _resolve_runtime_agent_kwargs's existing
    behavior is untouched on the default path)."""
    _fresh_route_lease_state(monkeypatch)

    built = {"called": False}

    def _boom():
        built["called"] = True
        raise AssertionError("RouteLeaseManager must not be constructed when the flag is off")

    monkeypatch.setattr(run_module, "_get_route_lease_manager", _boom)

    original_kwargs = {
        "api_key": "sk-original",
        "base_url": "https://original.example/v1",
        "provider": "original-provider",
        "max_tokens": 8192,
    }
    result = run_module._maybe_apply_route_lease("session-abc", dict(original_kwargs))

    assert result == original_kwargs
    assert built["called"] is False

    # Release side must also no-op without raising or touching state.
    run_module._release_route_lease("session-abc")
    assert built["called"] is False


def test_flag_off_via_explicit_false_value(monkeypatch):
    """Explicitly set to something other than a truthy value — still off."""
    _fresh_route_lease_state(monkeypatch)
    monkeypatch.setenv(run_module._ROUTE_LEASE_ENABLED_ENV, "0")

    original_kwargs = {"provider": "unchanged", "model_untouched": True}
    result = run_module._maybe_apply_route_lease("session-xyz", dict(original_kwargs))
    assert result == original_kwargs


def test_flag_on_calls_allocate_lease_and_honors_decision(monkeypatch):
    """With the flag on, the real allocate_lease() call path must run and
    its resulting lease's provider/model must be layered onto the runtime
    kwargs handed back to the caller."""
    _fresh_route_lease_state(monkeypatch)
    monkeypatch.setenv(run_module._ROUTE_LEASE_ENABLED_ENV, "1")

    calls: list[str] = []

    class _FakeLease:
        provider = "fake-governed-provider"
        model_id = "fake-governed-model"
        route_id = "fake-route-007"

    class _FakeManager:
        async def allocate_lease(self, session_id):
            calls.append(session_id)
            return AllocationResult(
                success=True,
                lease=_FakeLease(),
                route_id="fake-route-007",
                provider="fake-governed-provider",
                model_id="fake-governed-model",
                reason="allocated",
            )

        def release_lease(self, session_id, reason):
            calls.append(f"release:{session_id}:{reason}")
            return True

    fake_manager = _FakeManager()
    monkeypatch.setattr(run_module, "_get_route_lease_manager", lambda: fake_manager)

    original_kwargs = {
        "provider": "config-default-provider",
        "base_url": "https://default.example/v1",
        "max_tokens": 4096,
    }
    result = run_module._maybe_apply_route_lease("session-real-001", dict(original_kwargs))

    # allocate_lease was actually invoked, with the real session key threaded
    # through (not a fabricated identifier).
    assert calls == ["session-real-001"]

    # And its decision was honored: provider/model overwritten, route id
    # surfaced for observability.
    assert result["provider"] == "fake-governed-provider"
    assert result["model"] == "fake-governed-model"
    assert result["route_lease_route_id"] == "fake-route-007"
    # Fields the lease didn't touch are preserved.
    assert result["base_url"] == "https://default.example/v1"
    assert result["max_tokens"] == 4096

    # Teardown: release_lease must be called with the same session key.
    run_module._route_lease_manager_singleton = fake_manager
    run_module._release_route_lease("session-real-001")
    assert "release:session-real-001:LeaseReleaseReason.SESSION_CLOSE" in calls or any(
        c.startswith("release:session-real-001:") for c in calls
    )


def test_flag_on_but_allocation_declined_leaves_kwargs_unchanged(monkeypatch):
    """A real-world case: the governed router has no eligible provider and
    RouteLeaseManager's own local-Qwen fallback is also unavailable in the
    fake, so allocation fails. Runtime kwargs must fall back to the
    pre-existing (unmodified) values rather than being corrupted."""
    _fresh_route_lease_state(monkeypatch)
    monkeypatch.setenv(run_module._ROUTE_LEASE_ENABLED_ENV, "1")

    class _FakeManagerAllFail:
        async def allocate_lease(self, session_id):
            return AllocationResult(success=False, error="no eligible routes", reason="no_eligible_routes")

    monkeypatch.setattr(run_module, "_get_route_lease_manager", lambda: _FakeManagerAllFail())

    original_kwargs = {"provider": "config-default-provider", "base_url": "https://default.example/v1"}
    result = run_module._maybe_apply_route_lease("session-fail-1", dict(original_kwargs))
    assert result == original_kwargs
