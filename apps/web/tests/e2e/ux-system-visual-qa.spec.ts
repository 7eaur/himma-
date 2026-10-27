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
      const journey = page.getByTestId("student-journey-steps");
      const progress = page.getByTestId("student-v2-progress");
      const levelProgress = page.getByTestId("student-journey-status");

      for (const locator of [identity, summary, nextAction, progress, journey, levelProgress]) {
        await expect(locator).toBeVisible();
      }
      // V1 achievements are never shown as V2 rewards.
      await expect(page.getByTestId("student-badges")).toHaveCount(0);

      await expect(page.getByTestId("student-results")).toHaveCount(0);
      // No active retry means no empty card/extra vertical space.
      await expect(page.getByTestId("v2-active-retry-tasks")).toHaveCount(0);
      await expect(page.getByTestId("level-journey")).toHaveCount(0);

      const boxes = await Promise.all([identity, nextAction, progress, journey].map((locator) => locator.boundingBox()));
      for (let index = 1; index < boxes.length; index += 1) {
        expect(boxes[index]?.y ?? 0).toBeGreaterThan((boxes[index - 1]?.y ?? 0) + (boxes[index - 1]?.height ?? 0) - 2);
      }

      await expect(page.getByTestId("student-journey-step")).toHaveCount(3);
      await expect(page.getByTestId("student-journey-step").nth(0)).toContainText("الاختبار القبلي");
      await expect(page.getByTestId("student-journey-step").nth(1)).toContainText("رحلة الدروس");
      await expect(page.getByTestId("student-journey-step").nth(2)).toContainText("الاختبار البعدي");

      if (viewport.name === "phone-390") {
        const journeyBoxes = await page.getByTestId("student-journey-step").evaluateAll((nodes) =>
          nodes.map((node) => {
            const rect = node.getBoundingClientRect();
            return { x: rect.x, y: rect.y };
          }),
        );
        for (let index = 1; index < journeyBoxes.length; index += 1) {
          expect(journeyBoxes[index].y).toBeGreaterThan(journeyBoxes[index - 1].y);
        }
        const pageHeight = await page.evaluate(() => document.documentElement.scrollHeight);
        expect(pageHeight).toBeLessThanOrEqual(1650);
      }

      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-student-home.png`), fullPage: true });
    }
  });

  test("student dashboard reveals cross-session V2 rewrite task only when requested", async ({ page, context, request }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 390, height: 844 });
    const accessCode = await createStudent(page, request, context, "طالب مراجعة القراءة");
    await loginStudent(request, context, accessCode);
    // Simulate preview/current-action unavailability. A previously assigned
    // human-review retry must remain visible and actionable regardless.
    await page.route("**/api/v2/assessments/current-action", async (route) => {
      await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"preview temporarily unavailable"}' });
    });
    await page.route(/\/api\/v2\/retries\/student\/tasks(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [{
          task_id: 108, kind: "lesson", session_id: 99,
          question_id: "L2-01-GP-01", request_kind: "rewrite",
          status: "requested", reason: "أعد كتابة الإجابة بوضوح حتى يتمكن المشرف من مراجعتها",
          prompt: "اكتب الكلمة المطلوبة مرة أخرى",
        }] }),
      });
    });
    await page.goto("/student");
    await expect(page.getByTestId("student-home")).toBeVisible();
    const tasks = page.getByTestId("v2-active-retry-tasks");
    await expect(tasks).toBeVisible({ timeout: 15000 });
    await expect(tasks).toContainText("أعد كتابة الإجابة بوضوح");
    await expect(tasks.getByLabel("إجابتك الجديدة")).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("student retry task recovers after a transient offline failure", async ({ page, context, request }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 390, height: 844 });
    const accessCode = await createStudent(page, request, context, "طالب يتابع بعد انقطاع");
    await loginStudent(request, context, accessCode);
    let connected = false;
    await page.route("**/api/v2/assessments/current-action", async (route) => {
      await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"preview unavailable"}' });
    });
    await page.route(/\/api\/v2\/retries\/student\/tasks(?:\?.*)?$/, async (route) => {
      await route.fulfill(connected
        ? { status: 200, contentType: "application/json", body: JSON.stringify({ items: [{
            task_id: 509, kind: "lesson", session_id: 77, question_id: "L2-01-GP-01",
            request_kind: "rewrite", status: "requested", reason: "أعد الكتابة بعد عودة الاتصال",
            prompt: "اكتب النص مرة أخرى",
          }] })}
        : { status: 503, contentType: "application/json", body: '{"detail":"network unavailable"}' });
    });
    const initialFailure = page.waitForResponse((response) =>
      response.url().includes("/v2/retries/student/tasks") && response.status() === 503,
    );
    await page.goto("/student");
    await initialFailure;
    await expect(page.getByTestId("student-home")).toBeVisible();
    await expect(page.getByTestId("v2-active-retry-tasks")).toHaveCount(0);
    connected = true;
    await page.evaluate(() => window.dispatchEvent(new Event("online")));
    const tasks = page.getByTestId("v2-active-retry-tasks");
    await expect(tasks).toBeVisible({ timeout: 15000 });
    await expect(tasks).toContainText("أعد الكتابة بعد عودة الاتصال");
    await expect(tasks.getByLabel("إجابتك الجديدة")).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("student resumes private staged rerecord after reload without uploading again", async ({ page, context, request }) => {
    test.setTimeout(120000);
    await page.setViewportSize({ width: 390, height: 844 });
    const accessCode = await createStudent(page, request, context, "طالب استئناف القراءة");
    await loginStudent(request, context, accessCode);
    const staged = {
      audio_storage_key: "audio/test-owned-fixture/staged.webm",
      audio_file_size: 1024, audio_mime_type: "audio/webm",
      audio_duration_seconds: 4,
    };
    let uploadedAgain = false;
    let acceptedAnswer: Record<string, unknown> | null = null;
    let completed = false;

    // The task belongs to the student's real authenticated history, even if
    // a separately loaded journey preview is disabled in this environment.
    await page.route("**/api/v2/assessments/current-action", async (route) => {
      await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"preview temporarily unavailable"}' });
    });
    await page.route(/\/api\/v2\/retries\/student\/tasks(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ items: [{
          task_id: 456, kind: "lesson", session_id: 777,
          question_id: "L1-05-GP-02", request_kind: "rerecord",
          status: completed ? "submitted" : "requested",
          reason: "إعادة القراءة بعد ضعف التسجيل السابق",
          prompt: "اقرأ المقطع المعروض", staged_audio: completed ? null : staged,
        }] }),
      });
    });
    await page.route("**/api/v2/retries/student/tasks/456/recording", async (route) => {
      uploadedAgain = true;
      await route.fulfill({ status: 409, contentType: "application/json", body: '{"detail":"unnecessary reupload"}' });
    });
    await page.route("**/api/v2/retries/student/tasks/456/submit", async (route) => {
      acceptedAnswer = route.request().postDataJSON() as Record<string, unknown>;
      completed = true;
      await route.fulfill({
        status: 200, contentType: "application/json",
        body: '{"status":"submitted","task_id":456,"awaiting_human_review":true}',
      });
    });
    await page.goto("/student");
    const tasks = page.getByTestId("v2-active-retry-tasks");
    await expect(tasks).toBeVisible({ timeout: 15000 });
    await expect(tasks).toContainText("التسجيل السابق محفوظ في الخدمة");
    const submit = tasks.getByRole("button", { name: "إرسال الإجابة الجديدة للمراجعة" });
    await expect(submit).toBeEnabled();
    await submit.click();
    await expect(tasks).toContainText("وصلت إجابتك الجديدة");
    expect(uploadedAgain).toBe(false);
    expect(acceptedAnswer).toMatchObject({ ...staged, submit_key: expect.any(String) });
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

  test("review workspace remains usable from an old bookmark on phone and desktop", async ({ page, context, request }) => {
    await loginSupervisor(request, context);
    for (const viewport of [
      { name: "phone-390", width: 390, height: 844 },
      { name: "desktop-1440", width: 1440, height: 1000 },
    ]) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto("/admin/audio-review?submission_id=99101");
      await expect(page).toHaveURL(/\/admin\/v2-assessments$/);
      await expect(page.getByRole("heading", { name: "الاختبارات والتسكين" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "مراجعة القراءة والكتابة" })).toBeVisible();
      await expectNoHorizontalOverflow(page);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-assessment-review.png`), fullPage: true });
    }
  });
});
