# RIGHTS_V2 Production Seam Checkpoint
**Date:** 2026-09-03
**Workstream:** FACELESS_RIGHTS_V2_TO_TERMINAL_AND_CTC_HANDOFF_V1
**Source repo of the work described below:** `Aperk357/Faceless-Video` (NOT this repo, `Aperk357/hermes-agent`). This file is a governance checkpoint stored here for cross-project tracking; none of the commits, PRs, or file paths below exist in hermes-agent. See `PROVENANCE UPDATE` below for verification and current status.
**State (at original write time):** PRODUCTION_SEAM_WIRED — pending CI + NON-CLAUDE distinct integration

---

## PROVENANCE UPDATE (2026-09-03, added during independent reconciliation)

An independent review flagged this checkpoint because, read in isolation inside
`hermes-agent`, it does not state which repository the referenced commits and
PRs belong to. Reconciliation against live GitHub source (not prose) found:

- All SHAs below (`b583c8917d`, `1510f5b`, `7310a24`, `775bd99`, `04af173`) resolve
  exactly, with matching commit messages, in `Aperk357/Faceless-Video` — **not**
  in `hermes-agent`. STATUS: VALID, WRONG-REPO-IMPLIED (now corrected above).
- PR #64 and PR #65 referenced below are `Aperk357/Faceless-Video#64` and `#65`,
  not any PR in this repo (this repo's own PRs are numbered separately).
- PR #65 has since **merged**: `2ff27e99b933a29025b958e5dfa02900b1a8691c`, confirmed
  as current `Faceless-Video` `main` HEAD.
- Per `Aperk357/Nightwatch` checkpoint `NW-CHK-FACELESS-RIGHTS-V2-PR65-RECONCILE-COLLISION-2026-09-03`
  (superseding the gate values in the table below): **`RIGHTS_V2_TERMINAL = TRUE`**
  and **`CTC_HANDOFF_READY = TRUE`** as of the postmerge readback recorded there.
  The `BLOCKED_RIGHTS_REMAINS=true` / `RIGHTS_V2_TERMINAL=false` table below reflects
  the state at the time this file was originally written and is now stale — kept
  verbatim for forensic history, not as current status.
- The `videoEngine` gap noted at the bottom of this file is still open per that
  same Nightwatch record and remains accurate.

---

## Predecessor receipts

| Receipt | Value |
|---|---|
| PR #64 MERGE_SHA | b583c8917d |
| PR #65 reconcile commit | 1510f5b |
| NON-CLAUDE review fix (Hermes/nemotron-3-super-120b) | 7310a24 |
| Production seam commit | 775bd99 |
| Post-merge push HEAD | 04af173 |
| Branch | claude/rights-and-consent-v2-complete-v1 |

---

## Non-Claude review finding and fix

The independent adversarial reviewer (Hermes/nemotron-3-super-120b, non-Claude)
returned a BLOCKER on PR #65: `verifyProvenanceReceipt()` trusted the caller-
supplied `publication_eligible` field (snapshot-trusted), so a record eligible at
T0 remained eligible after its own expiry at T1. Fix (7310a24): re-derive
eligibility from record inputs at verification time using the provided `now`
argument (`RIGHTS_NOT_ELIGIBLE_AT_VERIFY`). Residual documented in source:
post-evaluation revocations require a live lookup, which is out of contract scope.

---

## Production seam wiring (775bd99 / 04af173)

### Files changed
- `shared/schema/pdv90.ts` — `rightsRecord jsonb` + `rightsState text` columns added to `renderJobs`
- `shared/validation/schemas.ts` — `renderJobCreateSchema` now requires `rights_record: RightsAndConsentV2Schema`
- `server/routes/renderJobs.ts` — enforcement block inserted after approval check, before fingerprint:
  1. Parse `rights_record` with `RightsAndConsentV2Schema` → fail closed on malformed (400)
  2. Check `publication_eligible === true` → fail closed on ineligible (403)
  3. Run `verifyJobRightsBinding` → fail closed on binding mismatch (403)
  4. Store `rightsRecord` + `rightsState` in DB row

### Causal negatives proven (10/10 tests pass)
| Control | Failure mode | Status |
|---|---|---|
| POSITIVE | Eligible attested record accepted | PASS 201 |
| N1 | Unattested VERIFIED (evidence_refs empty) | FAIL_CLOSED 400 |
| N2 | UNVERIFIED source authority | FAIL_CLOSED 403 |
| N3 | Territory mismatch | FAIL_CLOSED 403 |
| N4 | Purpose mismatch | FAIL_CLOSED 403 |
| N5 | Revoked authority | FAIL_CLOSED 403 |
| N6 | Missing rights_record (absent) | FAIL_CLOSED 400 |
| N7 | Malformed rights_record (not object) | FAIL_CLOSED 400 |
| N8 | Expired rights (expiry past) | FAIL_CLOSED 403 |
| N9 | Revoked consent | FAIL_CLOSED 403 |

### Test counts post-merge
- Rights enforcement: 10/10 PASS
- Contract suite: 78/81 PASS (3 ffmpeg baseline failures, pre-existing on main)
- Idempotency: 3/3 PASS (updated with valid rights_record)
- Tenant isolation: 2/2 PASS (updated with valid rights_record)

---

## Current workstream state

| Gate | Value |
|---|---|
| BLOCKED_RIGHTS_REMAINS | true |
| RIGHTS_V2_TERMINAL | false |
| CTC_HANDOFF_READY | false |
| PR #65 CI on 04af173 | pending |
| NON-CLAUDE distinct integration | pending (external dependency) |
| Production seam verified | true (contract + route + 10 causal negatives) |

---

## Remaining blockers to RIGHTS_V2_TERMINAL=true

1. PR #65 CI on head 04af173 must be green
2. NON-CLAUDE human must perform distinct integration (cannot be a Claude subagent)
3. Postmerge production-path proof after PR #65 merges to main
4. Exact-head review on final merged state (after any byte changes)

---

## Postmerge verification plan

After PR #65 merges:
1. Confirm `04af173` is the merged head (or adjusted for any rebase)
2. Run full contract + integration test suite on main
3. Confirm `POST /render-jobs` with missing rights_record returns 400 on production
4. Confirm `POST /render-jobs` with ineligible rights returns 403 on production
5. Write RIGHTS_V2_TERMINAL=true receipt only when all gates confirm

---

## Open failure domain: videoEngine path

`POST /api/video-engine/generate` has no rights enforcement and goes through a
different bridge service (`videoEngineBridge`). This is a separate failure domain
outside current PR #65 scope. Must be addressed before CTC_HANDOFF_READY=true.
