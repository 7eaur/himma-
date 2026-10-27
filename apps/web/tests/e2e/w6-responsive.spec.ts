import { expect, test, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const SCREENSHOT_DIR = path.join(process.cwd(), "playwright-report", "screenshots", "student-responsive");
const VIEWPORTS = [
  { name: "phone-320", width: 320, height: 720 },
  { name: "phone-360", width: 360, height: 800 },
  { name: "phone-390", width: 390, height: 844 },
  { name: "phone-430", width: 430, height: 932 },
  { name: "tablet-768", width: 768, height: 1024 },
  { name: "desktop-1440", width: 1440, height: 1000 },
] as const;

async function addAuthCookie(context: BrowserContext, response: Awaited<ReturnType<APIRequestContext["post"]>>) {
  const value = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(value).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: value ?? "", domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

async function loginSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, { data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD } });
  expect(response.status()).toBe(200);
  await addAuthCookie(context, response);
}

async function loginStudent(request: APIRequestContext, context: BrowserContext, accessCode: string) {
  const response = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(response.status()).toBe(200);
  await addAuthCookie(context, response);
}

async function createStudent(page: Page, request: APIRequestContext, context: BrowserContext) {
  await loginSupervisor(request, context);
  await page.goto("/admin/students/new");
  const name = `طالب قبول W6 ${Date.now()}`;
  await page.getByTestId("input-student-name").fill(name);
  await page.getByTestId("submit-create-student").click();
  const code = page.getByTestId("student-access-code");
  await expect(code).toBeVisible({ timeout: 10000 });
  const accessCode = (await code.textContent())?.trim() ?? "";
  expect(accessCode).toMatch(/^\d{6}$/);
  return { name, accessCode };
}

async function expectNoHorizontalOverflow(page: Page) {
  const widths = await page.evaluate(() => ({ viewport: window.innerWidth, document: document.documentElement.scrollWidth, body: document.body.scrollWidth }));
  expect(widths.document, JSON.stringify(widths)).toBeLessThanOrEqual(widths.viewport + 1);
  expect(widths.body, JSON.stringify(widths)).toBeLessThanOrEqual(widths.viewport + 1);
}

async function capture(page: Page, viewport: string, surface: string) {
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, `${viewport}-${surface}.png`),
    fullPage: true,
  });
}

test("W6 Student critical surfaces stay usable from 320px through desktop", async ({ page, context, request }) => {
  test.setTimeout(120000);
  const student = await createStudent(page, request, context);
  await context.clearCookies();
  await loginStudent(request, context, student.accessCode);

  for (const viewport of VIEWPORTS) {
    await test.step(`${viewport.name} student home`, async () => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/student");
      await expect(page.getByTestId("student-home")).toBeVisible({ timeout: 10000 });
      await expectNoHorizontalOverflow(page);
      const primary = page.getByTestId("student-primary-action");
      await expect(primary).toBeVisible();
      const box = await primary.boundingBox();
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
      await capture(page, viewport.name, "home");
    });
  }

  const start = await request.post(`${API_URL}/assessment/start`, { data: { session_type: "pretest" } });
  expect(start.status()).toBe(200);
  const payload = await start.json();
  const sessionId = payload.id ?? payload.session_id;
  expect(sessionId).toBeTruthy();

  for (const viewport of VIEWPORTS) {
    await test.step(`${viewport.name} assessment`, async () => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto(`/student/session/${sessionId}`);
      const root = page.getByTestId("assessment-session");
      await expect(root).toHaveAttribute("data-phase", "question", { timeout: 15000 });
      await expectNoHorizontalOverflow(page);

      const title = page.getByTestId("question-title");
      await expect(title).toBeVisible();
      if (viewport.width <= 430) {
        const titleFontSize = await title.evaluate((node) => Number.parseFloat(getComputedStyle(node).fontSize));
        expect(titleFontSize).toBeLessThanOrEqual(25);
      }

      const interactive = page.locator('button[aria-pressed="false"], [data-testid="record-reading"]').first();
      await expect(interactive).toBeVisible({ timeout: 7000 });
      const box = await interactive.boundingBox();
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
      await capture(page, viewport.name, "assessment");
    });
  }
});
