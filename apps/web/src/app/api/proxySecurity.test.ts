/** @jest-environment node */

import { NextRequest } from "next/server";
import { boundedRequestBody, MAX_PROXY_BODY_BYTES, ProxyBodyTooLarge, rejectUnsafeMutation } from "./proxySecurity";


describe("BFF mutation boundary", () => {
  it("rejects a cross-origin mutation", () => {
    const request = new NextRequest("https://himma.example/api/auth/login", {
      method: "POST",
      headers: { origin: "https://attacker.example", "sec-fetch-site": "cross-site" },
    });
    expect(rejectUnsafeMutation(request)?.status).toBe(403);
  });

  it("accepts same-origin and non-browser server mutations", () => {
    const sameOrigin = new NextRequest("https://himma.example/api/auth/login", { method: "POST", headers: { origin: "https://himma.example" } });
    const serverRequest = new NextRequest("https://himma.example/api/auth/login", { method: "POST" });
    expect(rejectUnsafeMutation(sameOrigin)).toBeNull();
    expect(rejectUnsafeMutation(serverRequest)).toBeNull();
  });

  it("rejects oversized bodies before buffering", async () => {
    const request = new NextRequest("https://himma.example/api/recordings", {
      method: "POST",
      headers: { "content-length": String(MAX_PROXY_BODY_BYTES + 1) },
      body: "small",
    });
    await expect(boundedRequestBody(request)).rejects.toBeInstanceOf(ProxyBodyTooLarge);
  });
});
