import { responseCacheControl } from "./cachePolicy";

describe("BFF response cache policy", () => {
  it("preserves browser-only reuse for fingerprinted educational images", () => {
    expect(responseCacheControl({ upstreamPath: "v2/content/media/VOC-04", method: "GET", ok: true,
      upstreamCacheControl: "private, max-age=86400, immutable", hasSetCookie: false,
    })).toBe("private, max-age=86400, immutable");
  });

  it.each(["v2/student/home", "recordings/1", "v2/lessons/admin/media/VOC-04", "v2/content/media/VOC-04/extra"])(
    "never expands browser reuse to private data or unrelated routes: %s", (upstreamPath) => {
      expect(responseCacheControl({ upstreamPath, method: "GET", ok: true,
        upstreamCacheControl: "private, max-age=86400, immutable", hasSetCookie: false,
      })).toBe("private, no-store");
    });

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
    ["v2/content/media/VOC-04", "GET", true, "public, max-age=86400", false],
    ["v2/content/media/VOC-04", "GET", false, "private, max-age=86400, immutable", false],
    ["v2/content/media/VOC-04", "GET", true, "private, max-age=86400, immutable", true],
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
