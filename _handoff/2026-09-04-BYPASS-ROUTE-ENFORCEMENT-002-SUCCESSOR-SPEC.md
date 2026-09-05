# Bypass Route Enforcement — Successor Lease 002 Research Packet + Implementation Spec
**Date:** 2026-09-04
**Workstream:** FACELESS_RIGHTS_V2_TO_TERMINAL_AND_CTC_HANDOFF_V1
**Sub-mission:** FACELESS_RIGHTS_V2_LAWFUL_SUCCESSOR_V1
**Session:** session_01VPh5iq3fdMfKrFjiAjFYKK
**Target repo:** `Aperk357/Faceless-Video`
**Governance repo:** `Aperk357/Nightwatch`
**Supersedes:** `_handoff/2026-09-04-BYPASS-ROUTE-ENFORCEMENT-LEASE-AND-IMPLEMENTATION.md` (001)

---

## Why a successor?

Lease 001 (`COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904`) and its
corresponding branch `claude/rights-v2-bypass-route-enforcement-001` had an authorization
gap: the implementation spec was assembled under an unconfirmed lease prior to owner
issuance. Lease 002 begins from an explicit owner-authorized commitment recorded in
Nightwatch at commit `e719f231` (Aperk357, 2026-09-04T12:46:19Z) before any code is
written, satisfying NO_RETROACTIVE_AUTHORITY.

Additionally, the 001 implementation had a circular binding defect: `verifyJobRightsBinding`
was called with `source_asset_id` and `source_checksum` extracted from inside the same
`rights_record` being validated — tautological. Lease 002 corrects this by requiring
independent `source_asset_id` and `source_checksum` fields in every request body so the
server compares a caller-supplied asset identity against the rights record.

---

## Part 1: Nightwatch Lease Record

### Owner authorization

Aperk357 commit `e719f231` to Nightwatch (2026-09-04T12:46:19Z) authorizes:

| Field | Value |
|---|---|
| Lease ID | `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-002-20260904` |
| Writer identity | Claude Code / hermes-agent session 8a81700b |
| Target repo | `Aperk357/Faceless-Video` |
| Target branch | `claude/rights-v2-bypass-route-enforcement-002` |
| Bounded scope (files) | 15 (see below) |
| Expiry | `2026-09-04T21:40:00Z` |
| Mutation gate | NON-CIRCULAR binding enforcement required |

### Bounded scope — 15 files

```
server/routes/batchExport.ts
server/routes/publish.ts
server/routes/video_flow.ts
server/routes/videoEngine.ts
server/routes/renderJobs.ts
server/routes/facebook.ts                               (new — not in 001)
shared/validation/schemas.ts
tests/integration/rights-enforcement-bypass-routes.test.ts   (new file, 35 tests)
tests/integration/publishApprovalGate.test.ts           (fixture update)
tests/integration/publishRouteContract.test.ts          (fixture update)
tests/integration/publishSafetyGateScope.test.ts        (fixture update)
tests/integration/renderJobsRightsEnforcement.test.ts   (fixture update)
tests/integration/renderJobsIdempotency.test.ts         (fixture update)
tests/integration/renderJobsDeadLetter.test.ts          (fixture update)
tests/integration/videoFlowApprovalGate.test.ts         (fixture update)
```

### Branch requirement

Branch `claude/rights-v2-bypass-route-enforcement-002` MUST be created fresh from
Faceless-Video main `e5d2c1a39ab9f01dc46b56484a54edb39f354f46` (or current head at time
of pickup). It MUST NOT inherit history from
`claude/rights-v2-bypass-route-enforcement-001`.

---

## Part 2: Core design change — non-circular binding

### 001 defect

```typescript
// DEFECT: jobView fields come from the SAME rights_record being validated
const jobView = {
  source_asset_id: rights.source_asset_id,    // tautological
  source_checksum: rights.source_checksum,     // tautological
  rights_state: rights.source_authority.state,
};
const bindingResult = verifyJobRightsBinding(jobView, rights);
```

A caller could submit any `source_asset_id` inside the `rights_record` and it would
always match itself. `verifyJobRightsBinding` can never return `JOB_ASSET_ID_MISMATCH`
under this pattern.

### 002 fix

Each request schema adds independent `source_asset_id: z.string()` and
`source_checksum: z.string()` fields at the top level of the request body (outside
`rights_record`). The enforcement block reads these from `req.body`:

```typescript
const { source_asset_id, source_checksum, rights_record } = req.body;
// ... parse and evaluate rights_record ...
const jobView = {
  source_asset_id,   // from request body — caller asserts which asset is being processed
  source_checksum,   // from request body — caller asserts what they have
  rights_state: rights.source_authority.state,
};
const bindingResult = verifyJobRightsBinding(jobView, rights);
// bindingResult.errors may include: JOB_ASSET_ID_MISMATCH, JOB_ASSET_CHECKSUM_MISMATCH
```

If `source_asset_id` in the body differs from `rights.source_asset_id`, the server
returns 403 `JOB_ASSET_ID_MISMATCH`. This is a genuine causal negative — proven by N4
tests across all 7 routes.

---

## Part 3: Schema changes (shared/validation/schemas.ts)

### New fields required in 6 schemas

All 6 publication schemas must add `source_asset_id` and `source_checksum` alongside
`rights_record`. `renderJobCreateSchema` is NOT in this list because the render-jobs
route already required `rights_record` in PR #65 and the dead-letter retry uses stored
values (no independent binding needed there — see Part 5).

**batchExportSchema** — add 3 fields:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

**publishJobSchema** — add 3 fields:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

**videoFlowGenerateAndPublishSchema** — add 3 fields:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

**videoEngineGenerateSchema** — add 3 fields:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

**videoEngineBatchSchema** — add 3 fields:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

**facebookGenerateAndPublishSchema** (NEW schema update, not in 001) — add 3 fields:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

Note: `RightsAndConsentV2Schema` must be imported at the top of schemas.ts if not
already present. It is already present from PR #65.

---

## Part 4: Route handler enforcement pattern (all 6 publication routes)

### Required import (add to each route file that lacks it)

```typescript
import {
  RightsAndConsentV2Schema,
  evaluateRightsAndConsent,
  verifyJobRightsBinding,
} from "../../shared/contracts/reference_commerce.v2";
```

For `videoEngine.ts`, also add:
```typescript
import { logAuditEvent } from "../services/auditService";
```

### Enforcement block (standard pattern — 6 publication routes)

Insert after the existing auth/approval gate, before the action call. Use the route's
own `tenantId` and `userId` variable names.

```typescript
const { source_asset_id, source_checksum, rights_record } = req.body;
const rightsParseResult = RightsAndConsentV2Schema.safeParse(rights_record);
if (!rightsParseResult.success) {
  await logAuditEvent({
    tenantId,
    userId,
    action: "render.denied_rights_malformed",
    resourceType: "render_job",
    details: { errors: rightsParseResult.error.flatten() },
    success: false,
  });
  return res.status(400).json({
    error: "Rights record is missing or malformed.",
    details: rightsParseResult.error.flatten(),
  });
}
const rights = rightsParseResult.data;
const { evaluated_at: _evalAt, publication_eligible: _pe, ineligibility_reasons: _ir, ...rightsInput } = rights;
const freshEval = evaluateRightsAndConsent(rightsInput, new Date());
if (!freshEval.publication_eligible) {
  await logAuditEvent({
    tenantId,
    userId,
    action: "render.denied_rights_ineligible",
    resourceType: "render_job",
    details: { ineligibility_reasons: freshEval.ineligibility_reasons },
    success: false,
  });
  return res.status(403).json({
    error: "Rights record is not eligible for publication.",
    ineligibility_reasons: freshEval.ineligibility_reasons,
  });
}
const jobView = {
  source_asset_id,
  source_checksum,
  rights_state: rights.source_authority.state,
};
const bindingResult = verifyJobRightsBinding(jobView, rights);
if (!bindingResult.valid) {
  await logAuditEvent({
    tenantId,
    userId,
    action: "render.denied_rights_binding",
    resourceType: "render_job",
    details: { binding_errors: bindingResult.errors },
    success: false,
  });
  return res.status(403).json({
    error: "Rights record failed job binding verification.",
    binding_errors: bindingResult.errors,
  });
}
```

### Route-specific injection points

| Route | File | Injection point |
|---|---|---|
| POST /api/batch-export | `server/routes/batchExport.ts` | After quota check, before `planBatchExport(request)` |
| POST /api/v1/publish | `server/routes/publish.ts` | After `isApprovedForRender` gate, before `runAutoposterJob()` |
| POST /api/v1/video/generate_and_publish | `server/routes/video_flow.ts` | After `isApprovedForRender` gate, before `runAutoposterJob()`. Do NOT add to POST /generate. |
| POST /api/video-engine/generate | `server/routes/videoEngine.ts` | Before `submitJob()` call. Use distinct variable `rightsRecordGenerate`. |
| POST /api/video-engine/batch | `server/routes/videoEngine.ts` | Before `Promise.allSettled(jobs.map(...))`. Use `rightsRecordBatch`. |
| POST /api/v1/facebook/generate_and_publish | `server/routes/facebook.ts` | After platform credential validation, before `runAutoposterJob()`. |

Note for `publish.ts`: `tenantId = userId` — the publish route uses `userId` for both
fields. This is the correct mapping for this route (userId is the tenant scoping unit).

Note for `videoEngine.ts`: Use distinct variable names (`rightsRecordGenerate` for the
generate handler and `rightsRecordBatch` for the batch handler) to avoid `const`
redeclaration conflicts when both handlers are in the same module scope.

---

## Part 5: renderJobs.ts dead-letter retry (unchanged from 001)

The dead-letter retry enforcement pattern from 001 remains correct. It does NOT need
independent `source_asset_id`/`source_checksum` because:
- The retry uses `emptyBodySchema` (no request body fields)
- It re-reads `job.rightsRecord` from the DB record
- Comparing stored rights against themselves is not circular here — the point is
  temporal re-evaluation at retry time, not asset identity binding

The 001 spec (Part 3, renderJobs section) applies unchanged. No new changes needed to
`renderJobs.ts` beyond what was already specified in 001.

---

## Part 6: fixture test updates (7 files)

All 7 existing fixture test files need their `BASE_BODY` / `WELL_FORMED` / `validBody`
constants updated to include the new required fields. Without these updates, existing
tests will fail schema validation on the 6 routes that now require `source_asset_id`
and `source_checksum`.

The shared additions for all affected tests:
```typescript
const VALID_RIGHTS_RECORD = {
  contract_version: "2.0.0",
  source_asset_id: "asset-test-123",
  source_checksum: "a".repeat(64),
  source_authority: {
    state: "VERIFIED",
    evidence_refs: ["ev-001"],
    verified_by: "test-verifier",
    verified_at: "2025-01-01T00:00:00.000Z",
  },
  human_identity_used: false,
  voice_identity_used: false,
  likeness_consent: { state: "NOT_APPLICABLE", reason: "human identity not used" },
  voice_consent: { state: "NOT_APPLICABLE", reason: "voice identity not used" },
  product_trademark_authority: {
    state: "VERIFIED",
    evidence_refs: ["ev-001"],
    verified_by: "test-verifier",
    verified_at: "2025-01-01T00:00:00.000Z",
  },
  territory: ["US"],
  purpose: ["commercial"],
  intended_publication: { territory: "US", purpose: "commercial" },
  expiry: "2030-01-01T00:00:00.000Z",
  revocation: "NOT_REVOKED",
  evaluated_at: "2025-01-01T00:00:00.000Z",
  publication_eligible: true,
  ineligibility_reasons: [],
};
```

### Per-file changes

**tests/integration/publishApprovalGate.test.ts**
Add to `BASE_BODY`:
```typescript
source_asset_id: "asset-test-123",
source_checksum: "a".repeat(64),
rights_record: VALID_RIGHTS_RECORD,
```

**tests/integration/publishRouteContract.test.ts**
Add to `WELL_FORMED`:
```typescript
source_asset_id: "asset-test-123",
source_checksum: "a".repeat(64),
rights_record: VALID_RIGHTS_RECORD,
```

**tests/integration/publishSafetyGateScope.test.ts**
Add to `MULTI_PLATFORM_BODY`:
```typescript
source_asset_id: "asset-test-123",
source_checksum: "a".repeat(64),
rights_record: VALID_RIGHTS_RECORD,
```

**tests/integration/renderJobsRightsEnforcement.test.ts**
Update to use `eligibleRights()` builder. Add `validRightsRecord` constant.
`baseBody` keeps existing `mode: "HUMO"`, `script: "Test script."` — renderJobCreateSchema
does NOT require `source_asset_id`/`source_checksum` at body level.

**tests/integration/renderJobsIdempotency.test.ts**
Add `validRightsRecord` constant. Update `validBody` to include:
```typescript
rights_record: validRightsRecord,
```
(renderJobCreateSchema already required `rights_record` from PR #65)

**tests/integration/renderJobsDeadLetter.test.ts**
Add `VALID_RIGHTS_RECORD` constant. Update `seedDeadLetterJob` call:
```typescript
await seedDeadLetterJob({ rightsRecord: VALID_RIGHTS_RECORD });
```

**tests/integration/videoFlowApprovalGate.test.ts**
Add to `BASE_BODY`:
```typescript
source_asset_id: "asset-test-123",
source_checksum: "a".repeat(64),
rights_record: VALID_RIGHTS_RECORD,
```

---

## Part 7: Merge gates (same as 001, updated for 002)

The bypass-route enforcement PR MUST NOT be merged until:
1. Branch `claude/rights-v2-bypass-route-enforcement-002` is created fresh from
   Faceless-Video main (NOT inheriting -001 history)
2. All 15 files committed in one atomic commit referencing lease
   `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-002-20260904`
3. CI: all 35 integration tests pass + existing fixture tests pass
4. NON-CLAUDE independent adversarial reviewer provides PASS_EXACT_HEAD at PR head SHA
   (GPT, human, or other non-Claude-subagent reviewer)
5. NO_SELF_MERGE unconditional — Aperk357 or designated non-Claude integrator merges

---

## Part 8: Postmerge Nightwatch checkpoint

After merge, write to Nightwatch:
- Terminal receipt: `RIGHTS_V2_TERMINAL=true`
- Handoff ready: `CTC_HANDOFF_READY=true`
- All 7 terminal gates CLOSED
- Lease `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-002-20260904` → RELEASED

---

## Part 9: Terminal gates status (as of 2026-09-04, pre-002-merge)

| Gate | Status | Evidence |
|---|---|---|
| (1) Contract enforcement correct | DONE | PR #65 merged, evaluateRightsAndConsent re-derives at server time |
| (2) Production path invokes it | PARTIAL | POST /render-jobs ENFORCED; 6 bypass routes OPEN |
| (3) API/UI cannot bypass | OPEN | batchExport/publish/video_flow/videoEngine/facebook unenforced |
| (4) Negative controls fail-closed | PARTIAL | 10 negatives proven for /render-jobs; bypass routes pending 35 more |
| (5) Exact-head independent review passes | PENDING | Awaiting 002 PR at PASS_EXACT_HEAD |
| (6) Merge+postmerge proof complete | PARTIAL | PR #65 merged; bypass PR 002 pending |
| (7) Nightwatch receipt records terminal state | OPEN | Requires all above gates |

`RIGHTS_V2_TERMINAL=false` — Gates 2, 3, 4, 5, 6, 7 remain open.
`BLOCKED_RIGHTS_REMAINS=true` — preserved until all production gaps closed.
