"""PDV Per-Tab Session Route Lease Manager.

Manages session-level route leases for Hermes tabs/sessions.
Consumes canonical routing authority (pdv-provider-routing → smart proxy → provider registry)
and manages only: session route lease, model preference/pin, session continuity, lease refresh/release.

NO raw API keys are copied into tab/session state.
NO duplicate router is built.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────────────────────────

class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    COOLED = "cooled"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class PinMode(str, Enum):
    SMART = "smart"
    PREFERRED = "preferred"
    EXACT = "exact"


class RouteClassification(str, Enum):
    LOCAL = "local"
    HOSTED = "hosted"
    FREE = "free"


class LeaseReleaseReason(str, Enum):
    SESSION_CLOSE = "session_close"
    SESSION_RESET = "session_reset"
    ROTATION = "rotation"
    EXPIRED = "expired"
    MANUAL = "manual"
    HEALTH_FAILURE = "health_failure"


class AllocationPolicy(str, Enum):
    SMART = "smart"
    CAPABILITY_FIRST = "capability_first"
    CAPACITY_FIRST = "capacity_first"
    RATE_SPREAD = "rate_spread"


# ── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class RouteCapability:
    """Describes what a route can do."""
    route_id: str
    model_id: str
    provider: str
    base_url: str
    capability_class: str  # e.g. "general", "code", "reasoning", "vision", "audio"
    max_tokens: int
    is_paid: bool
    is_local: bool
    concurrent_limit: int
    current_load: int = 0
    health: HealthState = HealthState.UNKNOWN
    cooldown_until: float = 0.0
    rate_bucket: str = ""
    classification: RouteClassification = RouteClassification.HOSTED

    @property
    def is_cooled(self) -> bool:
        return self.health == HealthState.COOLED or (
            self.cooldown_until > 0 and time.time() < self.cooldown_until
        )

    @property
    def available_capacity(self) -> int:
        return max(0, self.concurrent_limit - self.current_load)

    @property
    def is_eligible(self) -> bool:
        return (
            self.health in (HealthState.HEALTHY, HealthState.DEGRADED)
            and not self.is_cooled
            and self.available_capacity > 0
        )


@dataclass
class RouteLease:
    """Per-session route lease contract.
    
    Fields:
        session_id: Unique session identifier
        route_id: Route identifier from canonical router
        provider: Provider name
        model_id: Model identifier
        capability_class: Task capability requirement
        assigned_at: UTC epoch-millisecond timestamp
        lease_expires_at: Lease expiry timestamp
        heartbeat_interval: Seconds between heartbeat checks
        health_state: Current health state
        cooldown_state: Current cooldown state
        pin_mode: SMART / PREFERRED / EXACT
        classification: LOCAL / HOSTED / FREE
        credential_reference_id: Reference only, NO raw key
        checkpoint_id: Session checkpoint correlation
        task_correlation: Active task correlation
        release_reason: Why lease was released
        base_url: API endpoint
        max_tokens: Context window size
        concurrent_limit: Route concurrency limit
        rate_bucket: Rate bucket identifier
    """
    session_id: str
    route_id: str
    provider: str
    model_id: str
    capability_class: str
    assigned_at: int  # epoch-ms
    lease_expires_at: int  # epoch-ms
    heartbeat_interval: int = 30
    health_state: str = HealthState.HEALTHY.value
    cooldown_state: str = "none"
    pin_mode: str = PinMode.SMART.value
    classification: str = RouteClassification.HOSTED.value
    credential_reference_id: str = ""
    checkpoint_id: str = ""
    task_correlation: str = ""
    release_reason: str = ""
    base_url: str = ""
    max_tokens: int = 0
    concurrent_limit: int = 0
    rate_bucket: str = ""
    _release_reason_set: bool = False

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "route_id": self.route_id,
            "provider": self.provider,
            "model_id": self.model_id,
            "capability_class": self.capability_class,
            "assigned_at": self.assigned_at,
            "lease_expires_at": self.lease_expires_at,
            "heartbeat_interval": self.heartbeat_interval,
            "health_state": self.health_state,
            "cooldown_state": self.cooldown_state,
            "pin_mode": self.pin_mode,
            "classification": self.classification,
            "credential_reference_id": self.credential_reference_id,
            "checkpoint_id": self.checkpoint_id,
            "task_correlation": self.task_correlation,
            "release_reason": self.release_reason,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "concurrent_limit": self.concurrent_limit,
            "rate_bucket": self.rate_bucket,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RouteLease":
        return cls(
            session_id=data["session_id"],
            route_id=data["route_id"],
            provider=data["provider"],
            model_id=data["model_id"],
            capability_class=data["capability_class"],
            assigned_at=data["assigned_at"],
            lease_expires_at=data["lease_expires_at"],
            heartbeat_interval=data.get("heartbeat_interval", 30),
            health_state=data.get("health_state", HealthState.HEALTHY.value),
            cooldown_state=data.get("cooldown_state", "none"),
            pin_mode=data.get("pin_mode", PinMode.SMART.value),
            classification=data.get("classification", RouteClassification.HOSTED.value),
            credential_reference_id=data.get("credential_reference_id", ""),
            checkpoint_id=data.get("checkpoint_id", ""),
            task_correlation=data.get("task_correlation", ""),
            release_reason=data.get("release_reason", ""),
            base_url=data.get("base_url", ""),
            max_tokens=data.get("max_tokens", 0),
            concurrent_limit=data.get("concurrent_limit", 0),
            rate_bucket=data.get("rate_bucket", ""),
        )

    def is_expired(self) -> bool:
        return time.time() * 1000 > self.lease_expires_at

    def is_healthy(self) -> bool:
        return self.health_state in (HealthState.HEALTHY.value, HealthState.DEGRADED.value)

    def is_cooled(self) -> bool:
        if self.cooldown_state == "none":
            return False
        return True  # cooldown_state tracks the cooldown state


@dataclass
class AllocationResult:
    """Result of an allocation attempt."""
    success: bool
    lease: Optional[RouteLease] = None
    error: str = ""
    route_id: str = ""
    provider: str = ""
    model_id: str = ""
    reason: str = ""


# ── Canonical Router Interface ─────────────────────────────────────────────

class CanonicalRouterInterface:
    """Interface for querying the canonical pdv-provider-routing authority.
    
    Hermes consumes this authority — it does NOT duplicate it.
    In production, this would call pdv-provider-routing.
    For verification/testing, a mock implementation is used.
    """

    async def get_healthy_routes(self, capability_class: str = "general") -> List[RouteCapability]:
        """Return healthy, compatible routes from canonical provider registry."""
        raise NotImplementedError

    async def get_route_details(self, route_id: str) -> Optional[RouteCapability]:
        """Get detailed info for a specific route."""
        raise NotImplementedError

    async def update_route_health(self, route_id: str, health: HealthState) -> bool:
        """Update route health in canonical registry."""
        raise NotImplementedError

    async def check_rate_bucket(self, route_id: str) -> str:
        """Check which rate bucket a route belongs to."""
        raise NotImplementedError

    async def get_concurrent_count(self, route_id: str) -> int:
        """Get current concurrent session count for a route."""
        raise NotImplementedError


# ── Route Lease Manager ────────────────────────────────────────────────────

class RouteLeaseManager:
    """Manages per-session route leases for Hermes tabs/sessions.
    
    Responsibilities:
    - Allocate leases via canonical router
    - Monitor lease health/cooldown
    - Handle lease refresh/rotation
    - Release leases on session close
    - Enforce per-route concurrency
    - Track allocation policy
    
    Does NOT:
    - Duplicate the canonical router
    - Handle raw API keys
    - Make routing decisions outside the lease layer
    """

    # Local Qwen 3.6 fallback
    LOCAL_QWEN_MODEL = "qwen3.6:ctx65k"
    LOCAL_QWEN_BASE_URL = "127.0.0.1:11435/v1"
    LOCAL_QWEN_PROVIDER = "local"

    def __init__(
        self,
        router: Optional[CanonicalRouterInterface] = None,
        lease_store_path: Optional[str] = None,
        lease_ttl_seconds: int = 3600,
        heartbeat_interval: int = 30,
        cooldown_duration_seconds: int = 300,
        max_retries_on_failure: int = 1,
    ):
        self._router = router or MockRouter()
        self._lease_store_path = lease_store_path
        self._lease_ttl_seconds = lease_ttl_seconds
        self._heartbeat_interval = heartbeat_interval
        self._cooldown_duration_seconds = cooldown_duration_seconds
        self._max_retries = max_retries_on_failure

        # Active leases: session_id -> RouteLease
        self._leases: Dict[str, RouteLease] = {}

        # Route capacity tracking
        self._route_capacity: Dict[str, RouteCapability] = {}

        # Rate bucket spread tracking
        self._rate_bucket_counts: Dict[str, int] = {}

        # Cooldown tracking
        self._cooldowns: Dict[str, float] = {}

        # Concurrent sessions per route
        self._concurrent_per_route: Dict[str, int] = {}

        # Allocation policy
        self._allocation_policy = AllocationPolicy.SMART

        # Load persisted leases
        self._load_leases()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _get_local_qwen_route(self) -> Optional[RouteCapability]:
        """Get local Qwen 3.6 fallback route."""
        return RouteCapability(
            route_id="qwen-local-001",
            model_id=self.LOCAL_QWEN_MODEL,
            provider=self.LOCAL_QWEN_PROVIDER,
            base_url=self.LOCAL_QWEN_BASE_URL,
            capability_class="general",
            max_tokens=65536,
            is_paid=False,
            is_local=True,
            concurrent_limit=20,
            current_load=0,
            health=HealthState.HEALTHY,
            cooldown_until=0,
            rate_bucket="local",
            classification=RouteClassification.LOCAL,
        )

    # ── Allocation ───────────────────────────────────────────────────────

    async def allocate_lease(
        self,
        session_id: str,
        capability_class: str = "general",
        pin_mode: PinMode = PinMode.SMART,
        preferred_model: Optional[str] = None,
        checkpoint_id: str = "",
        exclude_route_ids: Optional[set] = None,
    ) -> AllocationResult:
        """Allocate a route lease for a new session.
        
        Allocation policy (SMART):
        1. Determine task/model capability requirement
        2. Choose healthy enabled compatible route
        3. Prefer route with available capacity
        4. Avoid concentrating new tabs on the same rate bucket
        5. Persist lease
        6. Route session through canonical smart router
        """
        # Check for existing lease
        if session_id in self._leases:
            existing = self._leases[session_id]
            if not existing.is_expired():
                return AllocationResult(
                    success=True,
                    lease=existing,
                    route_id=existing.route_id,
                    provider=existing.provider,
                    model_id=existing.model_id,
                    reason="existing_lease",
                )

        # Get healthy routes from canonical router
        healthy_routes = await self._router.get_healthy_routes(capability_class)

        # Filter eligible routes
        eligible = [r for r in healthy_routes if r.is_eligible]

        # Exclude specified routes (e.g., failed routes during rotation)
        if exclude_route_ids:
            eligible = [r for r in eligible if r.route_id not in exclude_route_ids]

        if not eligible:
            # Try local Qwen 3.6 as fallback
            local_route = self._get_local_qwen_route()
            if local_route:
                lease = self._create_lease(
                    session_id=session_id,
                    route=local_route,
                    pin_mode=pin_mode,
                    preferred_model=preferred_model,
                    checkpoint_id=checkpoint_id,
                )
                self._leases[session_id] = lease
                self._persist_lease(lease)
                return AllocationResult(
                    success=True,
                    lease=lease,
                    route_id=lease.route_id,
                    provider=lease.provider,
                    model_id=lease.model_id,
                    reason="local_fallback",
                )
            return AllocationResult(
                success=False,
                error="No healthy routes available",
                reason="no_eligible_routes",
            )

        # Apply allocation policy
        selected = self._select_route(
            eligible, capability_class, pin_mode, preferred_model
        )

        if not selected:
            return AllocationResult(
                success=False,
                error="No compatible route found",
                reason="no_compatible_route",
            )

        lease = self._create_lease(
            session_id=session_id,
            route=selected,
            pin_mode=pin_mode,
            preferred_model=preferred_model,
            checkpoint_id=checkpoint_id,
        )
        self._leases[session_id] = lease
        self._persist_lease(lease)
        self._update_route_capacity(selected, increment=True)

        logger.info(
            "Allocated lease for session %s: %s/%s (route: %s)",
            session_id, selected.provider, selected.model_id, selected.route_id,
        )
        return AllocationResult(
            success=True,
            lease=lease,
            route_id=lease.route_id,
            provider=lease.provider,
            model_id=lease.model_id,
            reason="allocated",
        )

    # ── Rotation ─────────────────────────────────────────────────────────

    async def rotate_lease(
        self,
        session_id: str,
        reason: str,
        checkpoint_id: str = "",
    ) -> AllocationResult:
        """Rotate lease due to 429/cooldown/failure.
        
        On 429/cooldown:
        - Update shared route health
        - Preserve session checkpoint
        - Acquire compatible replacement lease
        - Continue same turn/task where safe
        - Prevent duplicate tool/side-effect execution
        - Release old lease
        """
        if session_id not in self._leases:
            return AllocationResult(
                success=False,
                error=f"No active lease for session {session_id}",
                reason="no_lease",
            )

        old_lease = self._leases[session_id]
        old_checkpoint = old_lease.checkpoint_id or checkpoint_id

        # Preserve checkpoint
        if checkpoint_id:
            old_lease.checkpoint_id = checkpoint_id

        # Update route health if failure-related
        if reason in ("429", "cooldown", "temporary_failure"):
            await self._update_route_health_on_failure(old_lease.route_id)

        # Temporarily exclude the failed route from selection
        failed_route_id = old_lease.route_id

        # Release old lease
        self.release_lease(session_id, LeaseReleaseReason.ROTATION)

        # Acquire new lease, excluding the failed route
        return await self.allocate_lease(
            session_id=session_id,
            capability_class=old_lease.capability_class,
            pin_mode=PinMode(old_lease.pin_mode),
            checkpoint_id=old_checkpoint,
            exclude_route_ids={failed_route_id},
        )

    # ── Health Monitoring ────────────────────────────────────────────────

    async def check_lease_health(self, session_id: str) -> HealthState:
        """Check health of a session's lease."""
        if session_id not in self._leases:
            return HealthState.UNKNOWN

        lease = self._leases[session_id]

        # Check expiry
        if lease.is_expired():
            await self._handle_expired_lease(session_id)
            return HealthState.UNHEALTHY

        # Check cooldown
        if lease.cooldown_state != "none":
            return HealthState.COOLED

        # Check route health via canonical router
        route = self._route_capacity.get(lease.route_id)
        if route:
            if route.is_cooled:
                return HealthState.COOLED
            if route.health == HealthState.UNHEALTHY:
                return HealthState.UNHEALTHY

        return HealthState(lease.health_state)

    async def update_lease_health(self, session_id: str, health: HealthState) -> bool:
        """Update lease health state."""
        if session_id not in self._leases:
            return False

        lease = self._leases[session_id]
        lease.health_state = health.value
        self._persist_lease(lease)

        # Update canonical router
        await self._router.update_route_health(lease.route_id, health)
        return True

    # ── Release ──────────────────────────────────────────────────────────

    def release_lease(self, session_id: str, reason: LeaseReleaseReason) -> bool:
        """Release a session's route lease."""
        if session_id not in self._leases:
            return False

        lease = self._leases[session_id]
        lease.release_reason = reason.value
        lease.cooldown_state = "none"

        # Decrement route capacity
        route = self._route_capacity.get(lease.route_id)
        rid = lease.route_id
        if route:
            route.current_load = max(0, route.current_load - 1)
        self._concurrent_per_route[rid] = max(0, self._concurrent_per_route.get(rid, 0) - 1)
        self._update_rate_bucket_count(lease.rate_bucket, increment=False)

        # Remove lease
        del self._leases[session_id]
        self._persist_all_leases()

        logger.info("Released lease for session %s: %s", session_id, reason.value)
        return True

    # ── Mode Switch ──────────────────────────────────────────────────────

    async def switch_pin_mode(
        self,
        session_id: str,
        new_mode: PinMode,
        new_model: Optional[str] = None,
    ) -> AllocationResult:
        """Switch pin mode for a session, replacing the lease."""
        if session_id not in self._leases:
            return AllocationResult(
                success=False,
                error=f"No active lease for session {session_id}",
                reason="no_lease",
            )

        old_lease = self._leases[session_id]
        old_lease.release_reason = LeaseReleaseReason.MANUAL.value
        self.release_lease(session_id, LeaseReleaseReason.MANUAL)

        # Allocate new lease with new mode
        if new_mode == PinMode.EXACT and new_model:
            # Exact pin: find exact model match
            result = await self.allocate_lease(
                session_id=session_id,
                capability_class=old_lease.capability_class,
                pin_mode=PinMode.EXACT,
                preferred_model=new_model,
            )
        else:
            # SMART/PREFERRED: use allocation policy
            result = await self.allocate_lease(
                session_id=session_id,
                capability_class=old_lease.capability_class,
                pin_mode=new_mode,
                preferred_model=new_model,
            )

        if result.success and result.lease:
            result.lease.pin_mode = new_mode.value

        return result

    # ── Distribution ─────────────────────────────────────────────────────

    def get_active_lease_count(self) -> int:
        """Get count of active leases."""
        return len(self._leases)

    def get_lease_distribution(self) -> Dict[str, List[str]]:
        """Get distribution of sessions across routes."""
        distribution: Dict[str, List[str]] = {}
        for session_id, lease in self._leases.items():
            route_key = f"{lease.provider}/{lease.model_id}"
            if route_key not in distribution:
                distribution[route_key] = []
            distribution[route_key].append(session_id)
        return distribution

    def get_session_lease(self, session_id: str) -> Optional[RouteLease]:
        """Get lease for a session."""
        lease = self._leases.get(session_id)
        if lease and lease.is_expired():
            return None
        return lease

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs with active leases."""
        return [sid for sid, l in self._leases.items() if not l.is_expired()]

    # ── Internal Helpers ─────────────────────────────────────────────────

    def _select_route(
        self,
        eligible: List[RouteCapability],
        capability_class: str,
        pin_mode: PinMode,
        preferred_model: Optional[str],
    ) -> Optional[RouteCapability]:
        """Select route based on allocation policy."""
        if pin_mode == PinMode.EXACT and preferred_model:
            # Exact pin: find exact model match
            for route in eligible:
                if route.model_id == preferred_model:
                    return route
            return None

        if pin_mode == PinMode.PREFERRED and preferred_model:
            # Preferred: try preferred first, then fall back
            for route in eligible:
                if route.model_id == preferred_model:
                    return route
            # Fall through to SMART selection

        # SMART mode: use allocation policy
        # Rate spread is the default to avoid concentrating tabs on same bucket
        best = self._select_by_rate_spread(eligible)
        if best:
            return best

        # Default: prefer capacity
        return self._select_by_capacity(eligible)

    def _select_by_capacity(self, eligible: List[RouteCapability]) -> Optional[RouteCapability]:
        """Select route with most available capacity."""
        if not eligible:
            return None
        return max(eligible, key=lambda r: r.available_capacity)

    def _select_by_rate_spread(self, eligible: List[RouteCapability]) -> Optional[RouteCapability]:
        """Select route in least-used rate bucket, tiebreaking on per-route load."""
        if not eligible:
            return None

        def bucket_load(route: RouteCapability) -> int:
            return self._rate_bucket_counts.get(route.rate_bucket, 0)

        # Primary: least-used rate bucket
        min_bucket_load = min(bucket_load(r) for r in eligible)
        bucket_candidates = [r for r in eligible if bucket_load(r) == min_bucket_load]

        # Secondary: least used route within that bucket (per-route spread)
        def route_load(route: RouteCapability) -> int:
            return self._concurrent_per_route.get(route.route_id if hasattr(route, 'route_id') else '', 0)

        min_route_load = min(route_load(r) for r in bucket_candidates)
        final_candidates = [r for r in bucket_candidates if route_load(r) == min_route_load]

        # Tertiary: most available capacity
        return max(final_candidates, key=lambda r: r.available_capacity)

    def _create_lease(
        self,
        session_id: str,
        route: RouteCapability,
        pin_mode: PinMode,
        preferred_model: Optional[str],
        checkpoint_id: str,
    ) -> RouteLease:
        """Create a new lease from a route."""
        now_ms = int(time.time() * 1000)
        lease = RouteLease(
            session_id=session_id,
            route_id=route.route_id if hasattr(route, 'route_id') else f"route-{uuid.uuid4().hex[:8]}",
            provider=route.provider,
            model_id=route.model_id,
            capability_class=route.capability_class,
            assigned_at=now_ms,
            lease_expires_at=now_ms + self._lease_ttl_seconds * 1000,
            heartbeat_interval=self._heartbeat_interval,
            health_state=route.health.value,
            cooldown_state="none",
            pin_mode=pin_mode.value,
            classification=route.classification.value,
            credential_reference_id="",  # NO raw key
            checkpoint_id=checkpoint_id,
            task_correlation="",
            release_reason="",
            base_url=route.base_url,
            max_tokens=route.max_tokens,
            concurrent_limit=route.concurrent_limit,
            rate_bucket=route.rate_bucket,
        )
        return lease

    def _update_route_capacity(self, route: RouteCapability, increment: bool = True) -> None:
        """Update route capacity tracking."""
        rid = route.route_id if hasattr(route, 'route_id') else ''
        if increment:
            route.current_load += 1
            self._concurrent_per_route[rid] = self._concurrent_per_route.get(rid, 0) + 1
        else:
            route.current_load = max(0, route.current_load - 1)
            self._concurrent_per_route[rid] = max(0, self._concurrent_per_route.get(rid, 0) - 1)
        self._route_capacity[rid] = route

    def _update_rate_bucket_count(self, bucket: str, increment: bool = True) -> None:
        """Update rate bucket tracking."""
        if not bucket:
            return
        current = self._rate_bucket_counts.get(bucket, 0)
        self._rate_bucket_counts[bucket] = current + (1 if increment else -1)

    async def _update_route_health_on_failure(self, route_id: str) -> None:
        """Update route health when failure detected."""
        route = self._route_capacity.get(route_id)
        if not route:
            return

        # Update health
        if route.health == HealthState.HEALTHY:
            route.health = HealthState.DEGRADED
        elif route.health == HealthState.DEGRADED:
            route.health = HealthState.UNHEALTHY
            route.cooldown_until = time.time() + self._cooldown_duration_seconds

        await self._router.update_route_health(route_id, route.health)

    async def _handle_expired_lease(self, session_id: str) -> None:
        """Handle expired lease."""
        self.release_lease(session_id, LeaseReleaseReason.EXPIRED)

    # ── Persistence ──────────────────────────────────────────────────────

    def _load_leases(self) -> None:
        """Load persisted leases from disk."""
        if not self._lease_store_path:
            return
        path = Path(self._lease_store_path)
        if path.exists():
            try:
                with open(path, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                for sid, lease_data in data.items():
                    self._leases[sid] = RouteLease.from_dict(lease_data)
            except Exception:
                logger.warning("Failed to load route leases", exc_info=True)

    def _persist_lease(self, lease: RouteLease) -> None:
        """Persist a single lease."""
        if not self._lease_store_path:
            return
        path = Path(self._lease_store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {k: v for k, v in self._leases.items()}
            data[lease.session_id] = lease.to_dict()
            with open(path, 'w', encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            logger.warning("Failed to persist route lease", exc_info=True)

    def _persist_all_leases(self) -> None:
        """Persist all leases."""
        if not self._lease_store_path:
            return
        path = Path(self._lease_store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {sid: lease.to_dict() for sid, lease in self._leases.items()}
            with open(path, 'w', encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            logger.warning("Failed to persist all route leases", exc_info=True)


# ── Mock Router (for testing/verification) ─────────────────────────────────

class MockRouter(CanonicalRouterInterface):
    """Mock canonical router for testing/verification.
    
    Simulates pdv-provider-routing with healthy routes.
    """

    def __init__(self):
        self._routes: Dict[str, RouteCapability] = {}
        self._initialize_routes()

    def _initialize_routes(self):
        """Initialize mock routes for testing."""
        routes = [
            RouteCapability(
                route_id="nemotron-001",
                model_id="nemotron",
                provider="nvidia",
                base_url="127.0.0.1:11436/v1",
                capability_class="general",
                max_tokens=131072,
                is_paid=False,
                is_local=False,
                concurrent_limit=10,
                current_load=0,
                health=HealthState.HEALTHY,
                cooldown_until=0,
                rate_bucket="free-general",
                classification=RouteClassification.FREE,
            ),
            RouteCapability(
                route_id="minimax-001",
                model_id="minimax",
                provider="free",
                base_url="127.0.0.1:11437/v1",
                capability_class="general",
                max_tokens=65536,
                is_paid=False,
                is_local=False,
                concurrent_limit=5,
                current_load=0,
                health=HealthState.HEALTHY,
                cooldown_until=0,
                rate_bucket="free-general",
                classification=RouteClassification.FREE,
            ),
            RouteCapability(
                route_id="laguna-001",
                model_id="laguna",
                provider="nvidia",
                base_url="127.0.0.1:11438/v1",
                capability_class="vision",
                max_tokens=65536,
                is_paid=False,
                is_local=False,
                concurrent_limit=5,
                current_load=0,
                health=HealthState.HEALTHY,
                cooldown_until=0,
                rate_bucket="free-vision",
                classification=RouteClassification.FREE,
            ),
            RouteCapability(
                route_id="qwen-local-001",
                model_id="qwen3.6:ctx65k",
                provider="local",
                base_url="127.0.0.1:11435/v1",
                capability_class="general",
                max_tokens=65536,
                is_paid=False,
                is_local=True,
                concurrent_limit=20,
                current_load=0,
                health=HealthState.HEALTHY,
                cooldown_until=0,
                rate_bucket="local",
                classification=RouteClassification.LOCAL,
            ),
            RouteCapability(
                route_id="paid-001",
                model_id="paid-model",
                provider="nvidia",
                base_url="127.0.0.1:11439/v1",
                capability_class="reasoning",
                max_tokens=131072,
                is_paid=True,
                is_local=False,
                concurrent_limit=3,
                current_load=0,
                health=HealthState.HEALTHY,
                cooldown_until=0,
                rate_bucket="paid",
                classification=RouteClassification.HOSTED,
            ),
        ]
        for r in routes:
            self._routes[r.route_id] = r

    async def get_healthy_routes(self, capability_class: str = "general") -> List[RouteCapability]:
        """Return healthy routes matching capability."""
        routes = list(self._routes.values())
        if capability_class != "general":
            routes = [r for r in routes if r.capability_class == capability_class]
        return [r for r in routes if r.is_eligible and not r.is_paid]  # No paid fallback

    async def get_route_details(self, route_id: str) -> Optional[RouteCapability]:
        return self._routes.get(route_id)

    async def update_route_health(self, route_id: str, health: HealthState) -> bool:
        route = self._routes.get(route_id)
        if route:
            route.health = health
        return True

    async def check_rate_bucket(self, route_id: str) -> str:
        route = self._routes.get(route_id)
        return route.rate_bucket if route else ""

    async def get_concurrent_count(self, route_id: str) -> int:
        route = self._routes.get(route_id)
        return route.current_load if route else 0

    def add_cooldown(self, route_id: str, duration_seconds: int = 300) -> None:
        """Add cooldown to a route for testing."""
        route = self._routes.get(route_id)
        if route:
            route.health = HealthState.COOLED
            route.cooldown_until = time.time() + duration_seconds

    def add_429_failure(self, route_id: str) -> None:
        """Simulate 429 failure on a route for testing."""
        route = self._routes.get(route_id)
        if route:
            route.health = HealthState.UNHEALTHY
            route.cooldown_until = time.time() + 300


# ── Integration with HermesState ────────────────────────────────────────────

# Module-level singleton for use by Hermes
_route_lease_manager: Optional[RouteLeaseManager] = None


def get_route_lease_manager() -> RouteLeaseManager:
    """Get the module-level route lease manager singleton."""
    global _route_lease_manager
    if _route_lease_manager is None:
        _route_lease_manager = RouteLeaseManager()
    return _route_lease_manager


def reset_route_lease_manager() -> None:
    """Reset the module-level route lease manager (for testing)."""
    global _route_lease_manager
    _route_lease_manager = None


# ── Testing ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def main():
        # Reset for clean test
        reset_route_lease_manager()

        manager = get_route_lease_manager()
        manager._router = MockRouter()

        # Test 1: Allocate leases for multiple sessions
        print("=== Test 1: Multi-session allocation ===")
        sessions = ["tab-a", "tab-b", "tab-c", "tab-d", "tab-e"]
        for sid in sessions:
            result = await manager.allocate_lease(sid, capability_class="general")
            print(f"  {sid}: {result.success} -> {result.provider}/{result.model_id} ({result.reason})")

        # Test 2: Distribution
        print("\n=== Test 2: Distribution ===")
        dist = manager.get_lease_distribution()
        for route, sids in dist.items():
            print(f"  {route}: {len(sids)} sessions")

        # Test 3: 429 rotation
        print("\n=== Test 3: 429 rotation ===")
        if "tab-a" in manager._leases:
            old_lease = manager._leases["tab-a"]
            print(f"  tab-a before: {old_lease.provider}/{old_lease.model_id}")
            result = await manager.rotate_lease("tab-a", reason="429")
            print(f"  tab-a after: {result.success} -> {result.provider}/{result.model_id}")

        # Test 4: Lease release
        print("\n=== Test 4: Lease release ===")
        manager.release_lease("tab-e", LeaseReleaseReason.SESSION_CLOSE)
        print(f"  Active leases: {manager.get_active_lease_count()}")

        # Test 5: Exact pin
        print("\n=== Test 5: Exact pin ===")
        manager._router.add_cooldown("qwen-local-001", 300)  # Cool down local
        result = await manager.allocate_lease(
            "tab-f",
            pin_mode=PinMode.EXACT,
            preferred_model="qwen3.6:ctx65k",
        )
        print(f"  tab-f exact pin qwen3.6: {result.success} ({result.reason})")

        # Test 6: Switch mode
        print("\n=== Test 6: Mode switch ===")
        result = await manager.switch_pin_mode("tab-b", PinMode.EXACT, "nemotron")
        print(f"  tab-b switch to nemotron: {result.success}")

        print("\n=== All tests complete ===")

    asyncio.run(main())
