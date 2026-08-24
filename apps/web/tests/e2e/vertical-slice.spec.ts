import { test, expect, APIRequestContext } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

/**
 * Login helper: calls API directly and stores cookies in the browser context.
 * This bypasses the UI login form to avoid the 307 redirect cookie issue.
 */
async function loginAsResearcher(request: APIRequestContext, context: import("@playwright/test").BrowserContext) {
  if (!RESEARCHER_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const res = await request.post(`${API_URL}/auth/login`, {
    data: { username: RESEARCHER_USERNAME, password: RESEARCHER_PASSWORD },
  });
  expect(res.status(), "Admin login should return 200").toBe(200);

  // Extract set-cookie header and inject into browser context
  const setCookieHeader = res.headers()["set-cookie"];
  if (setCookieHeader) {
    const cookieMatch = setCookieHeader.match(/access_token=([^;]+)/);
    if (cookieMatch) {
      await context.addCookies([{
        name: "access_token",
        value: cookieMatch[1],
        domain: "localhost",
        path: "/",
        httpOnly: true,
        sameSite: "Lax",
        secure: false,
      }]);
    }
  }
}

async function loginAsStudent(request: APIRequestContext, context: import("@playwright/test").BrowserContext, accessCode: string) {
  const res = await request.post(`${API_URL}/auth/student-login`, {
    data: { access_code: accessCode },
  });
  expect(res.status(), `Student login with code ${accessCode} should return 200`).toBe(200);

  const setCookieHeader = res.headers()["set-cookie"];
  if (setCookieHeader) {
    const cookieMatch = setCookieHeader.match(/access_token=([^;]+)/);
    if (cookieMatch) {
      await context.addCookies([{
        name: "access_token",
        value: cookieMatch[1],
        domain: "localhost",
        path: "/",
        httpOnly: true,
        sameSite: "Lax",
        secure: false,
      }]);
    }
  }
}

test.describe("Full Vertical Slice — B02 Lifecycle Gate", () => {
  test("Admin creates student → Student takes pretest → Admin grades audio", async ({
    page,
    context,
    request,
  }) => {
    // ── Step 1: Login as Admin via API ──────────────────────────────────────
    await loginAsResearcher(request, context);

    // ── Step 2: Navigate to Create Student ──────────────────────────────────
    await page.goto("/admin/students/new");
    await expect(page).not.toHaveURL(/login/, { timeout: 5000 });

    const studentName = `E2E Student ${Date.now()}`;
    await page.getByTestId("input-student-name").fill(studentName);
    await expect(page.getByTestId("input-student-grade")).toHaveValue("3");
    await expect(page.getByTestId("input-student-grade")).toBeDisabled();
    await page.getByTestId("submit-create-student").click();

    // ── Step 3: Extract access code ──────────────────────────────────────────
    const codeEl = page.getByTestId("student-access-code");
    await expect(codeEl).toBeVisible({ timeout: 10000 });
    const accessCode = (await codeEl.textContent())?.trim();
    expect(accessCode, "Access code should be present").toBeTruthy();
    console.log("Created student and captured one-time access code");

    // ── Step 4: Clear admin session ──────────────────────────────────────────
    await context.clearCookies();

    // ── Step 5: Login as Student ──────────────────────────────────────────────
    await loginAsStudent(request, context, accessCode!);
    await page.goto("/student");
    await expect(page.getByText(/أهلاً|مرحباً/)).toBeVisible({ timeout: 5000 });

    // ── Step 6: Start Pretest ─────────────────────────────────────────────────
    const startBtn = page.getByRole("button", { name: /ابدأ|اختبار/ });
    await startBtn.click();
    await expect(page).toHaveURL(/\/student\/session\/\d+/, { timeout: 10000 });
    const sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    expect(sessionId, "Session id should be present in the URL").toBeTruthy();

    const sessionRoot = page.getByTestId("assessment-session");
    const progressCounter = page.getByTestId("assessment-progress");
    const waitForActionablePhase = async () => {
      await expect(sessionRoot).toHaveAttribute(
        "data-phase",
        /^(question|recording|waiting_audio_review|done|error)$/,
        { timeout: 15000 },
      );
      const currentPhase = await sessionRoot.getAttribute("data-phase");
      if (currentPhase === "error") {
        const message = (await sessionRoot.textContent())?.trim() || "Unknown assessment error";
        throw new Error(`Assessment entered an error state: ${message}`);
      }
      return currentPhase;
    };

    await waitForActionablePhase();

    // ── Step 7: Answer questions (up to 30) ──────────────────────────────────
    let questionsAnswered = 0;
    const maxQuestions = 30;

    while (questionsAnswered < maxQuestions) {
      const currentPhase = await waitForActionablePhase();
      if (currentPhase === "waiting_audio_review" || currentPhase === "done") break;

      // Check for audio question
      const recordBtn = page.getByRole("button", { name: "ابدأ التسجيل" });

      if (currentPhase === "recording") {
        // Audio question: use fake media stream (configured in playwright.config.ts)
        await expect(recordBtn).toBeVisible({ timeout: 5000 });
        await recordBtn.click();
        await page.waitForTimeout(2500); // record 2.5s of fake audio
        const stopBtn = page.getByRole("button", { name: /إيقاف|أوقف/ }).first();
        await stopBtn.click();
        await page.waitForTimeout(500);
        const submitBtn = page.getByRole("button", { name: /إرسال التسجيل|أرسل/ }).first();
        await expect(submitBtn).toBeEnabled({ timeout: 5000 });
        await submitBtn.click();
      } else {
        // MCQ question: click first visible option
        const optionBtns = page.locator(".assessment-option");
        await expect(optionBtns.first()).toBeVisible({ timeout: 5000 });
        await optionBtns.first().click({ timeout: 5000 });
        await page.getByRole("button", { name: "تأكيد الإجابة" }).click();
      }

      questionsAnswered++;
      if (questionsAnswered < maxQuestions) {
        await expect(progressCounter).toContainText(`${questionsAnswered}/`, { timeout: 15000 });
        await waitForActionablePhase();
      }
      if (questionsAnswered === 1) {
        await page.reload();
        await expect(page).toHaveURL(new RegExp(`/student/session/${sessionId}`));
        await waitForActionablePhase();
        await expect(progressCounter).toContainText("1/", { timeout: 15000 });
      }
    }

    console.log(`Answered ${questionsAnswered} questions`);

    // ── Step 8: Verify completion ─────────────────────────────────────────────
    await expect(page.getByText("في انتظار المراجعة")).toBeVisible({ timeout: 15000 });

    // ── Step 9: Admin reviews audio ───────────────────────────────────────────
    await context.clearCookies();
    await loginAsResearcher(request, context);
    await page.goto("/admin/audio-review");
    await expect(page).not.toHaveURL(/login/, { timeout: 5000 });

    const startReview = page.getByRole("button", { name: "بدء المراجعة" });
    await expect(startReview.first()).toBeVisible({ timeout: 15000 });
    let reviewed = 0;
    while (await startReview.count()) {
      await startReview.first().click();
      await page.getByRole("button", { name: "حفظ التقييم" }).click();
      await expect(page.getByRole("button", { name: "حفظ التقييم" })).toHaveCount(0);
      reviewed++;
    }
    expect(reviewed).toBeGreaterThan(0);

    // ── Step 10: Student receives the final result after review ───────────────
    await context.clearCookies();
    await loginAsStudent(request, context, accessCode!);
    await page.goto(`/student/session/${sessionId}`);
    await expect(page.getByText("أحسنت")).toBeVisible({ timeout: 15000 });

    // ── Step 11: Verify student list updated ─────────────────────────────────
    await context.clearCookies();
    await loginAsResearcher(request, context);
    await page.goto("/admin/students");
    await expect(page.getByText(studentName)).toBeVisible({ timeout: 5000 });

    console.log("✓ Vertical slice complete");
  });
});
