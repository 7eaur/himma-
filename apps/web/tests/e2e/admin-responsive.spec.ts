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
        await expect(page.getByTestId("v2-bank-question").first()).toBeVisible({ timeout: 25000 });
      }
      if (route === "/admin/students") {
        await expect(page.getByText("جاري تحميل بيانات V2...")).toHaveCount(0, { timeout: 20000 });
        await expect(page.getByText("تعذر تحميل تقدم طلاب V2، ولم تُستخدم أرقام V1 بديلة.")).toHaveCount(0);
        await expect(page.getByText("رمز الدخول", { exact: false })).toHaveCount(0);
        await expect(page.locator("table.data-table th").filter({ hasText: "التقدم V2" })).toHaveCount(1); // The mobile card also has its own V2 progress label
      }
      if (route === "/admin/v2-media") {
        await expect(page.getByText(/الملفات المرشحة الموجودة/)).toBeVisible({ timeout: 15000 });
      }
      await expectNoHorizontalOverflow(page);
      await capture(page, viewport.name, route);

      if (route === "/admin/content-preview") {
        const firstQuestion = page.getByTestId("v2-bank-question").first();
        await expect(firstQuestion).toBeVisible({ timeout: 25000 });
        await firstQuestion.getByText("الإجابة والمرجع للمشرف").click();
        await expect(firstQuestion.getByTestId("v2-bank-answer")).toHaveAttribute("open", "");
        await page.getByRole("combobox", { name: "القسم" }).selectOption("L1-01");
        await expect(page.getByText(/التمهيد:/)).toBeVisible();
        await expect(page.getByTestId("v2-bank-question").first()).toBeVisible();
        await expectNoHorizontalOverflow(page);
        if (viewport.width <= 820) {
          await capture(page, viewport.name, "/admin/content-preview-detail");
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
    { route: "/admin/v2-review-center", heading: "الاختبارات ومراجعة القراءة" },
    { route: "/admin/v2-assessments", heading: "الاختبارات ومراجعة القراءة" },
    { route: "/admin/v2-lesson-review", heading: "مراجعة قراءة وكتابة الدروس" },
    { route: "/admin/v2-media", heading: "الوسائط التعليمية" },
    { route: "/admin/v2-reviewed-recordings", heading: "التسجيلات التي اكتمل تقييمها" },
    { route: "/admin/students", heading: "الطلاب" },
    { route: "/admin/content-preview", heading: "بنك الدروس والأسئلة" },
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
      await expect(page.getByTestId("v2-bank-question").first()).toBeVisible({ timeout: 25000 });
    }
    if (route === "/admin/v2-media") {
      await expect(page.getByText(/الأصول المطلوبة المتاحة/)).toBeVisible({ timeout: 15000 });
    }
    await expectNoHorizontalOverflow(page);
    await capture(page, "desktop-1440x900", route);
  }
});

test("P09.1-D: supervisor sees official V2 first without V1 stars, and access code stays private", async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.goto("/admin/students/new");
  const name = `طالب التحقق V2 ${Date.now()}`;
  await page.getByTestId("input-student-name").fill(name);
  await page.getByTestId("submit-create-student").click();
  const code = (await page.getByTestId("student-access-code").textContent())?.trim() ?? "";
  expect(code).toMatch(/^\d{6}$/);

  await page.goto("/admin/students");
  await page.getByRole("textbox", { name: "البحث عن طالب بالاسم" }).fill(name);
  const studentLink = page.getByRole("link", { name, exact: true }).first();
  await expect(studentLink).toBeVisible({ timeout: 15000 });
  const id = (await studentLink.getAttribute("href"))?.match(/\/admin\/students\/(\d+)/)?.[1];
  expect(id).toBeTruthy();
  await expect(page.getByText(code, { exact: true })).toHaveCount(0);

  const identityRequest = page.waitForResponse(response => response.url().endsWith(`/v2/student/admin/students/${id}/account`) && response.request().method() === "GET");
  await page.goto(`/admin/students/${id}`);
  const accountIdentity = await (await identityRequest).json();
  expect(accountIdentity.source).toBe("himma_v2_account");
  expect(accountIdentity).not.toHaveProperty("access_code");
  expect(accountIdentity).not.toHaveProperty("core_completed_items");
  const projection = page.getByTestId("supervisor-v2-overview");
  await expect(projection).toBeVisible({ timeout: 10000 });
  await expect(projection.getByTestId("supervisor-v2-level")).toContainText("لم يُعتمد بعد");
  await expect(projection.getByTestId("supervisor-v2-progress")).toContainText("بانتظار الاعتماد");
  await expect(projection.getByTestId("supervisor-v2-action")).toBeVisible();
  await expect(projection.getByText("لم تُعتمد نتيجة")).toHaveCount(2);
  await expect(projection.getByTestId("supervisor-v2-lessons")).toHaveCount(0);
  await expect(projection.getByText("تعذر تحميل سجل هِمّة V2")).toHaveCount(0);
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  for (const viewport of [
    { name: "phone-360x780", width: 360, height: 780 },
    { name: "phone-390x844", width: 390, height: 844 },
    { name: "phone-430x932", width: 430, height: 932 },
    { name: "tablet-768x1024", width: 768, height: 1024 },
    { name: "desktop-1440x900", width: 1440, height: 900 },
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await expectNoHorizontalOverflow(page);
    await expect(projection.getByTestId("supervisor-v2-level")).toBeVisible();
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, `${viewport.name}-student360-v2.png`),
      fullPage: viewport.width < 900,
    });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText(code, { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "الحساب", exact: true }).click();
  await expect(page.getByText(code, { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "إظهار الرمز" }).click();
  await expect(page.getByText(code, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "إخفاء الرمز" }).click();
  await expect(page.getByText(code, { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "مسار هِمّة V2" }).click();
  await expect(page.getByTestId("supervisor-v2-overview")).toBeVisible();

  // Simulate an unavailable official V2 read-model. The supervisor must
  // see a bounded error, NEVER a V1 score replacing the current V2 source.
  const v2Route = `**/api/v2/student/admin/students/${id}/home`;
  await page.route(v2Route, route => route.fulfill({
    status: 503, contentType: "application/json", body: '{"detail":"temporary unavailable"}',
  }));
  await page.reload();
  await expect(page.getByRole("alert").filter({ hasText: "تعذر تحميل سجل هِمّة V2" })).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("supervisor-v2-progress")).toHaveCount(0);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "phone-390x844-student360-v2-source-error.png"),
    fullPage: true,
  });
  await page.unroute(v2Route);
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("supervisor-v2-progress")).toContainText("بانتظار الاعتماد", { timeout: 15000 });
});


test("W3: current bank and staff media gallery support real browsing and playback", async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.goto('/admin/content-preview');
  const first = page.getByTestId('v2-bank-question').first();
  await expect(first).toContainText('V2-PRE-Q01');
  await first.getByText('الإجابة والمرجع للمشرف', { exact: true }).click();
  await expect(first.getByText(/الخيارات الصحيحة أو ترتيبها/)).toBeVisible();
  await page.getByRole('combobox', { name: 'القسم', exact: true }).selectOption('L1-01');
  await expect(page.getByTestId('v2-bank-question')).toHaveCount(8);
  await expect(page.getByTestId('v2-bank-question').first()).toContainText('L1-01-GP-01');
  await expect(page.getByText(/التمهيد:/)).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await capture(page, 'phone-390x844', '/admin/v2-bank-lesson');
  await page.goto('/admin/v2-media');
  await expect(page.getByTestId('v2-media-card')).toHaveCount(89);
  await page.getByRole('combobox', { name: 'نوع الوسيط' }).selectOption('audio');
  await expect(page.getByTestId('v2-media-card')).toHaveCount(47);
  const card = page.getByTestId('v2-media-card').first();
  await card.getByRole('button', { name: /معاينة/ }).click();
  const audio = card.locator('audio');
  await expect(audio).toBeVisible();
  await audio.evaluate(async element => { await (element as HTMLAudioElement).play(); });
  await expect.poll(() => audio.evaluate(element => (element as HTMLAudioElement).duration)).toBeGreaterThan(0);
  await audio.evaluate(element => (element as HTMLAudioElement).pause());
  await expectNoHorizontalOverflow(page);
  await capture(page, 'phone-390x844', '/admin/v2-media-audio-preview');
});


test('W3: V2 reports export a real private workbook and keep historical metrics out of the default page', async ({ page }) => {
  await login(page);
  await page.goto('/admin/reports');
  await expect(page.getByTestId('v2-report-table')).toBeVisible();
  await expect(page.getByText('التقارير والإحصائيات · V1 التاريخي', { exact: true })).toHaveCount(0);
  const downloadReady = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Excel', exact: true }).click();
  const download = await downloadReady;
  expect(download.suggestedFilename()).toBe('himma-v2-cohort.xlsx');
  const file = await download.path();
  expect(file).toBeTruthy();
  const bytes = await (await import('node:fs/promises')).readFile(file!);
  expect(bytes.subarray(0, 2).toString()).toBe('PK');
  expect(bytes.length).toBeGreaterThan(1000);
});

test("W3 notifications default to the durable V2 inbox and keep V1 explicit", async ({ page }) => {
  await login(page);
  await page.goto('/admin');
  const v2Response = page.waitForResponse(response => response.url().includes('/v2/notifications?limit=24') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'الإشعارات', exact: true }).click();
  const v2 = await v2Response;
  expect(v2.status()).toBe(200);
  expect((await v2.json()).source).toBe('himma_v2_attention');
  const dialog = page.getByRole('dialog', { name: 'إشعارات المشرف' });
  await expect(dialog.getByText('إشعارات V2', { exact: true })).toBeVisible();
  const dialogBox=await dialog.boundingBox();
  expect(dialogBox?.x).toBeGreaterThanOrEqual(0);
  expect((dialogBox?.x??0)+(dialogBox?.width??0)).toBeLessThanOrEqual(page.viewportSize()!.width);
  const refreshButton=dialog.getByRole('button',{name:'تحديث',exact:true});
  expect((await refreshButton.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  const refreshed = page.waitForResponse(response => response.url().includes('/v2/notifications?limit=24') && response.request().method() === 'GET');
  await refreshButton.click();
  expect((await refreshed).status()).toBe(200);
  await expect(dialog.getByText('إشعارات V2', { exact: true })).toBeVisible();
  await expect(dialog.getByText('أرشيف إشعارات V1', { exact: true })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'الإشعارات', exact: true })).toBeFocused();
});
