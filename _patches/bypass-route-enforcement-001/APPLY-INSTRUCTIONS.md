# Apply Instructions — Bypass Route Enforcement 001
**Target repo:** `Aperk357/Faceless-Video` head `e5d2c1a39ab9f01dc46b56484a54edb39f354f46`

## Prerequisites

1. Nightwatch lease `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904`
   must be ACTIVE before making any code changes. Run readback to confirm:
   ```bash
   python -m tools.writer_lease_fencing status \
     COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904
   ```

2. Verify Faceless-Video head matches `e5d2c1a39ab9f01dc46b56484a54edb39f354f46`
   (or rebase onto current main and re-read injection points).

## Step 1: shared/validation/schemas.ts

Add `rights_record: RightsAndConsentV2Schema` to these 5 schema objects.
`RightsAndConsentV2Schema` is already imported at the top of the file.

Add the field as the LAST field before `.strict()` in each schema:

- `batchExportSchema`: add `rights_record: RightsAndConsentV2Schema,`
- `publishJobSchema`: add `rights_record: RightsAndConsentV2Schema,`
- `videoFlowGenerateAndPublishSchema`: add `rights_record: RightsAndConsentV2Schema,`
- `videoEngineGenerateSchema`: add `rights_record: RightsAndConsentV2Schema,`
- `videoEngineBatchSchema`: add `rights_record: RightsAndConsentV2Schema,`

Do NOT touch `renderJobCreateSchema` — it already has `rights_record`.

## Step 2: server/routes/batchExport.ts

### Add import (near top, with other shared/contracts imports):
```typescript
import {
  RightsAndConsentV2Schema,
  evaluateRightsAndConsent,
  verifyJobRightsBinding,
} from "../../shared/contracts/reference_commerce.v2";
```

### Injection point: after quota check, before `planBatchExport(request)`

Insert the enforcement block (see `_handoff/2026-09-04-BYPASS-ROUTE-ENFORCEMENT-LEASE-AND-IMPLEMENTATION.md`
Part 3 for the full block). The `tenantId` and `userId` variables must already be
in scope from the auth middleware at this point.

## Step 3: server/routes/publish.ts

### Add import (same as Step 2)

### Injection point: after `isApprovedForRender` check succeeds, before `runAutoposterJob()`

Insert the enforcement block. `logAuditEvent` is already imported.

## Step 4: server/routes/video_flow.ts

### Add import (same as Step 2)

### Injection point: POST /generate_and_publish handler only
After `isApprovedForRender` gate succeeds, before `runAutoposterJob()`.

Do NOT add enforcement to POST /generate (generation-only, no publish).

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
### Injection point /batch: before `Promise.allSettled(jobs.map(...))` call

For /batch, check that `tenantId` and `userId` are accessible in that handler scope
before adding audit logging. If not available, add a note in the PR that audit logging
is omitted for /batch due to missing context (do NOT fabricate values).

## Step 6: Add integration test file

Copy `tests-integration-rights-enforcement-bypass-routes.ts` from this patch directory
to `tests/integration/rights-enforcement-bypass-routes.test.ts` in Faceless-Video.

Check that `tests/fixtures/rightsFixtures.ts` (or equivalent) exports `buildValidRightsRecord`
and `buildExpiredRightsRecord`. If it doesn't, add them following the same fixture
pattern used in `tests/integration/renderJobsRightsEnforcement.test.ts`.

## Step 7: Run CI locally

```bash
npx jest tests/integration/rights-enforcement-bypass-routes.test.ts
npx tsc --noEmit
```

Both must pass before committing.

## Step 8: Create draft PR

Branch name: `claude/rights-v2-bypass-route-enforcement-001`

PR description must include:
- Lease ID: `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904`
- Merge gate: "DO NOT MERGE until lease is confirmed ACTIVE in Nightwatch"
- Link to this hermes-agent commit for implementation specification
- 25 causal negatives table (5 routes × 5 tests)

## Step 9: Route to NON-CLAUDE review

The reviewer must NOT be a Claude subagent, relabeled or otherwise.
Exact-head review required at the PR head SHA.

## Step 10: After PASS_EXACT_HEAD review — Aperk357 merges

NO_SELF_MERGE — Claude must NOT merge this PR. Aperk357 holds merge authority.

## Step 11: Write Nightwatch postmerge checkpoint

After merge, write checkpoint in Nightwatch confirming:
- All 7 terminal gates CLOSED
- RIGHTS_V2_TERMINAL=true
- CTC_HANDOFF_READY=true
