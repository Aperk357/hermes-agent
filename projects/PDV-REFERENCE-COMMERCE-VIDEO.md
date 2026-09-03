# PDV Reference Commerce Video — Workstream State

**Project:** Faceless Video (PDV) RightsAndConsent V2 production enforcement
**Repo:** Aperk357/Faceless-Video, branch: claude/rights-and-consent-v2-complete-v1

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
- Status: open, BLOCKER addressed — awaiting NON-CLAUDE exact-head review at 6d342e8 + merge
- Prior review (Aperk357, 72201dc): BLOCKER_COMMENT — stale-snapshot eligibility at POST /render-jobs gate
- Fix (f2dadea + 6d342e8): evaluateRightsAndConsent(rightsInput, new Date()) replaces snapshot trust; N10 causal negative added; Prettier formatted

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

- [x] CI green on PR #65 head — CONFIRMED (6d342e8, both gate jobs completed/success 2026-09-03T07:07 UTC)
- [ ] NON-CLAUDE exact-head review at 6d342e8 — PENDING (blocker addressed; CI green; new review required per any-byte-change rule)
- [ ] NON-CLAUDE distinct integration (merge) — PENDING
- [ ] Postmerge production-path proof — PENDING (after merge)
- [ ] RIGHTS_V2_TERMINAL=true receipt — PENDING
- [ ] CTC_HANDOFF_READY=true — PENDING
