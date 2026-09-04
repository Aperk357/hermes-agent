/**
 * Integration tests: RightsAndConsentV2 enforcement on bypass routes
 *
 * Proves 25 causal negatives (5 tests × 5 routes).
 * Routes under test:
 *   POST /api/batch-export
 *   POST /api/v1/publish
 *   POST /api/v1/video/generate_and_publish
 *   POST /api/video-engine/generate
 *   POST /api/video-engine/batch
 *
 * Each route must: reject absent rights (400), reject malformed (400),
 * reject server-time-ineligible (403), reject binding mismatch (403),
 * and accept a fully authorized eligible record.
 *
 * Pattern mirrors tests/integration/renderJobsRightsEnforcement.test.ts
 * (the reference implementation for POST /render-jobs).
 */

import request from "supertest";
import app from "../../server/app";
import { buildValidRightsRecord, buildExpiredRightsRecord } from "../fixtures/rightsFixtures";

const AUTH_HEADERS = { Authorization: "Bearer test-token" };

// ---------------------------------------------------------------------------
// Shared fixture builders
// ---------------------------------------------------------------------------

function validRights() {
  return buildValidRightsRecord();
}

function expiredRights() {
  return buildExpiredRightsRecord();
}

function bindingMismatchRights() {
  const r = buildValidRightsRecord();
  return { ...r, source_asset_id: "WRONG-ASSET-ID-XYZ" };
}

// ---------------------------------------------------------------------------
// POST /api/batch-export
// ---------------------------------------------------------------------------

describe("POST /api/batch-export — RightsAndConsentV2 enforcement", () => {
  const baseBody = { projectId: "proj-123" };

  it("POSITIVE: eligible rights_record → proceeds (2xx)", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: validRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("NEGATIVE: missing rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .set(AUTH_HEADERS)
      .send(baseBody);
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: malformed rights_record (string) → 400", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: expired at server time → 403", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
  });

  it("NEGATIVE: binding mismatch (asset_id) → 403", async () => {
    const res = await request(app)
      .post("/api/batch-export")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ---------------------------------------------------------------------------
// POST /api/v1/publish
// ---------------------------------------------------------------------------

describe("POST /api/v1/publish — RightsAndConsentV2 enforcement", () => {
  const baseBody = {
    video_url: "https://example.com/video.mp4",
    platforms: ["youtube"],
  };

  it("POSITIVE: eligible rights_record → proceeds (2xx)", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: validRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("NEGATIVE: missing rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .set(AUTH_HEADERS)
      .send(baseBody);
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: malformed rights_record (string) → 400", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: expired at server time → 403", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
  });

  it("NEGATIVE: binding mismatch (asset_id) → 403", async () => {
    const res = await request(app)
      .post("/api/v1/publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ---------------------------------------------------------------------------
// POST /api/v1/video/generate_and_publish
// ---------------------------------------------------------------------------

describe("POST /api/v1/video/generate_and_publish — RightsAndConsentV2 enforcement", () => {
  const baseBody = {
    prompt: "A test video prompt",
    platforms: ["youtube"],
  };

  it("POSITIVE: eligible rights_record → proceeds (2xx)", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: validRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("NEGATIVE: missing rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .set(AUTH_HEADERS)
      .send(baseBody);
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: malformed rights_record (string) → 400", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: expired at server time → 403", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
  });

  it("NEGATIVE: binding mismatch (asset_id) → 403", async () => {
    const res = await request(app)
      .post("/api/v1/video/generate_and_publish")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ---------------------------------------------------------------------------
// POST /api/video-engine/generate
// ---------------------------------------------------------------------------

describe("POST /api/video-engine/generate — RightsAndConsentV2 enforcement", () => {
  const baseBody = {
    script: "A test script for video generation",
  };

  it("POSITIVE: eligible rights_record → proceeds (2xx)", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: validRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("NEGATIVE: missing rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .set(AUTH_HEADERS)
      .send(baseBody);
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: malformed rights_record (string) → 400", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: expired at server time → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
  });

  it("NEGATIVE: binding mismatch (asset_id) → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/generate")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});

// ---------------------------------------------------------------------------
// POST /api/video-engine/batch
// ---------------------------------------------------------------------------

describe("POST /api/video-engine/batch — RightsAndConsentV2 enforcement", () => {
  const baseBody = {
    scripts: ["Script one", "Script two"],
  };

  it("POSITIVE: eligible rights_record → proceeds (2xx)", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: validRights() });
    expect(res.status).toBeLessThan(400);
  });

  it("NEGATIVE: missing rights_record → 400", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .set(AUTH_HEADERS)
      .send(baseBody);
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: malformed rights_record (string) → 400", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: "not-an-object" });
    expect(res.status).toBe(400);
  });

  it("NEGATIVE: expired at server time → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: expiredRights() });
    expect(res.status).toBe(403);
  });

  it("NEGATIVE: binding mismatch (asset_id) → 403", async () => {
    const res = await request(app)
      .post("/api/video-engine/batch")
      .set(AUTH_HEADERS)
      .send({ ...baseBody, rights_record: bindingMismatchRights() });
    expect(res.status).toBe(403);
  });
});
