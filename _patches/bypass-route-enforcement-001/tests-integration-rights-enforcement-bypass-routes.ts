/**
 * Integration tests: RightsAndConsentV2 enforcement on bypass routes
 *
 * Proves 30 causal negatives (5 tests × 5 publication routes + 5 admin dead-letter retry).
 * Routes under test:
 *   POST /api/batch-export          (batchExport.ts)
 *   POST /api/v1/publish            (publish.ts)
 *   POST /api/v1/video/generate_and_publish  (video_flow.ts)
 *   POST /api/video-engine/generate (videoEngine.ts)
 *   POST /api/video-engine/batch    (videoEngine.ts)
 *   POST /api/render-jobs/:jobId/dead-letter/retry  (renderJobs.ts, admin-gated)
 *
 * Pattern mirrors tests/integration/renderJobsRightsEnforcement.test.ts.
 * Uses Vitest + vi.mock(); no external fixture files.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import express, { type Express, type NextFunction, type Response } from "express";
import request from "supertest";

// ── Shared mock: auth always passes ───────────────────────────────────────────

vi.mock("../../server/replit_integrations/auth/replitAuth", () => ({
  isAuthenticated: (req: any, _res: Response, next: NextFunction) => {
    req.user = { claims: { sub: "rights-test-user", role: "admin" } };
    next();
  },
  requireAdmin: (req: any, _res: Response, next: NextFunction) => next(),
}));

// ── Shared mock: approval always passes ──────────────────────────────────────

vi.mock("../../server/services/approvalService", () => ({
  syncApprovalWithProjectContent: async () => ({
    status: "approved_for_render",
    version: 1,
    approvedVersion: 1,
    contentFingerprint: "fp",
    approvedContentFingerprint: "fp",
  }),
  isApprovedForRender: () => true,
  getApproval: async () => ({ status: "approved_for_render" }),
}));

// ── Shared mock: audit logs are no-ops ────────────────────────────────────────

vi.mock("../../server/services/auditService", () => ({
  logAuditEvent: async () => undefined,
}));

// ── Shared mock: quota always allows ─────────────────────────────────────────

vi.mock("../../server/services/quotaService", () => ({
  checkRenderQuota: async () => ({ allowed: true, quotaInfo: {} }),
  consumeRenderQuota: async () => undefined,
  releaseRenderSlot: async () => undefined,
  checkBatchQuota: async () => ({ allowed: true }),
}));

// ── Shared mock: rate limit always passes ─────────────────────────────────────

vi.mock("../../server/middleware/accessControl", () => ({
  rateLimit: () => (_req: any, _res: Response, next: NextFunction) => next(),
}));

// ── Shared mock: kill switch always allows ────────────────────────────────────

vi.mock("../../server/services/killSwitchService", () => ({
  isRenderAllowed: async () => ({ allowed: true }),
  getKillSwitchState: async () => ({ renderDisabled: false }),
}));

// ── Shared mock: webhook no-op ────────────────────────────────────────────────

vi.mock("../../server/services/webhookService", () => ({
  emitWebhookEvent: async () => undefined,
  startWebhookProcessor: () => undefined,
}));

// ── DB mock state (used by dead-letter retry tests) ────────────────────────────

let mockJobRecord: any = null;

vi.mock("../../server/db", () => ({
  db: {
    select: () => ({
      from: () => ({
        where: () => ({
          limit: () => Promise.resolve(mockJobRecord ? [mockJobRecord] : []),
        }),
      }),
    }),
    update: () => ({
      set: () => ({
        where: () => Promise.resolve(),
      }),
    }),
    insert: () => ({
      values: (v: any) => ({
        returning: () => Promise.resolve([{ ...v, id: 1 }]),
      }),
    }),
  },
  pool: {},
}));

// ── Job queue mocks ────────────────────────────────────────────────────────────

vi.mock("../../server/services/jobQueue", () => ({
  generateJobId: () => "job-test-id",
  signJobToken: () => "test-token",
  enqueueRenderJob: async () => ({ success: true, queuePosition: 1 }),
  getJobStatus: async () => null,
  retryDeadLetterJob: async () => ({ success: true }),
  submitJob: async () => ({ jobId: "engine-job-id" }),
}));

// ── Batch export service mock ──────────────────────────────────────────────────

vi.mock("../../server/services/batchExportService", () => ({
  planBatchExport: async () => ({ items: [] }),
  enqueueRenderJob: async () => ({ success: true, queuePosition: 1 }),
}));

// ── Autoposter mock ────────────────────────────────────────────────────────────

vi.mock("../../server/services/autoposterService", () => ({
  runAutoposterJob: async () => ({ status: "queued" }),
}));

// ── Video engine service mock ─────────────────────────────────────────────────

vi.mock("../../server/services/videoEngineService", () => ({
  buildVideoJobFromScript: async () => ({ jobId: "ve-job-id" }),
  buildBatchJobs: async () => [{ jobId: "ve-batch-job-id" }],
}));

// ── Credential resolution mock ────────────────────────────────────────────────

vi.mock("../../server/services/credentialService", () => ({
  resolveCredentials: async () => ({}),
}));

// ── Platform policy mock ──────────────────────────────────────────────────────

vi.mock("../../server/services/platformPolicyService", () => ({
  checkPlatformPolicy: async () => ({ allowed: true }),
  validatePlatformCredentials: async () => ({ valid: true }),
}));

// ── Video probe mock ──────────────────────────────────────────────────────────

vi.mock("../../server/services/videoProbeService", () => ({
  probeVideo: async () => ({ duration: 30, width: 1920, height: 1080 }),
}));

// ═══════════════════════════════════════════════════════════════════════════════
// Fixture builders (inline — no external fixture file)
// ═══════════════════════════════════════════════════════════════════════════════

const CHECKSUM = "a".repeat(64);

function eligibleRights(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    contract_version: "2.0.0",
    source_asset_id: "asset-test-123",
    source_checksum: CHECKSUM,
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
    ...overrides,
  };
}

function expiredRights(): Record<string, unknown> {
  return eligibleRights({
    expiry: "2020-01-01T00:00:00.000Z",
    publication_eligible: false,
    ineligibility_reasons: ["CONSENT_EXPIRED"],
  });
}

function bindingMismatchRights(): Record<string, unknown> {
  return eligibleRights({ source_asset_id: "WRONG-ASSET-ID" });
}

// ═══════════════════════════════════════════════════════════════════════════════
// POST /api/batch-export
// ═══════════════════════════════════════════════════════════════════════════════

describe("POST /api/batch-export — RightsAndConsentV2 enforcement", () => {
  let app: Express;

  beforeEach(async () => {
    const batchExportRouter = (await import("../../server/routes/batchExport")).default;
    app = express();
    app.use(express.json());
    app.use("/api", batchExportRouter);
  });

  const baseBody = { projectId: "proj-123" };

  it("POSITIVE: eligible rights_record → 2xx (proceeds)", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .send({ ...baseBody, rights_record: eligibleRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("N1: missing rights_record → 400", async () => {
    const res = await request(app).post("/api/batch-export").send(baseBody);
    expect(res.status).toBe(400);
  });

  it("N2: malformed rights_record (string) → 400", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("N3: expired rights at server time → 403", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
    expect(res.body.ineligibility_reasons).toContain("CONSENT_EXPIRED");
  });

  it("N4: binding mismatch (source_asset_id wrong) → 403", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// POST /api/v1/publish
// ═══════════════════════════════════════════════════════════════════════════════

describe("POST /api/v1/publish — RightsAndConsentV2 enforcement", () => {
  let app: Express;

  beforeEach(async () => {
    const publishRouter = (await import("../../server/routes/publish")).default;
    app = express();
    app.use(express.json());
    app.use("/api/v1", publishRouter);
  });

  const baseBody = {
    video_url: "https://example.com/video.mp4",
    platforms: ["youtube"],
  };

  it("POSITIVE: eligible rights_record → 2xx", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .send({ ...baseBody, rights_record: eligibleRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("N1: missing rights_record → 400", async () => {
    const res = await request(app).post("/api/v1/publish").send(baseBody);
    expect(res.status).toBe(400);
  });

  it("N2: malformed rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("N3: expired rights at server time → 403", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
    expect(res.body.ineligibility_reasons).toContain("CONSENT_EXPIRED");
  });

  it("N4: binding mismatch → 403", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// POST /api/v1/video/generate_and_publish
// ═══════════════════════════════════════════════════════════════════════════════

describe("POST /api/v1/video/generate_and_publish — RightsAndConsentV2 enforcement", () => {
  let app: Express;

  beforeEach(async () => {
    const videoFlowRouter = (await import("../../server/routes/video_flow")).default;
    app = express();
    app.use(express.json());
    app.use("/api/v1/video", videoFlowRouter);
  });

  const baseBody = {
    prompt: "A test video prompt",
    platforms: ["youtube"],
  };

  it("POSITIVE: eligible rights_record → 2xx", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .send({ ...baseBody, rights_record: eligibleRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("N1: missing rights_record → 400", async () => {
    const res = await request(app).post("/api/v1/video/generate_and_publish").send(baseBody);
    expect(res.status).toBe(400);
  });

  it("N2: malformed rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("N3: expired rights at server time → 403", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
    expect(res.body.ineligibility_reasons).toContain("CONSENT_EXPIRED");
  });

  it("N4: binding mismatch → 403", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// POST /api/video-engine/generate
// ═══════════════════════════════════════════════════════════════════════════════

describe("POST /api/video-engine/generate — RightsAndConsentV2 enforcement", () => {
  let app: Express;

  beforeEach(async () => {
    const videoEngineRouter = (await import("../../server/routes/videoEngine")).default;
    app = express();
    app.use(express.json());
    app.use("/api/video-engine", videoEngineRouter);
  });

  const baseBody = { script: "A test script for video generation" };

  it("POSITIVE: eligible rights_record → 2xx", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .send({ ...baseBody, rights_record: eligibleRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("N1: missing rights_record → 400", async () => {
    const res = await request(app).post("/api/video-engine/generate").send(baseBody);
    expect(res.status).toBe(400);
  });

  it("N2: malformed rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("N3: expired rights at server time → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
    expect(res.body.ineligibility_reasons).toContain("CONSENT_EXPIRED");
  });

  it("N4: binding mismatch → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// POST /api/video-engine/batch
// ═══════════════════════════════════════════════════════════════════════════════

describe("POST /api/video-engine/batch — RightsAndConsentV2 enforcement", () => {
  let app: Express;

  beforeEach(async () => {
    const videoEngineRouter = (await import("../../server/routes/videoEngine")).default;
    app = express();
    app.use(express.json());
    app.use("/api/video-engine", videoEngineRouter);
  });

  const baseBody = { scripts: ["Script one", "Script two"] };

  it("POSITIVE: eligible rights_record → 2xx", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .send({ ...baseBody, rights_record: eligibleRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("N1: missing rights_record → 400", async () => {
    const res = await request(app).post("/api/video-engine/batch").send(baseBody);
    expect(res.status).toBe(400);
  });

  it("N2: malformed rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("N3: expired rights at server time → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
    expect(res.body.ineligibility_reasons).toContain("CONSENT_EXPIRED");
  });

  it("N4: binding mismatch → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// POST /api/render-jobs/:jobId/dead-letter/retry
// Re-evaluates stored rights from DB record at retry time
// ═══════════════════════════════════════════════════════════════════════════════

describe("POST /api/render-jobs/:jobId/dead-letter/retry — rights re-evaluation", () => {
  let app: Express;

  beforeEach(async () => {
    mockJobRecord = null;
    const renderJobsRouter = (await import("../../server/routes/renderJobs")).default;
    app = express();
    app.use(express.json());
    app.use("/api", renderJobsRouter);
  });

  it("POSITIVE: dead-letter job with still-eligible stored rights → 2xx", async () => {
    mockJobRecord = {
      jobId: "job-dl-1",
      status: "dead_letter",
      tenantId: "tenant-1",
      rightsRecord: eligibleRights(),
      attemptsMade: 3,
      deadLetterRetryCount: 0,
      webhookUrl: null,
    };
    const res = await request(app)
      .post("/api/render-jobs/job-dl-1/dead-letter/retry")
      .send({});
    expect(res.status).toBeLessThan(400);
  });

  it("N1: dead-letter job with null rightsRecord (pre-enforcement) → 403", async () => {
    mockJobRecord = {
      jobId: "job-dl-2",
      status: "dead_letter",
      tenantId: "tenant-1",
      rightsRecord: null,
      attemptsMade: 3,
      deadLetterRetryCount: 0,
      webhookUrl: null,
    };
    const res = await request(app)
      .post("/api/render-jobs/job-dl-2/dead-letter/retry")
      .send({});
    expect(res.status).toBe(403);
    expect(res.body.error).toMatch(/no stored rights record/i);
  });

  it("N2: dead-letter job with malformed stored rights → 400", async () => {
    mockJobRecord = {
      jobId: "job-dl-3",
      status: "dead_letter",
      tenantId: "tenant-1",
      rightsRecord: "not-a-valid-rights-object",
      attemptsMade: 3,
      deadLetterRetryCount: 0,
      webhookUrl: null,
    };
    const res = await request(app)
      .post("/api/render-jobs/job-dl-3/dead-letter/retry")
      .send({});
    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/malformed/i);
  });

  it("N3: dead-letter job with expired stored rights → 403", async () => {
    mockJobRecord = {
      jobId: "job-dl-4",
      status: "dead_letter",
      tenantId: "tenant-1",
      rightsRecord: expiredRights(),
      attemptsMade: 3,
      deadLetterRetryCount: 0,
      webhookUrl: null,
    };
    const res = await request(app)
      .post("/api/render-jobs/job-dl-4/dead-letter/retry")
      .send({});
    expect(res.status).toBe(403);
    expect(res.body.ineligibility_reasons).toContain("CONSENT_EXPIRED");
  });

  it("N4: job not in dead_letter state → 400 (guard before rights check)", async () => {
    mockJobRecord = {
      jobId: "job-dl-5",
      status: "queued",
      tenantId: "tenant-1",
      rightsRecord: eligibleRights(),
      attemptsMade: 1,
      deadLetterRetryCount: 0,
      webhookUrl: null,
    };
    const res = await request(app)
      .post("/api/render-jobs/job-dl-5/dead-letter/retry")
      .send({});
    expect(res.status).toBe(400);
  });
});
