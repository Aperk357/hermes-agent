"""Tests for agent/route_capacity_advisor.py.

Real concurrency proof (actual threads against the real implementation, not
a mock) for the specific defect class NW-CHK-0008 Lane B found in
route_lease_manager.py (zero locking on shared cross-session state).
"""
import threading
import time

import pytest

from agent.route_capacity_advisor import (
    RouteCapacityAdvisor,
    get_route_capacity_advisor,
    reset_route_capacity_advisor,
)


def _chain(*pairs):
    return [{"provider": p, "model": m} for p, m in pairs]


def test_empty_state_returns_chain_unchanged():
    adv = RouteCapacityAdvisor()
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"))
    result = adv.advise_order(chain)
    assert result == chain
    assert result is not chain  # returns a copy, never the same list object


def test_single_chain_entry_is_never_reordered():
    adv = RouteCapacityAdvisor()
    chain = _chain(("nvidia", "nemotron"))
    for _ in range(5):
        adv.record_assignment(f"s{_}", "nvidia", "nemotron")
    assert adv.advise_order(chain) == chain


def test_below_threshold_load_does_not_reorder():
    adv = RouteCapacityAdvisor(load_threshold=2)
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"))
    adv.record_assignment("s1", "nvidia", "nemotron")  # only 1 assignment, below threshold
    assert adv.advise_order(chain) == chain


def test_at_threshold_with_less_loaded_alternative_reorders():
    adv = RouteCapacityAdvisor(load_threshold=2)
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"))
    adv.record_assignment("s1", "nvidia", "nemotron")
    adv.record_assignment("s2", "nvidia", "nemotron")  # head now has load 2, alibaba/qwen has 0
    result = adv.advise_order(chain)
    assert result[0] == {"provider": "alibaba", "model": "qwen"}
    assert result[1] == {"provider": "nvidia", "model": "nemotron"}
    # permutation only -- same elements, no invention/loss
    assert sorted(result, key=lambda e: (e["provider"], e["model"])) == sorted(chain, key=lambda e: (e["provider"], e["model"]))


def test_at_threshold_with_no_less_loaded_alternative_does_not_reorder():
    adv = RouteCapacityAdvisor(load_threshold=2)
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"))
    adv.record_assignment("s1", "nvidia", "nemotron")
    adv.record_assignment("s2", "nvidia", "nemotron")
    adv.record_assignment("s3", "alibaba", "qwen")
    adv.record_assignment("s4", "alibaba", "qwen")  # both entries at load 2 -- tie, no strictly-less alternative
    assert adv.advise_order(chain) == chain


def test_release_removes_assignment_immediately():
    adv = RouteCapacityAdvisor(load_threshold=1)
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"))
    adv.record_assignment("s1", "nvidia", "nemotron")
    assert adv.current_load("nvidia", "nemotron") == 1
    adv.release("s1")
    assert adv.current_load("nvidia", "nemotron") == 0
    assert adv.advise_order(chain) == chain  # load back below threshold


def test_ttl_expiry_stops_counting_stale_assignments():
    adv = RouteCapacityAdvisor(ttl_seconds=0.05, load_threshold=1)
    adv.record_assignment("s1", "nvidia", "nemotron")
    assert adv.current_load("nvidia", "nemotron") == 1
    time.sleep(0.1)
    assert adv.current_load("nvidia", "nemotron") == 0, "TTL-expired assignment must stop counting toward load without an explicit release()"


def test_advise_order_never_mutates_input_list():
    adv = RouteCapacityAdvisor(load_threshold=1)
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"))
    original = list(chain)
    adv.record_assignment("s1", "nvidia", "nemotron")
    adv.advise_order(chain)
    assert chain == original, "advise_order must never mutate the caller's list in place"


def test_malformed_entries_are_treated_as_zero_load_not_crashed():
    adv = RouteCapacityAdvisor(load_threshold=1)
    chain = [{"provider": "nvidia", "model": "nemotron"}, {"weird": "entry"}]
    adv.record_assignment("s1", "nvidia", "nemotron")
    result = adv.advise_order(chain)  # must not raise
    assert len(result) == 2


def test_concurrent_record_and_advise_real_threads_no_crash_and_consistent_state():
    """Real threads, not a mock -- the exact defect class route_lease_manager.py
    (NW-CHK-0008 Lane B finding #1) shipped without any protection against."""
    adv = RouteCapacityAdvisor(load_threshold=2)
    chain = _chain(("nvidia", "nemotron"), ("alibaba", "qwen"), ("local", "qwen3.6"))
    errors = []
    n_threads = 32
    n_iterations = 50

    def worker(idx: int) -> None:
        try:
            session_id = f"session-{idx}"
            for i in range(n_iterations):
                provider, model = chain[i % len(chain)]["provider"], chain[i % len(chain)]["model"]
                adv.record_assignment(session_id, provider, model)
                adv.advise_order(chain)
                if i % 7 == 0:
                    adv.release(session_id)
        except Exception as e:  # pragma: no cover - failure path
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"concurrent access raised: {errors}"
    assert len(adv._assignments) <= n_threads, "no torn/duplicated state -- at most one assignment per session"


def test_shared_singleton_accessor_returns_same_instance():
    reset_route_capacity_advisor()
    a = get_route_capacity_advisor()
    b = get_route_capacity_advisor()
    assert a is b


def test_reset_singleton_produces_a_fresh_instance():
    reset_route_capacity_advisor()
    a = get_route_capacity_advisor()
    a.record_assignment("s1", "nvidia", "nemotron")
    reset_route_capacity_advisor()
    b = get_route_capacity_advisor()
    assert a is not b
    assert b.current_load("nvidia", "nemotron") == 0
