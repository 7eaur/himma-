import { test, expect, type APIRequestContext, type BrowserContext } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function login(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, { data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD } });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

test("an old audio-review bookmark opens the current assessment review queue", async ({ page, request, context }) => {
  await login(request, context);
  await page.goto("/admin/audio-review?student_id=4242");
  await expect(page).toHaveURL(/\/admin\/v2-assessments$/);
  await expect(page.getByRole("heading", { name: "الاختبارات والتسكين" })).toBeVisible();
  await expect(page.getByRole("link", { name: "قراءات الدروس" })).toHaveAttribute("href", "/admin/v2-lesson-review");
  await expect(page.getByText("أرشيف الصوت المقيّم")).not.toBeVisible();
});
