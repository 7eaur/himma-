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
  "/admin/v2-review-center",
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
        await expect(page.getByText("جاري تحميل بيانات الطلاب...")).toHaveCount(0, { timeout: 20000 });
        await expect(page.getByText("تعذر تحميل تقدم طلاب V2، ولم تُستخدم أرقام V1 بديلة.")).toHaveCount(0);
        await expect(page.getByText("رمز الدخول", { exact: false })).toHaveCount(0);
        await expect(page.locator("table.data-table th").filter({ hasText: "التقدم" })).toHaveCount(1);
      }
      if (route === "/admin/v2-media") {
        await expect(page.getByText(/الأصول المطلوبة المتاحة لهذا الإصدار/)).toBeVisible({ timeout: 15000 });
      }
      if (route === "/admin/v2-review-center") {
        await expect(page.getByRole("heading", { name: "متابعة القراءة الصوتية" })).toBeVisible();
        const filters = page.getByRole("group", { name: "حالة القراءة" });
        await expect(filters.getByRole("button", { name: "جميع النتائج" })).toHaveAttribute("aria-pressed", "true");
        await expect(filters.getByRole("button", { name: "اكتمل التقييم" })).toBeVisible();
        await expect(filters.getByRole("button", { name: "تحتاج متابعة" })).toBeVisible();
      }
      await expectNoHorizontalOverflow(page);
      await capture(page, viewport.name, route);

      if (route === "/admin/content-preview") {
        const firstQuestion = page.getByTestId("v2-bank-question").first();
        await expect(firstQuestion).toBeVisible({ timeout: 25000 });
        await firstQuestion.getByText("الإجابة ومعيار المراجعة").click();
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
    { route: "/admin/v2-review-center", heading: "متابعة القراءة الصوتية" },
    { route: "/admin/v2-assessments", heading: "متابعة القراءة الصوتية" },
    { route: "/admin/v2-lesson-review", heading: "متابعة القراءة الصوتية" },
    { route: "/admin/v2-media", heading: "الوسائط التعليمية" },
    { route: "/admin/v2-reviewed-recordings", heading: "متابعة القراءة الصوتية" },
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
    if (["/admin/v2-assessments", "/admin/v2-lesson-review", "/admin/v2-reviewed-recordings"].includes(route)) {
      await expect(page).toHaveURL(/\/admin\/v2-review-center$/);
    }
    await expect(page.getByRole("heading", { level: 1, name: heading, exact: true })).toBeVisible();
    if (route === "/admin/v2-review-center") {
      await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
      const filters = page.getByRole("group", { name: "حالة القراءة" });
      await filters.getByRole("button", { name: "تحتاج متابعة" }).click();
      await expect(filters.getByRole("button", { name: "تحتاج متابعة" })).toHaveAttribute("aria-pressed", "true");
      await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
      await filters.getByRole("button", { name: "اكتمل التقييم" }).click();
      await expect(filters.getByRole("button", { name: "اكتمل التقييم" })).toHaveAttribute("aria-pressed", "true");
      await expect(page.getByRole("button", { name: "تحديث النتائج" })).toBeVisible();
    }
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

  await page.getByRole("tab", { name: "الحساب", exact: true }).click();
  await expect(page.getByText(code, { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "إظهار الرمز" }).click();
  await expect(page.getByText(code, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "إخفاء الرمز" }).click();
  await expect(page.getByText(code, { exact: true })).toHaveCount(0);
  await page.getByRole("tab", { name: "نظرة عامة" }).click();
  // Wait for the Router to commit the tab URL before reloading the document.
  await expect(page).toHaveURL(new RegExp(`/admin/students/${id}$`));
  await expect(page.getByTestId("supervisor-v2-overview")).toBeVisible();

  // Simulate an unavailable official V2 read-model. The supervisor must
  // see a bounded error, NEVER a V1 score replacing the current V2 source.
  const v2Route = `**/api/v2/student/admin/students/${id}/home`;
  await page.route(v2Route, route => route.fulfill({
    status: 503, contentType: "application/json", body: '{"detail":"temporary unavailable"}',
  }));
  await page.reload();
  await expect(page.getByRole("alert").filter({ hasText: "تعذر تحميل التقدم الدراسي لهذا الطالب" })).toBeVisible({ timeout: 15000 });
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
  await first.getByText('الإجابة ومعيار المراجعة', { exact: true }).click();
  await expect(first.getByText(/الإجابة الصحيحة:/)).toBeVisible();
  await page.getByRole('combobox', { name: 'القسم', exact: true }).selectOption('L1-01');
  await expect(page.locator('#v2-bank-question-picker option')).toHaveCount(8);
  await expect(page.getByTestId('v2-bank-question')).toHaveCount(1);
  await expect(page.getByTestId('v2-bank-question').first()).toContainText('L1-01-GP-01');
  await expect(page.getByText(/التمهيد:/)).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await capture(page, 'phone-390x844', '/admin/v2-bank-lesson');
  await page.goto('/admin/v2-media');
  await expect(page.getByTestId('v2-media-card')).toHaveCount(12);
  await expect(page.getByText(/87 أصلًا مطابقًا/)).toBeVisible();
  await page.getByRole('combobox', { name: 'نوع الوسيط' }).selectOption('audio');
  await expect(page.getByTestId('v2-media-card')).toHaveCount(12);
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
  // Playwright may discard a navigated-away response body while the
  // notification panel is mounting. Use the same authenticated context for
  // a deterministic source-contract assertion instead of a detached body.
  const inboxSource = await page.request.get('/api/v2/notifications?limit=24');
  expect(inboxSource.status()).toBe(200);
  expect((await inboxSource.json()).source).toBe('himma_v2_attention');
  const dialog = page.getByRole('dialog', { name: 'إشعارات المشرف' });
  await expect(dialog.getByText('إشعارات المشرف', { exact: true })).toBeVisible();
  const dialogBox=await dialog.boundingBox();
  expect(dialogBox?.x).toBeGreaterThanOrEqual(0);
  expect((dialogBox?.x??0)+(dialogBox?.width??0)).toBeLessThanOrEqual(page.viewportSize()!.width);
  const refreshButton=dialog.getByRole('button',{name:'تحديث',exact:true});
  expect((await refreshButton.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  const refreshed = page.waitForResponse(response => response.url().includes('/v2/notifications?limit=24') && response.request().method() === 'GET');
  await refreshButton.click();
  expect((await refreshed).status()).toBe(200);
  await expect(dialog.getByText('إشعارات المشرف', { exact: true })).toBeVisible();
  await expect(dialog.getByText('أرشيف إشعارات V1', { exact: true })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'الإشعارات', exact: true })).toBeFocused();
});


for (const width of [390, 1280]) {
  test(`legacy review bookmarks only show read-only native results at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await login(page);
    const calls: string[] = [];
    page.on("request", request => {
      if (request.method() !== "GET" && /\/api\/v2\/(assessments\/admin|review|retries|review-claims)/.test(request.url())) {
        calls.push(`${request.method()} ${request.url()}`);
      }
    });
    await page.route("**/api/v2/reading/admin/results?*", route => route.fulfill({
      json: {
        items: [{
          job_id: 9876, student_id: 9876, student_name: "طالب فحص القراءة",
          question_id: "TEST-READ", reference: "باب", kind: "word",
          session_kind: "lesson", result: "صحيحة", score_percent: null,
          created_at: "2026-10-28T10:00:00Z", has_audio: true,
        }], total: 1, next_offset: null,
      },
    }));
    for (const old of [
      "/admin/v2-assessments", "/admin/v2-lesson-review",
      "/admin/v2-reviewed-recordings",
    ]) {
      await page.goto(old);
      await expect(page).toHaveURL(/\/admin\/v2-review-center$/);
      await expect(page.getByRole("heading", { name: "متابعة القراءة الصوتية" })).toBeVisible();
      await expect(page.getByText("طالب فحص القراءة")).toBeVisible();
      await expect(page.getByText("باب", { exact: true })).toBeVisible();
      await expect(page.getByRole("button", { name: "تحديث النتائج" })).toBeVisible();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.getByRole("button", { name: "القراءة صحيحة" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "طلب إعادة التسجيل" })).toHaveCount(0);
      await expect(page.getByLabel("تسجيل قراءة طالب فحص القراءة")).toHaveAttribute(
        "src", "/api/v2/reading/admin/jobs/9876/audio",
      );
      await expectNoHorizontalOverflow(page);
      await mkdir(SCREENSHOT_DIR, { recursive: true });
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `native-read-only-${width}-${old.slice(7)}.png`),
      });
    }
    expect(calls).toEqual([]);
  });
}
