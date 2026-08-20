"""ADAPT layer: bridges RouteLeaseManager's CanonicalRouterInterface to the
real governed router in pdv-provider-routing (HermesProviderIntegration).

This file is new code (not part of the copied route_lease_manager.py). It
exists solely to translate between two interfaces that were designed
independently:

  - RouteLeaseManager (agent/route_lease_manager.py) expects a
    CanonicalRouterInterface that can hand back a *list* of healthy
    RouteCapability objects (with base_url, max_tokens, concurrent_limit,
    health, cooldown, rate_bucket, etc.) for a capability class.
  - The real governed router (pdv-provider-routing) exposes
    `_RequesterIntegration.request_provider(...)`, which returns exactly
    ONE `ProviderDecision` per call (task_id, requester_id, provider_id,
    reason_code, registry_id, registry_sha256, considered_provider_ids,
    model_label). It does NOT expose base_url / max_tokens /
    concurrent_limit / health / cooldown_until / rate_bucket — those live
    on the registry/health-store side of pdv-provider-routing, not on the
    decision object.

Design choice (documented per task instructions): `get_healthy_routes()`
below calls `request_provider()` once and wraps the single decision in a
one-element list. This is honest given the real interface: RouteLeaseManager
just sees "here is 1 candidate route for this capability class", which is
literally true of what request_provider returns. It is NOT a full registry
listing — pdv-provider-routing's ProviderService/ProviderRegistry were
inspected for a multi-candidate listing method callable without pulling in
health-store/credential plumbing, and none was found that fits this narrow
adapter surface; `considered_provider_ids` on ProviderDecision hints at
other candidates but does not carry their capability metadata, so it is not
used to synthesize extra RouteCapability entries (that would be fabricating
data this adapter doesn't have).

Fields RouteCapability requires that ProviderDecision does not expose
(base_url, max_tokens, is_paid, is_local, concurrent_limit, rate_bucket) are
filled with explicit placeholder values below, each commented. Do not read
these placeholders as real capacity/health data.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from agent.route_lease_manager import (
    CanonicalRouterInterface,
    HealthState,
    RouteCapability,
    RouteClassification,
)

logger = logging.getLogger(__name__)

# Default location of the pdv-provider-routing checkout on this machine.
# Overridable via HERMES_PDV_PROVIDER_ROUTING_PATH for other hosts/CI.
_DEFAULT_PDV_PROVIDER_ROUTING_PATH = Path(
    r"C:\Users\User\Desktop\PDV_APPS\pdv-provider-routing"
)


def _ensure_pdv_provider_routing_importable() -> None:
    """Add pdv-provider-routing to sys.path if its package isn't already importable.

    Only called when the route-lease adapter is actually being constructed
    (i.e. the opt-in flag is on) — never touches sys.path on the default,
    disabled path.
    """
    try:
        import pdv_developer_execution_os  # noqa: F401
        return
    except ImportError:
        pass

    import os

    root = os.environ.get("HERMES_PDV_PROVIDER_ROUTING_PATH")
    root_path = Path(root) if root else _DEFAULT_PDV_PROVIDER_ROUTING_PATH
    if root_path.exists() and str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))


@dataclass
class _AdapterConfig:
    runtime_profile: str = "windows_native"
    registry_path: Optional[Path] = None


class HermesGovernedRouterAdapter(CanonicalRouterInterface):
    """CanonicalRouterInterface implementation backed by the real,
    governed pdv-provider-routing HermesProviderIntegration.

    This class does NOT implement its own routing/health/capacity logic —
    it only translates. All real routing authority stays in
    pdv-provider-routing, per route_lease_manager.py's own stated
    contract ("Consumes canonical routing authority ... NO duplicate
    router is built").
    """

    def __init__(self, config: Optional[_AdapterConfig] = None):
        _ensure_pdv_provider_routing_importable()

        from pdv_developer_execution_os.provider_service import ProviderService
        from pdv_developer_execution_os.requester_integrations import (
            HermesProviderIntegration,
        )

        cfg = config or _AdapterConfig()
        self._service = ProviderService.build(
            runtime_profile=cfg.runtime_profile,
            registry_path=cfg.registry_path,
        )
        self._integration = HermesProviderIntegration(self._service)
        # last decision per route_id, so get_route_details/update_route_health
        # have something honest to report against instead of guessing.
        self._last_decisions: dict = {}

    # -- CanonicalRouterInterface -------------------------------------

    async def get_healthy_routes(self, capability_class: str = "general") -> List[RouteCapability]:
        """Call request_provider() once; wrap its single decision as a
        one-element list. See module docstring for why this is the honest
        shape given the real interface.
        """
        import uuid

        try:
            decision = self._integration.request_provider(
                task_id=f"hermes-route-lease-{uuid.uuid4().hex[:12]}",
                capabilities=frozenset({capability_class}),
                privacy_class="standard",
                workload="interactive",
                context_tokens=0,
                remaining_retry_budget=1,
                now=datetime.now(timezone.utc),
            )
        except Exception:
            logger.warning(
                "HermesGovernedRouterAdapter.get_healthy_routes failed for capability_class=%s",
                capability_class,
                exc_info=True,
            )
            return []

        if not decision.provider_id:
            # A decision with no provider_id means the governed router
            # declined to select one (reason_code carries why). No route
            # to offer RouteLeaseManager.
            logger.info(
                "Governed router returned no provider_id (reason_code=%s) for capability_class=%s",
                decision.reason_code, capability_class,
            )
            return []

        route = RouteCapability(
            route_id=decision.provider_id,
            model_id=decision.model_label or decision.provider_id,
            provider=decision.provider_id,
            # NOT exposed by ProviderDecision. base_url lives in the
            # registry/health-store side of pdv-provider-routing, which
            # this narrow adapter does not query. Empty string is an
            # explicit "unknown", not a real endpoint.
            base_url="",
            capability_class=capability_class,
            # NOT exposed by ProviderDecision — placeholder, not measured.
            max_tokens=0,
            # NOT exposed by ProviderDecision — unknown whether paid;
            # conservatively assume paid=True so nothing downstream treats
            # this as a confirmed-free route it wasn't told about.
            is_paid=True,
            is_local=False,
            # NOT exposed by ProviderDecision — placeholder. RouteLeaseManager
            # uses this for capacity-based selection; 1 avoids advertising
            # capacity this adapter has no evidence for.
            concurrent_limit=1,
            current_load=0,
            # A successful decision with a provider_id is, at minimum,
            # "the governed router considers this usable right now" — map
            # that to HEALTHY. Real health/cooldown data is not exposed by
            # ProviderDecision.
            health=HealthState.HEALTHY,
            cooldown_until=0.0,
            rate_bucket=decision.reason_code or "",
            classification=RouteClassification.HOSTED,
        )
        self._last_decisions[route.route_id] = decision
        return [route]

    async def get_route_details(self, route_id: str) -> Optional[RouteCapability]:
        # No registry lookup-by-id surface used here; only what this
        # adapter has already seen via get_healthy_routes is available.
        decision = self._last_decisions.get(route_id)
        if decision is None:
            return None
        return RouteCapability(
            route_id=route_id,
            model_id=decision.model_label or route_id,
            provider=route_id,
            base_url="",
            capability_class="general",
            max_tokens=0,
            is_paid=True,
            is_local=False,
            concurrent_limit=1,
            current_load=0,
            health=HealthState.HEALTHY,
            cooldown_until=0.0,
            rate_bucket=decision.reason_code or "",
            classification=RouteClassification.HOSTED,
        )

    async def update_route_health(self, route_id: str, health: HealthState) -> bool:
        # The real governed router owns health/circuit state internally
        # (ProviderHealthStore) and is not written to by this adapter —
        # doing so would be exactly the "duplicate router" route_lease_manager.py
        # says must not be built. This is a documented no-op, not silent
        # data loss: RouteLeaseManager's own in-memory route_capacity map
        # still reflects the update locally for its own selection logic.
        logger.debug(
            "update_route_health(%s, %s) is a local-only no-op; the governed "
            "router's own health store is authoritative and not writable "
            "from this adapter.",
            route_id, health,
        )
        return True

    async def check_rate_bucket(self, route_id: str) -> str:
        decision = self._last_decisions.get(route_id)
        return decision.reason_code if decision else ""

    async def get_concurrent_count(self, route_id: str) -> int:
        # Not exposed by ProviderDecision/this adapter's surface — RouteLeaseManager
        # tracks concurrency itself via _concurrent_per_route once a lease is
        # allocated; this method returning 0 means "this adapter has no
        # independent measurement", not "route is idle".
        return 0
