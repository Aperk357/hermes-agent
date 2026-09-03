# PDV Reference Commerce Video — Workstream State

**Project:** Faceless Video (PDV) RightsAndConsent V2 production enforcement
**Repo:** Aperk357/Faceless-Video, branch: claude/rights-and-consent-v2-complete-v1

## Commit chain

| SHA | Description |
|---|---|
| b583c89 | PR #64 squash-landed: R1 + R5 (attested source authority) |
| 5af20a1 | R2/R3/R4 + binding (contract layer) |
| 59f493d | R1+R5 duplicate (squash conflict origin) |
| 1510f5b | Merge reconcile onto main after PR #64 |
| 7310a24 | NON-CLAUDE review fix: re-derive eligibility at verify time |
| 775bd99 | Production seam wiring: POST /render-jobs enforcement |
| 04af173 | Merge + push HEAD (current) |

## PR #65 state

- PR URL: Aperk357/Faceless-Video#65
- Head: 04af173
- Status: open, awaiting CI + NON-CLAUDE distinct integration

## Contract completeness

| Control | Status |
|---|---|
| R1: unattested VERIFIED structurally impossible | DONE (PR #64) |
| R5: dead expiry guard removed | DONE (PR #64) |
| R2: asset binding (source_asset_id/checksum) | DONE (PR #65) |
| R3: territory/purpose evaluated | DONE (PR #65) |
| R4: verifyProvenanceReceipt fail-closed + rightsValue required | DONE (PR #65) |
| Snapshot trust fix (re-derive at verify time) | DONE (7310a24, NON-CLAUDE) |
| Production seam: POST /render-jobs requires rights | DONE (775bd99) |
| videoEngine path enforcement | OPEN (separate failure domain) |

## Terminal gates remaining

- PR #65 CI green on 04af173
- NON-CLAUDE distinct integration
- Postmerge production-path proof
- RIGHTS_V2_TERMINAL=true receipt
- CTC_HANDOFF_READY=true after terminal proof
