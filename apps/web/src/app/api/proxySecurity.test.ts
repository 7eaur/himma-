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
    // Railway builds inherit RAILWAY_PUBLIC_DOMAIN. A synthetic origin test
    // must not inherit a different deployed host, unlike real requests.
    const previous = process.env.RAILWAY_PUBLIC_DOMAIN;
    delete process.env.RAILWAY_PUBLIC_DOMAIN;
    try {
      const sameOrigin = new NextRequest("https://himma.example/api/auth/login", { method: "POST", headers: { origin: "https://himma.example" } });
      const serverRequest = new NextRequest("https://himma.example/api/auth/login", { method: "POST" });
      expect(rejectUnsafeMutation(sameOrigin)).toBeNull();
      expect(rejectUnsafeMutation(serverRequest)).toBeNull();
    } finally {
      if (previous !== undefined) process.env.RAILWAY_PUBLIC_DOMAIN = previous;
    }
  });

  it("accepts Railway HTTPS public origin even if Next sees the internal HTTP URL", () => {
    const previous = process.env.RAILWAY_PUBLIC_DOMAIN;
    process.env.RAILWAY_PUBLIC_DOMAIN = "himma-web-production-eafd.up.railway.app";
    try {
      const request = new NextRequest("http://localhost:8080/api/auth/login", {
        method: "POST",
        headers: {
          origin: "https://himma-web-production-eafd.up.railway.app",
          "sec-fetch-site": "same-origin",
        },
      });
      expect(rejectUnsafeMutation(request)).toBeNull();
    } finally {
      if (previous === undefined) delete process.env.RAILWAY_PUBLIC_DOMAIN;
      else process.env.RAILWAY_PUBLIC_DOMAIN = previous;
    }
  });

  it("rejects untrusted origin despite an internal URL and same-site claim", () => {
    const previous = process.env.RAILWAY_PUBLIC_DOMAIN;
    process.env.RAILWAY_PUBLIC_DOMAIN = "himma-web-production-eafd.up.railway.app";
    try {
      const request = new NextRequest("http://localhost:8080/api/auth/login", {
        method: "POST",
        headers: {
          origin: "https://attacker.example",
          "sec-fetch-site": "same-origin",
        },
      });
      expect(rejectUnsafeMutation(request)?.status).toBe(403);
    } finally {
      if (previous === undefined) delete process.env.RAILWAY_PUBLIC_DOMAIN;
      else process.env.RAILWAY_PUBLIC_DOMAIN = previous;
    }
  });

  it("keeps rejecting cross-site mutations with a matching public origin", () => {
    const previous = process.env.RAILWAY_PUBLIC_DOMAIN;
    process.env.RAILWAY_PUBLIC_DOMAIN = "himma-web-production-eafd.up.railway.app";
    try {
      const request = new NextRequest("http://localhost:8080/api/auth/login", {
        method: "POST",
        headers: {
          origin: "https://himma-web-production-eafd.up.railway.app",
          "sec-fetch-site": "cross-site",
        },
      });
      expect(rejectUnsafeMutation(request)?.status).toBe(403);
    } finally {
      if (previous === undefined) delete process.env.RAILWAY_PUBLIC_DOMAIN;
      else process.env.RAILWAY_PUBLIC_DOMAIN = previous;
    }
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
