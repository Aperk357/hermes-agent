"""Cross-session fallback-order capacity advisor.

Per Nightwatch NW-CHK-0009's evidence-backed router reconciliation: the live
production router (`resolve_provider_client` / `agent._fallback_chain` /
`_try_activate_fallback` in `chat_completion_helpers.py`) already owns final
provider/model selection, failover, per-session isolation, exact pinning
(`/model`), and error handling — all live, all more mature than
`route_lease_manager.py`'s equivalents. That module's SMART/rate-bucket
allocation was the one capability with no live equivalent: nothing today
coordinates which route concurrent sessions/tabs prefer, so N tabs opened at
once can all pick the same first-choice fallback entry with zero awareness
of each other.

This module is the bounded, single-purpose absorption of that one primitive,
per the reconciliation's Option A (LIVE_ROUTER_CANONICAL_ABSORB_LEASE_PRIMITIVES)
— NOT a second router. It does not select a provider/model, does not talk to
any provider API, does not participate in failover, and does not touch
`_try_activate_fallback`/`resolve_provider_client` at all. Its only job is:
given the `_fallback_chain` list `init_agent()` already builds from config,
optionally move a less-loaded candidate to the front when the current head
looks concentrated — a soft nudge over an ordering the existing router will
walk exactly as before.

Deliberately does NOT replicate `route_lease_manager.py`'s
`RouteCapability`/`RouteCapacity`/rate-bucket model: that data (real
concurrent limits, real rate buckets) has no live source anywhere in this
estate (`CanonicalRouterInterface` has zero non-mock implementations — see
NW-CHK-0008 Lane B). Inventing capacity numbers to feed a richer algorithm
would be fabrication. The only real, honest signal available today is an
in-process count of which (provider, model) pair each currently-active
session most recently preferred — so that is the only signal this module
uses.

Fail-safe by construction: every public method is exception-safe internally,
and `agent_init.py`'s call site additionally wraps the whole advisory step
in its own try/except — an error here must never break agent
initialization. Concurrency-safe by construction (the opposite of
`route_lease_manager.py`'s finding #1): a single `threading.Lock` guards all
state.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Tuple

# How long an assignment counts toward load before it's treated as stale.
# Self-expiring by design — route_lease_manager.py's lease-expiry leak
# (NW-CHK-0008 Lane B finding #3) is deliberately not repeated here: there is
# no explicit release() this module depends on for correctness, only for
# promptness. A session that never releases still stops counting after TTL.
DEFAULT_TTL_SECONDS = 900.0

# Only nudge the order when the current head already has at least this many
# live concurrent assignments AND a strictly less-loaded alternative exists.
# A single active session must never trigger a reorder.
DEFAULT_LOAD_THRESHOLD = 2


class RouteCapacityAdvisor:
    """In-process, thread-safe, TTL-expiring advisor over fallback-chain order.

    Not a singleton by class design — `get_route_capacity_advisor()` below
    provides the process-wide shared instance real callers use; the class
    itself is directly instantiable for tests.
    """

    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS, load_threshold: int = DEFAULT_LOAD_THRESHOLD) -> None:
        self._ttl_seconds = ttl_seconds
        self._load_threshold = load_threshold
        self._lock = threading.Lock()
        # session_id -> (provider, model, last_seen_monotonic)
        self._assignments: Dict[str, Tuple[str, str, float]] = {}

    def _prune_stale_locked(self, now: float) -> None:
        """Caller must hold self._lock."""
        stale = [sid for sid, (_, _, seen) in self._assignments.items() if now - seen > self._ttl_seconds]
        for sid in stale:
            del self._assignments[sid]

    def record_assignment(self, session_id: str, provider: str, model: str) -> None:
        """Register that `session_id` currently prefers (provider, model).

        Safe to call repeatedly for the same session (e.g. once per turn) —
        each call refreshes both the assignment and its TTL clock.
        """
        if not session_id or not provider or not model:
            return
        now = time.monotonic()
        with self._lock:
            self._prune_stale_locked(now)
            self._assignments[session_id] = (provider, model, now)

    def release(self, session_id: str) -> None:
        """Best-effort explicit release. Not required for correctness — see TTL above."""
        if not session_id:
            return
        with self._lock:
            self._assignments.pop(session_id, None)

    def _load_for_locked(self, provider: str, model: str, now: float) -> int:
        """Caller must hold self._lock. Assumes _prune_stale_locked already ran."""
        return sum(1 for (p, m, _) in self._assignments.values() if p == provider and m == model)

    def current_load(self, provider: str, model: str) -> int:
        """Current live assignment count for (provider, model). Exposed for tests/observability."""
        now = time.monotonic()
        with self._lock:
            self._prune_stale_locked(now)
            return self._load_for_locked(provider, model, now)

    def advise_order(self, chain: List[dict]) -> List[dict]:
        """Return a possibly-reordered COPY of `chain`; never mutates the input.

        `chain` is `agent._fallback_chain`'s own shape: a list of
        `{"provider": ..., "model": ..., ...}` dicts, already in the order
        config/admin intent placed them. This method only ever performs a
        permutation of that exact list — it never adds, drops, or invents an
        entry, and it only moves an entry when the current head is at or
        above the load threshold and a strictly less-loaded alternative
        exists later in the chain. Absent that specific condition, the
        input order is returned unchanged (as a new list object).
        """
        if not chain or len(chain) < 2:
            return list(chain)

        now = time.monotonic()
        with self._lock:
            self._prune_stale_locked(now)

            def load_of(entry: dict) -> int:
                provider = entry.get("provider")
                model = entry.get("model")
                if not provider or not model:
                    return 0
                return self._load_for_locked(provider, model, now)

            head = chain[0]
            head_load = load_of(head)
            if head_load < self._load_threshold:
                return list(chain)

            best_index = None
            best_load = head_load
            for i in range(1, len(chain)):
                candidate_load = load_of(chain[i])
                if candidate_load < best_load:
                    best_load = candidate_load
                    best_index = i

            if best_index is None:
                return list(chain)

            reordered = list(chain)
            reordered[0], reordered[best_index] = reordered[best_index], reordered[0]
            return reordered


_shared_advisor: "RouteCapacityAdvisor | None" = None
_shared_advisor_lock = threading.Lock()


def get_route_capacity_advisor() -> RouteCapacityAdvisor:
    """Process-wide shared advisor instance. Thread-safe lazy singleton."""
    global _shared_advisor
    if _shared_advisor is None:
        with _shared_advisor_lock:
            if _shared_advisor is None:
                _shared_advisor = RouteCapacityAdvisor()
    return _shared_advisor


def reset_route_capacity_advisor() -> None:
    """Test-only: replaces the shared singleton with a fresh instance."""
    global _shared_advisor
    with _shared_advisor_lock:
        _shared_advisor = RouteCapacityAdvisor()
