import { expect, test } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

// Synthetic, text-only reading state. Browser, student session, RTL UI,
// transport errors and responsive layout are real. No child voice or Azure
// credentials leave the app; no academic answer POST is performed.
function assessment(advanced: boolean) {
  return {
    session: {
      session_id: 777, kind: "pretest", state: "answering",
      progress: { answered: advanced ? 6 : 5, total: 30 },
    },
    interaction: {
      question: advanced ? {
        question_id: "V2-PRE-Q07", role: "pretest", interaction: "choose_one",
        prompt: "اختر الكلمة المناسبة.", stimulus: { text: null, media: [] },
        options: [
          { id: "first", text: "كتاب", media: [] },
          { id: "second", text: "باب", media: [] },
        ], hint: null,
      } : {
        question_id: "V2-PRE-Q06", role: "pretest", interaction: "read_aloud",
        prompt: "اقرأ الحرف المعروض.", stimulus: { text: "لَ", media: [] },
        options: [], hint: null,
      },
      media: {},
      progress: {
        index: advanced ? 7 : 6, total: 30, stage: "pretest",
      },
      attempts: 0,
      reading_job_id: advanced ? null : 88,
    },
    summary: { pending_review: advanced ? 0 : 1 },
  };
}

for (const width of [390, 1280]) {
  test(`native reading retains one recorded attempt after an Azure outage at ${width}px`, async ({ page, request }) => {
    test.setTimeout(150000);
    if (!PASSWORD) throw new Error("E2E researcher credentials are required");

    const staff = await request.post(`${API_URL}/auth/login`, {
      data: { username: USERNAME, password: PASSWORD },
    });
    expect(staff.status()).toBe(200);
    const created = await request.post(`${API_URL}/researcher/students`, {
      data: { full_name: `طالب فحص صوت اصطناعي ${width} ${Date.now()}`, grade_level: 3 },
    });
    expect(created.status()).toBe(201);
    const accessCode = (await created.json()).access_code as string;
    await page.goto("/student/login");
    await page.getByTestId("input-access-code").fill(accessCode);
    await page.getByTestId("student-login-submit").click();
    await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
    await page.setViewportSize({ width, height: 860 });

    let retriedSavedBytes = false;
    let reads = 0;
    let replayRequests = 0;
    const unexpectedWrites: string[] = [];
    page.on("request", req => {
      if (req.method() !== "GET" && /\/api\/v2\/.*(?:\/recording|\/rerecord|\/answers)$/.test(req.url())) {
        unexpectedWrites.push(`${req.method()} ${req.url()}`);
      }
    });

    await page.route("**/api/v2/assessments/sessions/777", route =>
      route.fulfill({ json: assessment(retriedSavedBytes) }),
    );
    await page.route("**/api/v2/reading/jobs/88", route => {
      reads += 1;
      // Reproduce an interrupted request on a narrow phone browser.
      if (width === 390 && reads === 1) return route.abort("failed");
      return route.fulfill({
        json: retriedSavedBytes
          ? { state: "completed", message: "تم تسجيل قراءتك.", retry_required: false }
          : { state: "unavailable",
              message: "تعذر التحقق الآن. تسجيلك محفوظ؛ حاول المتابعة بعد قليل.",
              retry_required: false },
      });
    });
    await page.route("**/api/v2/reading/jobs/88/retry-analysis", route => {
      expect(route.request().method()).toBe("POST");
      replayRequests += 1;
      retriedSavedBytes = true;
      return route.fulfill({ json: {
        job_id: 88, state: "processing",
        message: "نستمع إلى تسجيلك المحفوظ مرة أخرى...",
      } });
    });

    await page.goto("/student/assessment-v2/777");
    const player = page.getByTestId("v2-interaction-player");
    const retry = page.getByRole("button", { name: "إعادة التحقق من التسجيل المحفوظ" });
    await expect(retry).toBeVisible({ timeout: 18000 });
    await expect(player).toContainText("6 من 30");
    await expect(page.getByRole("button", { name: "بدء التسجيل" })).toHaveCount(0);
    await expect(page.getByText(/تلميح:/)).toHaveCount(0);
    await expect(page.getByText("المشرف")).toHaveCount(0);

    // Refresh must restore the server-owned job without uploading a new take.
    await page.reload();
    await expect(retry).toBeVisible({ timeout: 18000 });
    await retry.click();
    await expect(page.getByText("اختر الكلمة المناسبة.")).toBeVisible({ timeout: 15000 });
    await expect(player).toContainText("7 من 30");
    expect(replayRequests).toBe(1);
    expect(unexpectedWrites).toEqual([]);
    expect(reads).toBeGreaterThanOrEqual(3);
    const widths = await page.evaluate(() => ({
      document: document.documentElement.scrollWidth, viewport: innerWidth,
    }));
    expect(widths.document, JSON.stringify(widths)).toBeLessThanOrEqual(widths.viewport + 1);
  });
}
