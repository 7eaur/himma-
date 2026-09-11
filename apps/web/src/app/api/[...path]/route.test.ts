import { responseCacheControl } from "./cachePolicy";

describe("BFF response cache policy", () => {
  it("preserves a safe public cache policy for approved media reads", () => {
    expect(responseCacheControl({
      upstreamPath: "media/VOC-01",
      method: "GET",
      ok: true,
      upstreamCacheControl: "public, max-age=86400, immutable",
      hasSetCookie: false,
    })).toBe("public, max-age=86400, immutable");
  });

  it("allows HEAD on approved media to use the same public policy", () => {
    expect(responseCacheControl({
      upstreamPath: "media/LET-01",
      method: "HEAD",
      ok: true,
      upstreamCacheControl: null,
      hasSetCookie: false,
    })).toBe("public, max-age=86400");
  });

  it.each([
    ["researcher/students/1", "GET", true, null, false],
    ["media/VOC-01", "POST", true, "public, max-age=86400", false],
    ["media/NOT-APPROVED", "GET", false, "public, max-age=86400", false],
    ["media/VOC-01", "GET", true, "private, no-store", false],
    ["media/VOC-01", "GET", true, "public, max-age=86400", true],
  ])("keeps private or unsafe responses out of shared caches", (upstreamPath, method, ok, upstreamCacheControl, hasSetCookie) => {
    expect(responseCacheControl({
      upstreamPath,
      method,
      ok,
      upstreamCacheControl,
      hasSetCookie,
    })).toBe("private, no-store");
  });
});
