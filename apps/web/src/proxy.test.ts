/** @jest-environment node */
import { NextRequest } from "next/server";
import { proxy, config } from "./proxy";

const originalFetch = global.fetch;
const session = (role: string, status = 200) => jest.fn().mockResolvedValue(new Response(JSON.stringify({ role }), { status }));
const request = (path: string, cookie = "") => new NextRequest(`http://localhost${path}`, { headers: cookie ? { cookie } : {} });

afterEach(() => { global.fetch = originalFetch; });

test.each(["/student/login", "/admin/login"])("login remains public: %s", async (path) => {
  global.fetch = jest.fn();
  expect((await proxy(request(path))).status).toBe(200);
  expect(global.fetch).not.toHaveBeenCalled();
});

test("student routes have a server guard and preserve a local return path", async () => {
  expect(config.matcher).toContain("/student/:path*");
  const response = await proxy(request("/student/session/4?mode=resume"));
  const destination = new URL(response.headers.get("location")!);
  expect(destination.pathname).toBe("/student/login");
  expect(destination.searchParams.get("next")).toBe("/student/session/4?mode=resume");
});

test.each([401, 403])("invalid cookie is rejected (%s)", async (status) => {
  global.fetch = session("student", status);
  expect((await proxy(request("/student", "access_token=invalid"))).status).toBe(307);
});

test.each([["/student", "researcher"], ["/admin/students", "student"]])("wrong role cannot open %s", async (path, role) => {
  global.fetch = session(role);
  expect((await proxy(request(path, "access_token=test"))).status).toBe(307);
});

test.each([["/student", "student"], ["/admin/students", "researcher"]])("verified account can open %s", async (path, role) => {
  global.fetch = session(role);
  expect((await proxy(request(path, "access_token=test"))).status).toBe(200);
  expect(global.fetch).toHaveBeenCalledWith(expect.stringMatching(/\/me$/), expect.objectContaining({ cache: "no-store" }));
});

test("upstream outage fails closed without pretending the session expired", async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error("offline"));
  expect((await proxy(request("/student", "access_token=test"))).status).toBe(503);
});
