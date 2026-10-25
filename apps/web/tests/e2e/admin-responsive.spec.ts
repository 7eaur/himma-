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
    // The 89-asset inventory can exceed 12,000px on mobile. A giant
    // full-page screenshot obscures the real responsive layout; record its
    // initial viewport while route/data assertions guard correctness.
    fullPage: route !== "/admin/v2-media",
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
  "/admin/account",
  "/admin/v2-assessments",
  "/admin/v2-lesson-review",
  "/admin/v2-media",
  "/admin/v2-reviewed-recordings",
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
      if (route === "/admin/content-preview") {
        // Do not record the initial spinner as evidence of loaded V2/V1 UI.
        await expect(page.getByTestId("content-index-item").first()).toBeAttached({ timeout: 25000 });
      }
      if (route === "/admin/v2-media") {
        await expect(page.getByText(/الملفات المرشحة الموجودة/)).toBeVisible({ timeout: 15000 });
      }
      await expectNoHorizontalOverflow(page);
      await capture(page, viewport.name, route);

      if (route === "/admin/content-preview") {
        const detailPane = page.getByTestId("content-detail-pane");
        await expect(detailPane).toBeVisible({ timeout: 10000 });
        await expectNoHorizontalOverflow(page);

        if (viewport.width <= 820) {
          const indexPane = page.getByTestId("content-index-pane");
          await expect(indexPane).toBeHidden();

          const openNavigator = page.getByTestId("content-open-navigator");
          await expect(openNavigator).toBeVisible();
          const openBox = await openNavigator.boundingBox();
          expect(openBox?.height ?? 0).toBeGreaterThanOrEqual(44);

          await openNavigator.click();
          await expect(indexPane).toBeVisible();

          const firstContent = page.getByTestId("content-index-item").first();
          await expect(firstContent).toBeVisible();
          await firstContent.click();

          await expect(indexPane).toBeHidden();
          await expect(detailPane).toBeVisible();
          await expect(page.getByRole("navigation", { name: "التنقل بين عناصر القسم" })).toBeVisible();
          await expectNoHorizontalOverflow(page);
          await capture(page, viewport.name, "/admin/content-preview-detail");
        } else {
          const firstContent = page.getByTestId("content-index-item").first();
          await expect(firstContent).toBeVisible();
          await firstContent.click();
          await expect(detailPane).toBeVisible();
          await expectNoHorizontalOverflow(page);
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

// P09.0 screenshot baseline: authenticated V2 supervisor routes, including
// the reviewed-recording archive created in P08. These are fixture screenshots
// captured by the existing real Playwright backend + database CI job.
test("P09.0 V2 supervisor pages keep a desktop visual baseline", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await login(page);
  const routes = [
    { route: "/admin/v2-assessments", heading: "تقييمات V2 والمراجعة" },
    { route: "/admin/v2-lesson-review", heading: "مراجعة قراءة وكتابة الدروس" },
    { route: "/admin/v2-media", heading: "سجل وسائط V2" },
    { route: "/admin/v2-reviewed-recordings", heading: "التسجيلات التي اكتمل تقييمها" },
    { route: "/admin/students", heading: "الطلاب" },
    { route: "/admin/content-preview", heading: "المحتوى المعتمد" },
    { route: "/admin/account", heading: "إعدادات المشرف" },
  ];
  for (const { route, heading } of routes) {
    await page.goto(route);
    await expect(page).not.toHaveURL(/\/admin\/login/);
    if (route === "/admin/account") {
      // Intentional legacy redirect; never mistake it for a distinct account UI.
      await expect(page).toHaveURL(/\/admin\/settings$/);
    }
    await expect(page.getByRole("heading", { level: 1, name: heading, exact: true })).toBeVisible();
    if (route === "/admin/content-preview") {
      await expect(page.getByTestId("content-index-item").first()).toBeAttached({ timeout: 25000 });
    }
    if (route === "/admin/v2-media") {
      await expect(page.getByText(/الملفات المرشحة الموجودة/)).toBeVisible({ timeout: 15000 });
    }
    await expectNoHorizontalOverflow(page);
    await capture(page, "desktop-1440x900", route);
  }
});
