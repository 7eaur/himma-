import { responseCacheControl } from "./cachePolicy";

const media = (upstreamPath: string, upstreamCacheControl: string | null, ok = true, hasSetCookie = false) =>
  responseCacheControl({ upstreamPath, method: "GET", ok, upstreamCacheControl, hasSetCookie });

describe("V2 educational media browser cache policy", () => {
  it("allows only the exact authenticated private media policy", () => {
    expect(media("v2/content/media/VID-L1-01", "private, max-age=86400, immutable")).toBe("private, max-age=86400, immutable");
    expect(media("v2/content/media/VOC-04", "private, max-age=86400, immutable")).toBe("private, max-age=86400, immutable");
  });

  it("does not cache unsigned, failed, cookie-setting or unrelated responses", () => {
    expect(media("v2/content/media/VID-L1-01", "private, no-store")).toBe("private, no-store");
    expect(media("v2/content/media/VID-L1-01", "private, max-age=86400, immutable", false)).toBe("private, no-store");
    expect(media("v2/content/media/VID-L1-01", "private, max-age=86400, immutable", true, true)).toBe("private, no-store");
    expect(media("v2/lessons/sessions/1/interaction", "private, max-age=86400, immutable")).toBe("private, no-store");
    expect(media("v2/content/media/VID-L1-01", "public, max-age=86400")).toBe("private, no-store");
    expect(responseCacheControl({ upstreamPath: "v2/content/media/VID-L1-01", method: "POST", ok: true, upstreamCacheControl: "private, max-age=86400, immutable", hasSetCookie: false })).toBe("private, no-store");
  });
});
