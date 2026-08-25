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

test.describe("Full Vertical Slice — Stage 2 Closure Gate", () => {
  test("Admin creates student → pretest/review → assigned core path → researcher sees 10/10", async ({
    page,
    context,
    request,
  }) => {
    test.setTimeout(180000);

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
    const studentId = page.url().match(/\/admin\/students\/(\d+)/)?.[1];
    expect(studentId, "Student id should be present in the URL").toBeTruthy();

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

    // ── Step 7: Answer the exact 30-question pretest ─────────────────────────
    let questionsAnswered = 0;
    const maxQuestions = 30;

    while (questionsAnswered < maxQuestions) {
      const currentPhase = await waitForActionablePhase();
      if (currentPhase === "waiting_audio_review" || currentPhase === "done") break;

      const recordBtn = page.getByRole("button", { name: "ابدأ التسجيل" });
      if (currentPhase === "recording") {
        await expect(recordBtn).toBeVisible({ timeout: 5000 });
        await recordBtn.click();
        await page.waitForTimeout(2500);
        const stopBtn = page.getByRole("button", { name: /إيقاف|أوقف/ }).first();
        await stopBtn.click();
        await page.waitForTimeout(500);
        const submitBtn = page.getByRole("button", { name: /إرسال التسجيل|أرسل/ }).first();
        await expect(submitBtn).toBeEnabled({ timeout: 5000 });
        await submitBtn.click();
      } else {
        const optionBtns = page.locator(".assessment-option");
        await expect(optionBtns.first()).toBeVisible({ timeout: 5000 });
        await optionBtns.first().click({ timeout: 5000 });
        await page.getByRole("button", { name: "تأكيد الإجابة" }).click();
      }

      questionsAnswered++;
      if (questionsAnswered < maxQuestions) {
        await waitForActionablePhase();
        await expect(progressCounter).toContainText(`${questionsAnswered}/`, { timeout: 15000 });
      }
      if (questionsAnswered === 1) {
        await page.reload();
        await expect(page).toHaveURL(new RegExp(`/student/session/${sessionId}`));
        await waitForActionablePhase();
        await expect(progressCounter).toContainText("1/", { timeout: 15000 });
      }
    }

    expect(questionsAnswered).toBe(30);
    await expect(page.getByText("في انتظار المراجعة")).toBeVisible({ timeout: 15000 });

    // ── Step 8: Admin reviews all pretest audio ───────────────────────────────
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

    // ── Step 9: Student receives result and assigned level ────────────────────
    await context.clearCookies();
    await loginAsStudent(request, context, accessCode!);
    await page.goto(`/student/session/${sessionId}`);
    await expect(page.getByText("أحسنت")).toBeVisible({ timeout: 15000 });

    // ── Step 10: Start the ten core learning activities ───────────────────────
    await page.goto("/student");
    const learningButton = page.getByRole("button", { name: /ابدأ أنشطة مستواك|متابعة الأنشطة/ });
    await expect(learningButton).toBeEnabled({ timeout: 10000 });
    await learningButton.click();
    await expect(page).toHaveURL(/\/student\/activity\/\d+/, { timeout: 10000 });

    const activityRoot = page.getByTestId("activity-session");
    const activityProgress = page.getByTestId("activity-progress");
    await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });

    // Reload once to prove the learning path resumes from its durable session.
    await page.reload();
    await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });

    let learningInteractions = 0;
    while ((await activityRoot.getAttribute("data-phase")) !== "done") {
      learningInteractions++;
      expect(learningInteractions, "Core path should terminate").toBeLessThan(100);

      const gapButton = page.getByRole("button", { name: "متابعة دون احتساب هذه الجولة" });
      if (await gapButton.count()) {
        await gapButton.click();
      } else {
        const verifyButton = page.getByRole("button", { name: "تحقق وتابع" });
        const recordButton = page.getByRole("button", { name: "ابدأ القراءة" });

        if (await recordButton.count()) {
          await recordButton.click();
          await page.waitForTimeout(700);
          await page.getByRole("button", { name: /إيقاف التسجيل/ }).click();
          await expect(page.getByRole("button", { name: "حفظ القراءة والمتابعة" })).toBeEnabled({ timeout: 5000 });
          await page.getByRole("button", { name: "حفظ القراءة والمتابعة" }).click();
        } else {
          const optionButtons = activityRoot.locator("button[aria-pressed]");
          await expect(optionButtons.first()).toBeVisible({ timeout: 5000 });
          const optionCount = await optionButtons.count();
          for (let index = 0; index < optionCount; index++) {
            await optionButtons.nth(index).click();
            if (await verifyButton.isEnabled()) break;
          }
          await expect(verifyButton).toBeEnabled({ timeout: 3000 });
          await verifyButton.click();
        }
      }

      await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });
    }

    await expect(page.getByText("أحسنت، أكملت أنشطة مستواك")).toBeVisible({ timeout: 15000 });
    await expect(activityProgress).toContainText("10/10");

    // ── Step 11: Researcher sees 10/10 and can enable posttest ────────────────
    await context.clearCookies();
    await loginAsResearcher(request, context);
    await page.goto(`/admin/students/${studentId}`);
    await expect(page.getByText("10 من 10")).toBeVisible({ timeout: 10000 });
    const enablePosttest = page.getByRole("button", { name: "إتاحة الاختبار البعدي" });
    await expect(enablePosttest).toBeEnabled();

    // ── Step 12: Verify student list remains intact ───────────────────────────
    await page.goto("/admin/students");
    await expect(page.getByText(studentName)).toBeVisible({ timeout: 5000 });
  });
});
