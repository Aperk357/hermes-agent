# Bypass Route Enforcement — Lease Research Packet + Implementation Specification
**Date:** 2026-09-04
**Workstream:** FACELESS_RIGHTS_V2_TO_TERMINAL_AND_CTC_HANDOFF_V1
**Session:** session_01VPh5iq3fdMfKrFjiAjFYKK
**Target repo:** `Aperk357/Faceless-Video`
**Governance repo:** `Aperk357/Nightwatch`
**Nightwatch head at research:** `949ae4c484946317fb4c27d04e13d516c00d3279`
**Faceless-Video head at research:** `e5d2c1a39ab9f01dc46b56484a54edb39f354f46`
**Correction (2026-09-04, same session):** `localRender.ts` confirmed NOT a bypass route
(local preview/download, no publication action). Dead-letter retry in `renderJobs.ts`
(line 481, admin-gated) IS a real bypass — added to scope and spec.

---

## Purpose

This document is the Nightwatch lease research packet for the new bounded lease required
to implement `RightsAndConsentV2` enforcement on the five proven bypass routes in
`Aperk357/Faceless-Video`. It also contains the complete implementation specification
(exact injection points, code, and test plan) ready for pickup by host-lane (gh/Codex)
or after push-access grant.

This session (hermes-agent, Claude Code remote) cannot push directly to Faceless-Video or
Nightwatch — session is scoped to `Aperk357/hermes-agent` write access only. All
implementation artifacts are committed here for pickup.

---

## Part 1: Nightwatch Lease Research Packet

### Lease parameters

| Field | Value |
|---|---|
| Lease ID | `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904` |
| Lane ID | `FACELESS-VIDEO-RIGHTS-V2-BYPASS-ROUTE-ENFORCEMENT-001` |
| Holder | `hermes-agent` (Claude Code remote session) |
| Target repo | `Aperk357/Faceless-Video` |
| Failure domain | `faceless-video-server-routes-rights-v2-enforcement` |
| TTL | 28800 seconds (8 hours) from grant time |
| Forward-only | YES |
| NO_RETROACTIVE_AUTHORITY | unconditional |

### Bounded scope (files authorized for change)

```
shared/validation/schemas.ts
server/routes/batchExport.ts
server/routes/publish.ts
server/routes/video_flow.ts
server/routes/videoEngine.ts
server/routes/renderJobs.ts
tests/integration/rights-enforcement-bypass-routes.test.ts (new file)
```

Note: `server/routes/localRender.ts` is EXCLUDED — confirmed local preview/download only
(`startLocalRender()`, no publication action). NOT a bypass route.

### Collision check

- Prior lease `COS-LEASE-FACELESS-RIGHTS-CONSENT-V2-002-20260903`: **RELEASED** per
  `Aperk357/Nightwatch` checkpoint `NW-CHK-0212` (SHA `c4d6d4d5db07ad1612ad52040b91a70323aef6db`):
  "COS-LEASE-FACELESS-RIGHTS-CONSENT-V2-002-20260903 → RELEASED"
- Collision check result: **CLEAR** — no active writers on failure domain
  `faceless-video-server-routes-rights-v2-enforcement`

### Standing authority

`patterns/COS-OPERATING-CONTRACT.md` (SHA `857bc7d67ed255eb4e7f06bfae67655676382c8d`)
governs this case. Key passage:

> "Everything else is CoS's to research, diagnose, repair, prove, or advance under
> standing bounded-lease authority, without a fresh owner prompt."

Implementing rights enforcement on bypass routes is NOT in the owner-gate enumeration.
Owner gates are: credentials/secrets disclosure, fund movement/payment authorization,
legal/certification acceptance, irreversible destructive action, owner-reserved production
action, genuine business/product choice after options reduced.

### Nightwatch grant command

```bash
python -m tools.writer_lease_fencing grant \
  COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904 \
  --holder hermes-agent \
  --target-repo Aperk357/Faceless-Video \
  --scope server/routes/batchExport.ts,server/routes/publish.ts,server/routes/video_flow.ts,server/routes/videoEngine.ts,server/routes/renderJobs.ts,shared/validation/schemas.ts,tests/integration/rights-enforcement-bypass-routes.test.ts \
  --lane-id FACELESS-VIDEO-RIGHTS-V2-BYPASS-ROUTE-ENFORCEMENT-001 \
  --failure-domain faceless-video-server-routes-rights-v2-enforcement \
  --ttl-seconds 28800
```

### Lease readback (required before implementation begins)

```bash
python -m tools.writer_lease_fencing status \
  COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904
```

Expected: `state=ACTIVE`, `holder=hermes-agent`, scope matches above.

---

## Part 2: Bypass Route Bypass Matrix

| Route | File | Injection point | logAuditEvent available |
|---|---|---|---|
| POST /api/batch-export | `server/routes/batchExport.ts` | After quota check, before `planBatchExport(request)` | YES (import already present) |
| POST /api/v1/publish | `server/routes/publish.ts` | After `isApprovedForRender` gate, before `runAutoposterJob()` | YES |
| POST /api/v1/video/generate_and_publish | `server/routes/video_flow.ts` | After `isApprovedForRender` gate, before `runAutoposterJob()` | YES |
| POST /api/video-engine/generate | `server/routes/videoEngine.ts` | Before `submitJob()` call | NO (must add import) |
| POST /api/video-engine/batch | `server/routes/videoEngine.ts` | Before `Promise.allSettled(...)` call | NO (must add import) |
| POST /render-jobs/:jobId/dead-letter/retry | `server/routes/renderJobs.ts` line 481 | Before `retryDeadLetterJob(jobId)` — re-eval stored `job.rightsRecord` | YES (already imported) |

Notes:
- `POST /api/v1/video/generate` (generation-only, no publish) does NOT need rights
  enforcement — it does not publish. Only `/generate_and_publish` is in scope.
- `server/routes/localRender.ts` is NOT a bypass route — confirmed local preview/download
  only via `startLocalRender()`. No publication action. OUT OF SCOPE.
- Dead-letter retry is admin-gated (`requireAdmin`). The bypass is: rights valid at job
  creation time may have expired or been revoked by retry time. Fix: re-read
  `job.rightsRecord` from DB, re-evaluate `evaluateRightsAndConsent(rightsInput, new Date())`,
  fail-closed if ineligible. If `job.rightsRecord` is null (pre-enforcement job), fail-closed
  and require re-submission via POST /render-jobs.

---

## Part 3: Implementation Specification

### Enforcement pattern (from renderJobs.ts reference)

```typescript
// Injection: after existing auth/approval gate, before action call
const { rights_record } = req.body;
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
  source_asset_id: rights.source_asset_id,
  source_checksum: rights.source_checksum,
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

### Required import (add to each route file that lacks it)

```typescript
import {
  RightsAndConsentV2Schema,
  evaluateRightsAndConsent,
  verifyJobRightsBinding,
} from "../../shared/contracts/reference_commerce.v2";
```

For `videoEngine.ts`, also add `logAuditEvent` import:

```typescript
import { logAuditEvent } from "../services/auditService";
```

### schemas.ts changes (5 schemas, add `rights_record: RightsAndConsentV2Schema`)

Each schema below needs one line added (shown with comment):

**batchExportSchema**:
```typescript
export const batchExportSchema = z.object({
  projectId: z.union([z.string(), z.number()]),
  aspects: z.array(z.string().max(20)).max(20).optional(),
  formats: z.array(z.string().max(20)).max(20).optional(),
  priority: z.union([z.string(), z.number()]).optional(),
  rights_record: RightsAndConsentV2Schema,  // ADD THIS LINE
}).strict();
```

**publishJobSchema**:
```typescript
export const publishJobSchema = z.object({
  // ... existing fields ...
  rights_record: RightsAndConsentV2Schema,  // ADD THIS LINE
}).strict();
```

**videoFlowGenerateAndPublishSchema**:
```typescript
export const videoFlowGenerateAndPublishSchema = z.object({
  // ... existing fields ...
  rights_record: RightsAndConsentV2Schema,  // ADD THIS LINE
}).strict();
```

**videoEngineGenerateSchema**:
```typescript
export const videoEngineGenerateSchema = z.object({
  // ... existing fields ...
  rights_record: RightsAndConsentV2Schema,  // ADD THIS LINE
}).strict();
```

**videoEngineBatchSchema**:
```typescript
export const videoEngineBatchSchema = z.object({
  // ... existing fields ...
  rights_record: RightsAndConsentV2Schema,  // ADD THIS LINE
}).strict();
```

### renderJobs.ts dead-letter retry enforcement (different pattern — re-reads stored rights)

The dead-letter retry does not receive `rights_record` in the request body (it uses
`emptyBodySchema`). It must re-read the stored rights from the job record and re-evaluate.

Injection point: immediately after the `job.status !== "dead_letter"` guard, before
`retryDeadLetterJob(jobId)`:

```typescript
// Re-evaluate stored rights before allowing dead-letter retry
if (!job.rightsRecord) {
  await logAuditEvent({
    tenantId: job.tenantId,
    userId: adminUserId,
    action: "render.denied_rights_malformed",
    resourceType: "render_job",
    resourceId: jobId,
    details: { reason: "No rights record stored — job predates rights enforcement. Re-submit via POST /render-jobs." },
    success: false,
  });
  return res.status(403).json({
    error: "Job has no stored rights record. Re-submit via POST /render-jobs with a valid rights_record.",
  });
}
const rightsParseResult = RightsAndConsentV2Schema.safeParse(job.rightsRecord);
if (!rightsParseResult.success) {
  await logAuditEvent({
    tenantId: job.tenantId,
    userId: adminUserId,
    action: "render.denied_rights_malformed",
    resourceType: "render_job",
    resourceId: jobId,
    details: { errors: rightsParseResult.error.flatten() },
    success: false,
  });
  return res.status(400).json({
    error: "Stored rights record is malformed.",
    details: rightsParseResult.error.flatten(),
  });
}
const storedRights = rightsParseResult.data;
const { evaluated_at: _evalAt, publication_eligible: _pe, ineligibility_reasons: _ir, ...storedRightsInput } = storedRights;
const freshEval = evaluateRightsAndConsent(storedRightsInput, new Date());
if (!freshEval.publication_eligible) {
  await logAuditEvent({
    tenantId: job.tenantId,
    userId: adminUserId,
    action: "render.denied_rights_ineligible",
    resourceType: "render_job",
    resourceId: jobId,
    details: { ineligibility_reasons: freshEval.ineligibility_reasons },
    success: false,
  });
  return res.status(403).json({
    error: "Stored rights record is no longer eligible for publication.",
    ineligibility_reasons: freshEval.ineligibility_reasons,
  });
}
// Rights re-evaluated at retry time — proceed
```

Note: `RightsAndConsentV2Schema`, `evaluateRightsAndConsent` are already imported in
`renderJobs.ts` (added by PR #65). No new imports needed for this fix.

### videoEngine.ts note on logAuditEvent

`server/routes/videoEngine.ts` does NOT currently import `logAuditEvent`. Two options:
1. Add the import and use the same audit logging pattern as renderJobs.ts (preferred — consistency)
2. Omit audit logging for videoEngine, accept the audit gap

Option 1 is preferred. Add to imports:
```typescript
import { logAuditEvent } from "../services/auditService";
```

The `tenantId` and `userId` context variables must be available in scope (check if videoEngine.ts
uses the same auth middleware pattern as other routes). If they are not available, they can be
extracted from `req.user` (same pattern as other routes).

---

## Part 4: Integration Test Specification

File: `tests/integration/rights-enforcement-bypass-routes.test.ts`

See `_patches/bypass-route-enforcement-001/tests-integration-rights-enforcement-bypass-routes.ts`
for the full test file content.

### Required causal negatives per route

Each of the 4 routes (batchExport, publish, video_flow/generate_and_publish, videoEngine/generate,
videoEngine/batch) must prove:

| Test | Expected |
|---|---|
| POSITIVE: valid eligible record | 201 / 200 (route proceeds) |
| NEGATIVE: missing rights_record | 400 |
| NEGATIVE: malformed rights_record (not object) | 400 |
| NEGATIVE: ineligible at server time (expired) | 403 |
| NEGATIVE: binding mismatch (asset_id mismatch) | 403 |

That is 5 tests × 5 routes = 25 required causal negatives.

---

## Part 5: PR merge gate

The bypass-route enforcement PR MUST NOT be merged until:
1. Nightwatch readback confirms lease `COS-LEASE-FACELESS-VIDEO-BYPASS-ROUTE-ENFORCEMENT-001-20260904`
   is `state=ACTIVE`
2. All 25 causal negatives pass in CI
3. NON-CLAUDE independent adversarial reviewer provides PASS_EXACT_HEAD
4. Aperk357 (or designated non-Claude integrator) merges — NO_SELF_MERGE unconditional

---

## Part 6: Host-lane pickup instructions

If Aperk357 implements this via host lane (gh/Codex) rather than granting push access:

1. Run the Nightwatch grant command (Part 1 above)
2. Confirm readback shows `state=ACTIVE`
3. Apply changes to exactly the 6 files listed in bounded scope
4. Use exactly the enforcement pattern from Part 3
5. Create draft PR with merge gate note in description
6. Route to NON-CLAUDE independent review
7. After PASS_EXACT_HEAD review: Aperk357 merges
8. Write Nightwatch postmerge checkpoint confirming all 7 terminal gates
9. Update `RIGHTS_V2_TERMINAL=true` in Nightwatch writer-lease-registry
10. Set `CTC_HANDOFF_READY=true`

---

## Part 7: Terminal gates status (as of 2026-09-04)

| Gate | Status | Evidence |
|---|---|---|
| (1) Contract enforcement correct | DONE | PR #65 merged, evaluateRightsAndConsent re-derives at server time |
| (2) Production path invokes it | PARTIAL | POST /render-jobs ENFORCED; 4 bypass routes OPEN |
| (3) API/UI cannot bypass | OPEN | batchExport/publish/video_flow/videoEngine unenforced |
| (4) Negative controls fail-closed | PARTIAL | 10 negatives proven for /render-jobs; bypass routes pending |
| (5) Exact-head independent review passes | DONE | GPT-5.6 Sol PASS_WITH_NOTES at hermes-agent 3b10bb66 (2026-09-04T03:49:56Z) |
| (6) Merge+postmerge proof complete | PARTIAL | PR #65 merged (2ff27e99); bypass PR pending |
| (7) Nightwatch receipt records terminal state | OPEN | Requires all above gates |

`RIGHTS_V2_TERMINAL=false` — Gates 2, 3, 4 (bypass routes), 6 (bypass PR), 7 remain open.
