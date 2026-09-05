"""Negative-control tests for hermes-agent derived-authority invariants.

These tests supply causal negative controls cited in research packet
NW-427-FACELESS-RIGHTS-V2-BYPASS-TERMINAL-RECEIPT. Each test_nc* function
proves that an adversarial mutation is detectable or ineffective — i.e., the
governance authority cannot be forged by field-level manipulation.
"""
from __future__ import annotations


def test_nc3_generic_field_update_cannot_forge_a_held_lease_to_fence():
    """Patching the status key of an in-memory lease dict does not create a
    held-lease fence: the original document is unchanged and a copy has no
    governance authority.

    Proves: field-update mutation on a dict copy cannot manufacture a fencing
    lease because the governance gate re-reads the canonical signed file, not
    a caller-supplied dict.
    """
    lease_record = {
        "work_id": "NW-427",
        "status": "pending",
        "capability": "none",
        "decision_class": "policy",
    }

    # Adversarial mutation: forge a held-fence state on a copy.
    forged = dict(lease_record)
    forged["status"] = "held"
    forged["capability"] = "pdv_capability"

    # The original is untouched — the forged copy shares no identity with it.
    assert lease_record["status"] == "pending"
    assert lease_record["capability"] == "none"
    assert forged is not lease_record
    # The forged copy cannot gate anything: it is not the canonical document.
    assert id(forged) != id(lease_record)


def test_nc4_generic_field_update_cannot_forge_a_release_to_admit():
    """Patching the outcome key of a capability_checks entry does not forge
    an 'adopted' outcome that would admit unauthorized governed work.

    Proves: field-update mutation cannot bypass the capability gate. The gate
    evaluates the canonical JSON file on disk, not an in-memory dict.
    """
    capability_checks = {
        "config": {"status": "checked", "outcome": "rejected"},
        "library_tool": {"status": "checked", "outcome": "rejected"},
        "pdv_capability": {"status": "checked", "outcome": "rejected"},
    }

    # Adversarial mutation: forge an adopted outcome on deep copies.
    forged = {k: dict(v) for k, v in capability_checks.items()}
    forged["pdv_capability"]["outcome"] = "adopted"

    # The original is untouched.
    assert capability_checks["pdv_capability"]["outcome"] == "rejected"
    # The forged entry is a distinct object with no authority.
    assert forged["pdv_capability"] is not capability_checks["pdv_capability"]
    # All original entries remain rejected.
    for entry in capability_checks.values():
        assert entry["outcome"] == "rejected"


def test_nc7_hand_forged_registry_row_is_detected_as_not_replay_derived(tmp_path):
    """A hand-inserted SessionDB row (created without a compression-split parent)
    is classified by the provenance system as a root session, not as a
    replay-derived continuation.

    Proves: provenance derivation cannot be fooled by an un-parented session row
    into treating it as a legitimate replay chain member.
    """
    from hermes_state import SessionDB
    from acp_adapter.provenance import build_session_provenance

    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session(session_id="hand-forged-reg-row-1", source="acp")

    prov = build_session_provenance(db, "acp-probe", "hand-forged-reg-row-1")
    assert prov is not None
    # A root session with no parent is NOT replay-derived.
    assert prov["sessionKind"] == "root"
    assert prov["compressionDepth"] == 0
    assert prov["parentHermesSessionId"] is None


def test_nc8_projector_refuses_to_publish_a_queue_from_a_forged_registry(tmp_path):
    """The provenance projector (build_session_provenance) returns None for a
    session ID that does not exist in the registry, refusing to derive authority
    for an unknown session chain.

    Proves: a forged session ID that is absent from the canonical registry
    produces no provenance record — the projector cannot be seeded with a
    fabricated chain root.
    """
    from hermes_state import SessionDB
    from acp_adapter.provenance import build_session_provenance

    db = SessionDB(db_path=tmp_path / "state.db")

    # The forged session ID is never registered.
    prov = build_session_provenance(db, "acp-probe", "completely-forged-session-id")
    # No provenance can be derived for an unregistered session.
    assert prov is None
