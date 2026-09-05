# Apply Instructions — Bypass Route Enforcement 002
**Target repo:** `Aperk357/Faceless-Video`
**Required base:** fresh from Faceless-Video main (NOT inheriting -001 branch history)
**Lease:** `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-002-20260904`
**Owner authorization:** Aperk357 Nightwatch commit `e719f231` (2026-09-04T12:46:19Z)

## Prerequisites

1. Create branch `claude/rights-v2-bypass-route-enforcement-002` from current Faceless-Video
   main HEAD. Do NOT reuse or inherit from `-001` branch.

2. Confirm Nightwatch commit `e719f231` (Aperk357) exists and names this lease.

## Step 1: shared/validation/schemas.ts

Add 3 fields to each of the 6 listed schemas. `RightsAndConsentV2Schema` is already
imported from PR #65. Insert as the last fields before `.strict()`:

```
batchExportSchema:                add source_asset_id, source_checksum, rights_record
publishJobSchema:                 add source_asset_id, source_checksum, rights_record
videoFlowGenerateAndPublishSchema: add source_asset_id, source_checksum, rights_record
videoEngineGenerateSchema:        add source_asset_id, source_checksum, rights_record
videoEngineBatchSchema:           add source_asset_id, source_checksum, rights_record
facebookGenerateAndPublishSchema: add source_asset_id, source_checksum, rights_record
```

Zod types:
```typescript
source_asset_id: z.string(),
source_checksum: z.string(),
rights_record: RightsAndConsentV2Schema,
```

Do NOT touch `renderJobCreateSchema` — it already has `rights_record` from PR #65.

## Step 2: server/routes/batchExport.ts

### Add import:
```typescript
import {
  RightsAndConsentV2Schema,
  evaluateRightsAndConsent,
  verifyJobRightsBinding,
} from "../../shared/contracts/reference_commerce.v2";
```

### Injection point: after quota check, before `planBatchExport(request)`

Insert the standard enforcement block from the handoff spec (Part 4):
- Read `source_asset_id`, `source_checksum` from `req.body` (independent of rights_record)
- Parse rights_record → 400 on failure
- evaluateRightsAndConsent → 403 if ineligible
- verifyJobRightsBinding with body's source_asset_id/source_checksum → 403 if mismatch

## Step 3: server/routes/publish.ts

### Add import (same as Step 2)

### Injection point: after `isApprovedForRender` check succeeds, before `runAutoposterJob()`

Note: `tenantId = userId` — this route uses userId for both tenantId and userId fields
in logAuditEvent.

## Step 4: server/routes/video_flow.ts

### Add import (same as Step 2)

### Injection point: POST /generate_and_publish handler ONLY

After `isApprovedForRender` gate succeeds, before `runAutoposterJob()`.

Do NOT add enforcement to POST /generate (generation-only, no publication).

## Step 5: server/routes/videoEngine.ts

### Add imports:
```typescript
import {
  RightsAndConsentV2Schema,
  evaluateRightsAndConsent,
  verifyJobRightsBinding,
} from "../../shared/contracts/reference_commerce.v2";
import { logAuditEvent } from "../services/auditService";
```

### Injection point /generate: before `submitJob()` call
Use variable name `rightsRecordGenerate` to avoid const redeclaration conflict.

### Injection point /batch: before `Promise.allSettled(jobs.map(...))` call
Use variable name `rightsRecordBatch`.

## Step 6: server/routes/facebook.ts

### Add import (same as Step 2)

### Injection point: POST /api/v1/facebook/generate_and_publish
After platform credential validation, before `runAutoposterJob()`.

## Step 7: server/routes/renderJobs.ts — dead-letter retry

This route is UNCHANGED from the 001 spec. The dead-letter retry re-reads stored
`job.rightsRecord` from the DB (does NOT use independent source_asset_id from body —
`emptyBodySchema` applies). Use the same enforcement block from:
`_handoff/2026-09-04-BYPASS-ROUTE-ENFORCEMENT-LEASE-AND-IMPLEMENTATION.md` Part 3.

No new imports needed — `RightsAndConsentV2Schema` and `evaluateRightsAndConsent` are
already in `renderJobs.ts` from PR #65.

## Step 8: Add new integration test file

Copy `tests-integration-rights-enforcement-bypass-routes.ts` from this patch directory
to `tests/integration/rights-enforcement-bypass-routes.test.ts` in Faceless-Video.

This file has 35 tests (5 × 7 routes). N4 tests prove genuine non-circular binding:
`source_asset_id: MISMATCH_ASSET_ID` in the request body (different from `"asset-test-123"`
in the rights_record) → 403 JOB_ASSET_ID_MISMATCH.

## Step 9: Update 7 existing fixture test files

See handoff spec Part 6 for per-file changes. All 7 files need `VALID_RIGHTS_RECORD`
added plus `source_asset_id: "asset-test-123"` and `source_checksum: "a".repeat(64)`
in their base request bodies. The render-jobs tests are the exception — they do NOT
need independent source fields (renderJobCreateSchema pattern is unchanged).

## Step 10: Run CI locally

```bash
npx vitest run tests/integration/rights-enforcement-bypass-routes.test.ts
npx vitest run tests/integration/publishApprovalGate.test.ts
npx vitest run tests/integration/publishRouteContract.test.ts
npx vitest run tests/integration/publishSafetyGateScope.test.ts
npx vitest run tests/integration/renderJobsRightsEnforcement.test.ts
npx vitest run tests/integration/renderJobsIdempotency.test.ts
npx vitest run tests/integration/renderJobsDeadLetter.test.ts
npx vitest run tests/integration/videoFlowApprovalGate.test.ts
npx tsc --noEmit
```

All must pass before committing.

## Step 11: Create draft PR

Branch: `claude/rights-v2-bypass-route-enforcement-002`
Base: Faceless-Video main

PR description must include:
- Lease ID: `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-002-20260904`
- Owner authorization: Nightwatch commit `e719f231` by Aperk357
- Merge gate: "DO NOT MERGE until PASS_EXACT_HEAD from independent non-Claude reviewer"
- Summary of 35 causal negatives (7 routes × 5 tests)
- Reference to this hermes-agent session for implementation specification

## Step 12: Route to NON-CLAUDE independent review

The reviewer MUST NOT be a Claude subagent (relabeled or otherwise).
Exact-head review required at the PR head SHA.
PASS_EXACT_HEAD is required before merge.

## Step 13: After PASS_EXACT_HEAD review — Aperk357 merges

NO_SELF_MERGE — Claude must NOT merge this PR. Aperk357 holds merge authority.

## Step 14: Write Nightwatch postmerge checkpoint

After merge:
- Confirm all 7 terminal gates CLOSED
- Set `RIGHTS_V2_TERMINAL=true`
- Set `CTC_HANDOFF_READY=true`
- Mark lease `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-002-20260904` RELEASED
