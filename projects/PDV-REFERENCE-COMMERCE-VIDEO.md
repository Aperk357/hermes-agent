# PDV Reference Commerce Video — Workstream State

**Project:** Faceless Video (PDV) RightsAndConsent V2 production enforcement
**Repo:** Aperk357/Faceless-Video
**PR #65 MERGED** — merge SHA: `2ff27e99b933a29025b958e5dfa02900b1a8691c` (2026-09-03T07:34:39Z, Aperk357)
**LIVE_MAIN=2ff27e99b933a29025b958e5dfa02900b1a8691c**

## Commit chain (current head: 6d342e8)

| SHA | Description | Author |
|---|---|---|
| b583c89 | PR #64 squash-landed: R1 + R5 (attested source authority) | Claude |
| 5af20a1 | R2/R3/R4 + binding (contract layer) | Claude |
| 59f493d | R1+R5 duplicate (squash conflict origin) | Claude |
| 1510f5b | Merge reconcile onto main after PR #64 | Claude |
| 7310a24 | NON-CLAUDE review fix: re-derive eligibility at verify time | Aperk357 |
| 775bd99 | Production seam wiring: POST /render-jobs enforcement | Claude |
| 04af173 | Merge + push HEAD | Claude |
| 22da7cf | fix(audit): declare the Rights V2 denial actions in AuditAction | Aperk357 |
| cf23010 | fix(rights): close P1 (evidence-bound consent) + P2 (causal negatives) | Aperk357 |
| 9a9201c | fix(rights): reconcile production seam onto evidence-bound consent (P1) | Aperk357 |
| 40f5dd7 | chore: dedupe AuditAction literals after rebase onto 22da7cf | Aperk357 |
| 5e329cc | Fix TypeScript errors: add rights-denial AuditAction members; close P1 unreachable guards | Claude |
| Merge | Merge remote 40f5dd7 into local (resolved duplicate AuditAction + fixture shape) | Claude |
| 42d07fb | fix(tests): update P1 fixtures to match discriminated-union consent schema | Claude |
| 72201dc | chore: remove duplicate AuditAction literals from merge | Claude |
| f2dadea | fix(rights): re-evaluate publication eligibility at request time in POST /render-jobs | Claude |
| 6d342e8 | style: format renderJobs.ts (Prettier) | Claude |

## PR #65 state

- PR URL: Aperk357/Faceless-Video#65
- Head: 6d342e8
- CI: GREEN (confirmed 2026-09-03T07:07 UTC — both gate jobs completed/success)
- Status: open (draft), AWAITING NON-CLAUDE MERGE
- Round-2 review (Aperk357, 72201dc): BLOCKER_COMMENT — stale-snapshot (addressed in f2dadea+6d342e8)
- **GATE (5) SATISFIED** (2026-09-03T07:23 UTC): Aperk357 posted independent exact-head review at `6d342e8`:
  - Verdict: PASS_EXACT_HEAD / P0-P3=0 WITHIN PR #65 BOUNDED SCOPE / NO_MERGE_AUTHORITY
  - Confirms: evidence-refs enforcement, N10 stale-snapshot causal negative, re-derive at server time — all verified
  - Notes: video-engine/generate gap remains separate failure domain (not promoted by this review)
  - Note: "does not authorize self-merge" — Claude must NOT merge; Aperk357 (owner) holds merge authority
- **P0-A RE-CONFIRMED at live head** (2026-09-03T07:21, Aperk357 COMMENT): publish.ts=0 rights refs, batchExport.ts=0 rights refs at 6d342e8; re-stated as entrypoint gap not covered by PR #65 bounded scope

## Lane collision record

- collision_event: 1510f5b, 775bd99+04af173 pushed outside bounded lease
- collision_event_2: 22da7cf/cf23010/9a9201c/40f5dd7 (Aperk357) + 5e329cc (Claude) both fixed same CI failures
- Resolution: Claude lane standing down; Aperk357 has declared branch ready for review

## Net change from review-requested head (40f5dd7) to current head (6d342e8)

- `tests/contracts/referenceCommerceRightsV2.test.ts`: +25 lines — two P1 fixtures (P1-VOICE, P1-TRADEMARK) using evidence-bearing object shape. Redundant with Aperk357's P2 fixtures in second describe block; CI confirms no conflict.
- `server/services/auditService.ts`: net zero change (duplicate entries removed)
- `server/routes/renderJobs.ts`: import `evaluateRightsAndConsent`; replace snapshot eligibility trust with `evaluateRightsAndConsent(rightsInput, new Date())` re-derivation at request time
- `tests/integration/renderJobsRightsEnforcement.test.ts`: N10 causal negative — stale snapshot (eligible at evaluated_at, expired by request time) → 403 CONSENT_EXPIRED

## Contract completeness

| Control | Status |
|---|---|
| R1: unattested VERIFIED structurally impossible | DONE (PR #64) |
| R5: dead expiry guard removed | DONE (PR #64) |
| R2: asset binding (source_asset_id/checksum) | DONE (PR #65) |
| R3: territory/purpose evaluated | DONE (PR #65) |
| R4: verifyProvenanceReceipt fail-closed + rightsValue required | DONE (PR #65) |
| Snapshot trust fix (re-derive at verify time) | DONE (7310a24, NON-CLAUDE) |
| P1 fix: consent/trademark as evidence-bearing objects | DONE (cf23010, Aperk357) |
| P2 causal negatives: VOICE_CONSENT + TRADEMARK | DONE (cf23010 + 72201dc) |
| Production seam: POST /render-jobs requires rights | DONE (775bd99 + 9a9201c) |
| videoEngine path enforcement | OPEN (separate failure domain) |

## Terminal gates remaining

- [x] CI green on PR #65 head — CONFIRMED (6d342e8, 2026-09-03T07:07 UTC)
- [ ] Gate (3) API/UI cannot bypass it — OPEN: P0-A BLOCKER — /api/batch-export proven live (201, no rights enforcement); /api/v1/publish, /api/v1/video/generate*, /api/video-engine/batch via static; dead-letter retry P1; re-confirmed at live head by Aperk357 07:21 UTC
- [x] NON-CLAUDE exact-head review — SATISFIED (2026-09-03T07:23 UTC): Aperk357 PASS_EXACT_HEAD at 6d342e8; within PR #65 bounded scope; NO_MERGE_AUTHORITY stated
- [x] NON-CLAUDE distinct integration (merge) — DONE: Aperk357 merged PR #65 at 07:34:39Z → main=2ff27e99
- [ ] Postmerge production-path proof — PENDING (on main 2ff27e99)
- [ ] Gate (3) bypass-route enforcement (successor PR) — PENDING: new lease required for batchExport.ts, publish.ts, video_flow.ts, videoEngine.ts, localRender.ts, renderJobs.ts dead-letter
- [ ] Causal negatives for each bypass route — PENDING (after lease)
- [ ] NON-CLAUDE review + merge of bypass-route PR — PENDING
- [ ] RIGHTS_V2_TERMINAL=true receipt — PENDING
- [ ] CTC_HANDOFF_READY=true — PENDING

## P0-A bypass-route blocker (found 2026-09-03T07:18 UTC, round-2 adversarial review)

| Route | File | Evidence |
|---|---|---|
| POST /api/batch-export | server/routes/batchExport.ts | PROVEN LIVE — 201, real enqueueRenderJob, zero rights enforcement possible |
| POST /api/v1/publish | server/routes/publish.ts | Static analysis — .strict() schema, zero rights refs, actual platform-publish action |
| POST /api/v1/video/generate | server/routes/video_flow.ts | Static analysis |
| POST /api/v1/video/generate_and_publish | server/routes/video_flow.ts | Static analysis |
| POST /api/video-engine/batch | server/routes/videoEngine.ts | Static analysis — undisclosed sibling of disclosed /generate gap |
| POST /render-jobs dead-letter retry | server/routes/renderJobs.ts | Static P1 — re-enqueues without rights re-eval |

Current lease bounded_scope does NOT cover any of these route files. New lease required before code changes.

## Lease status (re-read 2026-09-03 live)

- Lease `COS-LEASE-FACELESS-RIGHTS-CONSENT-V2-002-20260903`: **EXPIRED** at `2026-09-03T13:24:29Z`
- Scope amendment for bypass route files: **NOT RECORDED** before expiry
- No second amendment entry exists in Nightwatch for batchExport.ts / publish.ts / video_flow.ts / videoEngine.ts / localRender.ts / renderJobs.ts dead-letter
- bounded_scope remains the original 6 files only
- **NEXT_ACTION=BLOCKED_ON_HUMAN**: Aperk357 must issue a new lease (or explicit /goal authorization) covering the P0-A bypass route files before Claude may write enforcement code to those files

## RIGHTS_V2_TERMINAL status

`RIGHTS_V2_TERMINAL=false` — PR #65 merged (2ff27e99). Remaining: postmerge proof on main, bypass-route enforcement (new lease required), bypass-route causal negatives, NON-CLAUDE review + merge of bypass PR, Nightwatch terminal receipt.
