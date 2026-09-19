import { expect, test, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const SCREENSHOT_DIR = path.join(process.cwd(), "playwright-report", "screenshots", "ux-visual-qa");

const DASHBOARD_VIEWPORTS = [
  { name: "phone-320", width: 320, height: 720 },
  { name: "phone-360", width: 360, height: 800 },
  { name: "phone-390", width: 390, height: 844 },
  { name: "phone-430", width: 430, height: 932 },
  { name: "tablet-768", width: 768, height: 1024 },
  { name: "desktop-1440", width: 1440, height: 1000 },
] as const;

async function loginSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

async function createStudent(page: Page, request: APIRequestContext, context: BrowserContext, label: string) {
  await loginSupervisor(request, context);
  await page.goto("/admin/students/new");
  await expect(page.getByTestId("input-student-name")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("input-student-name").fill(`${label} ${Date.now()}`);
  await page.getByTestId("submit-create-student").click();
  const code = page.getByTestId("student-access-code");
  await expect(code).toBeVisible({ timeout: 10000 });
  const accessCode = (await code.textContent())?.trim() ?? "";
  expect(accessCode).toMatch(/^\d{6}$/);
  await context.clearCookies();
  return accessCode;
}

async function loginStudent(request: APIRequestContext, context: BrowserContext, accessCode: string) {
  const response = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
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

async function answerVisibleChoice(page: Page) {
  const imageGroup = page.getByTestId("image-options");
  const sequenceImageGroup = page.getByTestId("sequence-image-options");
  const sequenceBoard = page.getByTestId("sequence-board");
  const confirm = page.getByRole("button", { name: "تأكيد والمتابعة" });

  if (await imageGroup.count()) {
    await imageGroup.getByRole("button").first().click();
  } else if (await sequenceImageGroup.count()) {
    while (!(await confirm.isEnabled())) {
      const available = sequenceImageGroup.getByRole("button").filter({ visible: true });
      const count = await available.count();
      expect(count, "Sequence should still expose an available choice until the required order is complete").toBeGreaterThan(0);
      await available.first().click();
    }
  } else {
    const options = page.locator('button[aria-pressed="false"]');
    if (await options.count()) {
      await options.first().click();
    } else if (await sequenceBoard.count()) {
      while (!(await confirm.isEnabled())) {
        const candidates = page.locator("main section button");
        let clicked = false;
        for (let index = 0; index < await candidates.count(); index += 1) {
          const candidate = candidates.nth(index);
          const text = ((await candidate.textContent()) ?? "").trim();
          if (!(await candidate.isVisible()) || !(await candidate.isEnabled())) continue;
          if (/^(استمع|تأكيد والمتابعة|إعادة الترتيب|إعادة التسجيل|إرسال التسجيل)$/u.test(text)) continue;
          await candidate.click();
          clicked = true;
          break;
        }
        expect(clicked, "Ordered question should expose another selectable item until the required order is complete").toBeTruthy();
      }
    } else {
      const candidates = page.locator("main section button");
      for (let index = 0; index < await candidates.count() && !(await confirm.isEnabled()); index += 1) {
        const candidate = candidates.nth(index);
        const text = ((await candidate.textContent()) ?? "").trim();
        if (!(await candidate.isVisible()) || !(await candidate.isEnabled())) continue;
        if (/^(استمع|تأكيد والمتابعة|إعادة الترتيب|إعادة التسجيل|إرسال التسجيل)$/u.test(text)) continue;
        await candidate.click();
      }
    }
  }
  await expect(confirm).toBeEnabled();
  await confirm.click();
}

test.describe("Himma UX system visual QA regression", () => {
  test.beforeEach(async () => {
    await mkdir(SCREENSHOT_DIR, { recursive: true });
  });

  test("student dashboard follows the approved semantic hierarchy across the viewport matrix", async ({ page, context, request }) => {
    test.setTimeout(120000);
    const accessCode = await createStudent(page, request, context, "طالب ترتيب الرحلة");
    await loginStudent(request, context, accessCode);

    for (const viewport of DASHBOARD_VIEWPORTS) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/student");
      await expect(page.getByTestId("student-home")).toBeVisible({ timeout: 10000 });
      await expectNoHorizontalOverflow(page);

      const identity = page.getByTestId("student-identity");
      const summary = page.getByTestId("student-status-summary");
      const nextAction = page.getByTestId("student-next-action");
      const journey = page.getByTestId("student-journey-overview");
      const levelProgress = page.getByTestId("student-level-progress-summary");
      const badges = page.getByTestId("student-badges");
      const results = page.getByTestId("student-results");

      for (const locator of [identity, summary, nextAction, journey, levelProgress, badges, results]) {
        await expect(locator).toBeVisible();
      }

      const boxes = await Promise.all([identity, summary, nextAction, journey, levelProgress, badges, results].map((locator) => locator.boundingBox()));
      for (let index = 1; index < boxes.length; index += 1) {
        expect(boxes[index]?.y ?? 0).toBeGreaterThan((boxes[index - 1]?.y ?? 0) + (boxes[index - 1]?.height ?? 0) - 2);
      }

      await expect(page.getByTestId("student-journey-step")).toHaveCount(5);
      await expect(page.getByTestId("student-journey-step").nth(0)).toContainText("الاختبار القبلي");
      await expect(page.getByTestId("student-journey-step").nth(1)).toContainText("مستوى التعلم");
      await expect(page.getByTestId("student-journey-step").nth(2)).toContainText("الأنشطة الأساسية");
      await expect(page.getByTestId("student-journey-step").nth(3)).toContainText("التقوية");
      await expect(page.getByTestId("student-journey-step").nth(4)).toContainText("الاختبار البعدي");

      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-student-home.png`), fullPage: true });
    }
  });

  test("mobile assessment keeps title, image choices, and sequence choices compact", async ({ page, context, request }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 390, height: 844 });
    const accessCode = await createStudent(page, request, context, "طالب فحص السؤال");
    await loginStudent(request, context, accessCode);

    const start = await request.post(`${API_URL}/assessment/start`, { data: { session_type: "pretest" } });
    expect([200, 409]).toContain(start.status());
    const payload = await start.json().catch(() => null);
    let sessionId = payload?.id ?? payload?.session_id;
    if (!sessionId) {
      await page.goto("/student");
      await page.getByTestId("student-primary-action").click();
      sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    }
    expect(sessionId).toBeTruthy();

    await page.goto(`/student/session/${sessionId}`);
    for (let index = 0; index < 10; index += 1) {
      await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "question", { timeout: 15000 });
      await expectNoHorizontalOverflow(page);

      const title = page.getByTestId("assessment-session").locator("main section h1").first();
      const titleSize = await title.evaluate((element) => Number.parseFloat(getComputedStyle(element).fontSize));
      expect(titleSize).toBeLessThanOrEqual(22);

      if (index === 4) {
        const imageButtons = page.getByTestId("image-options").getByRole("button");
        await expect(imageButtons).toHaveCount(4);
        const firstImage = imageButtons.first().locator("img");
        await expect(firstImage).toHaveAttribute("loading", "eager");
        await expect(firstImage).toHaveAttribute("src", /\/_next\/image\?/);
        const firstBox = await imageButtons.first().boundingBox();
        expect(firstBox?.height ?? 999).toBeLessThanOrEqual(190);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, "phone-390-assessment-image-options.png"), fullPage: true });
      }

      if (index === 9) {
        const sequenceButtons = page.getByTestId("sequence-image-options").getByRole("button");
        expect(await sequenceButtons.count()).toBeGreaterThan(0);
        const firstImage = sequenceButtons.first().locator("img");
        await expect(firstImage).toHaveAttribute("loading", "eager");
        await expect(firstImage).toHaveAttribute("src", /\/_next\/image\?/);
        const firstBox = await sequenceButtons.first().boundingBox();
        expect(firstBox?.height ?? 999).toBeLessThanOrEqual(190);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, "phone-390-assessment-sequence.png"), fullPage: true });
      }

      await answerVisibleChoice(page);
    }
  });

  test("audio review decision workflow is visually stable on phone and desktop", async ({ page, context, request }) => {
    await loginSupervisor(request, context);
    const submission = {
      id: 99101,
      storage_key: "tests/ux-visual-review.webm",
      status: "uploaded",
      submitted_at: "2026-09-17T18:00:00Z",
      student_id: 991,
      student_name: "طالب فحص بصري",
      session_type: "pretest",
      item_title: "قراءة جملة",
      expected_reading_text: "يَقْرَأُ سَالِمٌ كِتَابًا.",
    };

    await page.route("**/api/review/pending-audio*", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([submission]) });
    });

    for (const viewport of [
      { name: "phone-390", width: 390, height: 844 },
      { name: "desktop-1440", width: 1440, height: 1000 },
    ]) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/admin/audio-review?submission_id=99101");
      const workspace = page.getByTestId("audio-review-queue");
      const selector = page.getByTestId("audio-review-selector");
      await expect(workspace).toBeVisible();
      await expect(selector).toBeVisible();
      await expect(selector).toHaveValue("99101");
      await expect(page.getByText("اختر الطالب والتسجيل")).toBeVisible();
      await expectNoHorizontalOverflow(page);

      const form = page.getByTestId("audio-review-form");
      await expect(form).toBeVisible();
      await expect(form.getByRole("heading", { name: "طالب فحص بصري" })).toBeVisible();
      await expect(form.getByText("يَقْرَأُ سَالِمٌ كِتَابًا.")).toBeVisible();
      await expect(form.getByRole("button", { name: /تشغيل التسجيل/ })).toBeVisible();
      await expect(form.getByTestId("audio-review-meta")).toBeVisible();
      await expect(form.getByText("بانتظار المراجعة")).toBeVisible();

      const approveDecision = form.getByRole("button", { name: "اعتماد القراءة", exact: true });
      const rerecordDecision = form.getByRole("button", { name: "طلب إعادة تسجيل", exact: true });
      await expect(approveDecision).toBeVisible();
      await expect(rerecordDecision).toBeVisible();
      await expect(approveDecision).toHaveAttribute("aria-pressed", "true");

      const scoreFields = form.getByTestId("audio-review-score-fields");
      await expect(scoreFields).toBeVisible();
      await expect(scoreFields.getByLabel("إجمالي الوحدات")).toHaveValue("10");
      await expect(scoreFields.getByLabel("الحذف")).toHaveValue("0");
      await expect(scoreFields.getByLabel("الاستبدال")).toHaveValue("0");
      await expect(scoreFields.getByLabel("الإضافة")).toHaveValue("0");

      const notesToggle = form.getByRole("button", { name: /إضافة ملاحظات/ });
      await expect(notesToggle).toHaveAttribute("aria-expanded", "false");
      await expect(form.getByTestId("audio-review-notes")).toHaveCount(0);

      const approveBox = await approveDecision.boundingBox();
      const rerecordBox = await rerecordDecision.boundingBox();
      expect(approveBox?.height ?? 0).toBeGreaterThanOrEqual(56);
      expect(rerecordBox?.height ?? 0).toBeGreaterThanOrEqual(56);

      const evidenceBox = await form.getByTestId("audio-review-evidence").boundingBox();
      const assessmentBox = await form.getByTestId("audio-review-assessment").boundingBox();
      expect(evidenceBox).toBeTruthy();
      expect(assessmentBox).toBeTruthy();
      if (viewport.width >= 900) {
        expect(Math.abs((evidenceBox?.y ?? 0) - (assessmentBox?.y ?? 0))).toBeLessThanOrEqual(2);
      } else {
        expect(assessmentBox?.y ?? 0).toBeGreaterThan((evidenceBox?.y ?? 0) + (evidenceBox?.height ?? 0) - 2);
      }

      const workspaceBox = await workspace.boundingBox();
      const selectorBox = await selector.boundingBox();
      const formBox = await form.boundingBox();
      expect(workspaceBox).toBeTruthy();
      expect(selectorBox).toBeTruthy();
      expect(formBox).toBeTruthy();
      expect(formBox?.y ?? 0).toBeGreaterThan((selectorBox?.y ?? 0));
      expect((formBox?.x ?? 0) + (formBox?.width ?? 0)).toBeLessThanOrEqual((workspaceBox?.x ?? 0) + (workspaceBox?.width ?? 0) + 1);

      const pageHeight = await page.evaluate(() => document.documentElement.scrollHeight);
      expect(pageHeight).toBeLessThanOrEqual(viewport.width < 900 ? 1800 : 1100);

      await expectNoHorizontalOverflow(page);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-audio-review-decision.png`), fullPage: true });

      await notesToggle.click();
      await expect(notesToggle).toHaveAttribute("aria-expanded", "true");
      const notes = form.getByTestId("audio-review-notes");
      await expect(notes).toBeVisible();
      await expect(notes.getByLabel("ملاحظات النطق")).toBeVisible();
      await expect(notes.getByLabel("ملاحظات الطلاقة")).toBeVisible();
      await expectNoHorizontalOverflow(page);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-audio-review-notes-open.png`), fullPage: true });
      await notesToggle.click();
    }
  });
});
