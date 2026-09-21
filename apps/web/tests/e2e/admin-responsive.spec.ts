import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const SCREENSHOT_DIR = path.join(process.cwd(), "playwright-report", "screenshots", "admin-responsive");

async function login(page: Page) {
  if (!RESEARCHER_USERNAME || !RESEARCHER_PASSWORD) throw new Error("E2E researcher credentials are required");
  await page.goto("/admin/login");
  await page.getByTestId("input-username").fill(RESEARCHER_USERNAME);
  await page.getByTestId("input-password").fill(RESEARCHER_PASSWORD);
  await page.getByTestId("login-submit").click();
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20000 });
}

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
  }));
  expect(metrics.documentWidth, JSON.stringify(metrics)).toBeLessThanOrEqual(metrics.innerWidth + 1);
  expect(metrics.bodyWidth, JSON.stringify(metrics)).toBeLessThanOrEqual(metrics.innerWidth + 1);
}

async function capture(page: Page, viewport: string, route: string) {
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  const routeName = route === "/admin" ? "dashboard" : route.replace(/^\/admin\/?/, "").replaceAll("/", "-");
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, `${viewport}-${routeName}.png`),
    fullPage: true,
  });
}

const ROUTES = [
  "/admin",
  "/admin/students",
  "/admin/students/new",
  "/admin/audio-review",
  "/admin/content-preview",
  "/admin/reports",
  "/admin/skill-reports",
  "/admin/settings",
];

for (const viewport of [
  { name: "phone-390x844", width: 390, height: 844 },
  { name: "small-tablet-768x1024", width: 768, height: 1024 },
]) {
  test(`admin shell and key pages stay usable without horizontal overlap on ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await login(page);

    for (const route of ROUTES) {
      await page.goto(route);
      await expect(page).not.toHaveURL(/\/admin\/login/);
      await expect(page.getByRole("button", { name: "فتح القائمة" })).toBeVisible();
      const notificationsTrigger = page.getByRole("button", { name: "الإشعارات" });
      await expect(notificationsTrigger).toHaveCount(1);
      await expect(notificationsTrigger).toBeVisible();
      await page.getByRole("button", { name: "فتح القائمة" }).click();
      await expect(page.getByRole("dialog", { name: "قائمة لوحة المشرف" })).toBeVisible();
      await expect(page.getByRole("button", { name: "الإشعارات" })).toHaveCount(1);
      await page.getByRole("dialog", { name: "قائمة لوحة المشرف" }).getByRole("button", { name: "إغلاق القائمة" }).click();
      await page.waitForTimeout(250);
      await expectNoHorizontalOverflow(page);
      await capture(page, viewport.name, route);

      if (route === "/admin/content-preview") {
        const firstContent = page.getByTestId("content-index-item").first();
        await expect(firstContent).toBeVisible({ timeout: 10000 });
        await firstContent.click();
        await expect(page.getByTestId("content-detail-pane")).toBeVisible();
        await expectNoHorizontalOverflow(page);

        if (viewport.width <= 820) {
          await expect(page.getByTestId("content-index-pane")).toBeHidden();
          const back = page.getByRole("button", { name: "العودة إلى فهرس المحتوى" });
          await expect(back).toBeVisible();
          const backBox = await back.boundingBox();
          expect(backBox?.height ?? 0).toBeGreaterThanOrEqual(44);
          await capture(page, viewport.name, "/admin/content-preview-detail");
          await back.click();
          await expect(page.getByTestId("content-index-pane")).toBeVisible();
          await expect(page.getByTestId("content-detail-pane")).toBeHidden();
        }
      }
    }

    await page.goto("/admin/students");
    const studentLink = page.locator('a[href^="/admin/students/"]').filter({ hasNot: page.locator('a[href="/admin/students/new"]') }).first();
    if (await studentLink.isVisible().catch(() => false)) {
      const href = await studentLink.getAttribute("href");
      if (href && /^\/admin\/students\/\d+$/.test(href)) {
        await page.goto(href);
        await expect(page.getByRole("button", { name: "فتح القائمة" })).toBeVisible();
        await expectNoHorizontalOverflow(page);
        await capture(page, viewport.name, "student-detail");
      }
    }
  });
}