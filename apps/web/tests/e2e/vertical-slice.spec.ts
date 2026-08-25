import { test, expect, APIRequestContext } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function loginAsResearcher(request: APIRequestContext, context: import("@playwright/test").BrowserContext) {
  if (!RESEARCHER_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const res = await request.post(`${API_URL}/auth/login`, {
    data: { username: RESEARCHER_USERNAME, password: RESEARCHER_PASSWORD },
  });
  expect(res.status(), "Admin login should return 200").toBe(200);
  const setCookieHeader = res.headers()["set-cookie"];
  const cookieMatch = setCookieHeader?.match(/access_token=([^;]+)/);
  if (cookieMatch) {
    await context.addCookies([{
      name: "access_token", value: cookieMatch[1], domain: "localhost", path: "/",
      httpOnly: true, sameSite: "Lax", secure: false,
    }]);
  }
}

async function loginAsStudent(request: APIRequestContext, context: import("@playwright/test").BrowserContext, accessCode: string) {
  const res = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(res.status(), `Student login with code ${accessCode} should return 200`).toBe(200);
  const setCookieHeader = res.headers()["set-cookie"];
  const cookieMatch = setCookieHeader?.match(/access_token=([^;]+)/);
  if (cookieMatch) {
    await context.addCookies([{
      name: "access_token", value: cookieMatch[1], domain: "localhost", path: "/",
      httpOnly: true, sameSite: "Lax", secure: false,
    }]);
  }
}

async function shot(page: import("@playwright/test").Page, name: string) {
  await page.screenshot({ path: `playwright-report/screenshots/${name}.png`, fullPage: true });
}

test.describe("Full Vertical Slice — Stage 2 Closure Gate", () => {
  test("Admin creates student → pretest/review → assigned core path → researcher sees 10/10", async ({ page, context, request }) => {
    test.setTimeout(180000);

    await loginAsResearcher(request, context);
    await page.goto("/admin/students/new");
    await expect(page).not.toHaveURL(/login/, { timeout: 5000 });

    const studentName = `E2E Student ${Date.now()}`;
    await page.getByTestId("input-student-name").fill(studentName);
    await expect(page.getByTestId("input-student-grade")).toHaveValue("3");
    await expect(page.getByTestId("input-student-grade")).toBeDisabled();
    await page.getByTestId("submit-create-student").click();

    const codeEl = page.getByTestId("student-access-code");
    await expect(codeEl).toBeVisible({ timeout: 10000 });
    const accessCode = (await codeEl.textContent())?.trim();
    expect(accessCode).toBeTruthy();
    await shot(page, "01-student-created");

    const studentsRes = await request.get(`${API_URL}/researcher/students`);
    expect(studentsRes.status()).toBe(200);
    const students: Array<{ id: number; access_code: string; full_name: string }> = await studentsRes.json();
    const createdStudent = students.find((candidate) => candidate.access_code === accessCode);
    expect(createdStudent?.full_name).toBe(studentName);
    const studentId = createdStudent?.id;
    expect(studentId).toBeTruthy();

    await context.clearCookies();
    await loginAsStudent(request, context, accessCode!);
    await page.goto("/student");
    await expect(page.getByText(/أهلاً|مرحباً/)).toBeVisible({ timeout: 5000 });

    const startBtn = page.getByRole("button", { name: /ابدأ|اختبار/ });
    await startBtn.click();
    await expect(page).toHaveURL(/\/student\/session\/\d+/, { timeout: 10000 });
    const sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    expect(sessionId).toBeTruthy();

    const sessionRoot = page.getByTestId("assessment-session");
    const progressCounter = page.getByTestId("assessment-progress");
    const waitForActionablePhase = async () => {
      await expect(sessionRoot).toHaveAttribute("data-phase", /^(question|recording|waiting_audio_review|done|error)$/, { timeout: 15000 });
      const phase = await sessionRoot.getAttribute("data-phase");
      if (phase === "error") throw new Error((await sessionRoot.textContent()) || "Assessment error");
      return phase;
    };

    let questionsAnswered = 0;
    while (questionsAnswered < 30) {
      const phase = await waitForActionablePhase();
      if (phase === "waiting_audio_review" || phase === "done") break;
      if (phase === "recording") {
        await page.getByRole("button", { name: "ابدأ التسجيل" }).click();
        await page.waitForTimeout(2500);
        await page.getByRole("button", { name: /إيقاف|أوقف/ }).first().click();
        await page.waitForTimeout(500);
        const submitBtn = page.getByRole("button", { name: /إرسال التسجيل|أرسل/ }).first();
        await expect(submitBtn).toBeEnabled({ timeout: 5000 });
        await submitBtn.click();
      } else {
        const optionBtns = page.locator(".assessment-option");
        await expect(optionBtns.first()).toBeVisible({ timeout: 5000 });
        await optionBtns.first().click();
        await page.getByRole("button", { name: "تأكيد الإجابة" }).click();
      }
      questionsAnswered++;
      if (questionsAnswered < 30) {
        await waitForActionablePhase();
        await expect(progressCounter).toContainText(`${questionsAnswered}/`, { timeout: 15000 });
      }
      if (questionsAnswered === 1) {
        await page.reload();
        await waitForActionablePhase();
        await expect(progressCounter).toContainText("1/", { timeout: 15000 });
      }
    }
    expect(questionsAnswered).toBe(30);
    await expect(page.getByText("في انتظار المراجعة")).toBeVisible({ timeout: 15000 });

    await context.clearCookies();
    await loginAsResearcher(request, context);
    await page.goto("/admin/audio-review");
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

    await context.clearCookies();
    await loginAsStudent(request, context, accessCode!);
    await page.goto(`/student/session/${sessionId}`);
    await expect(page.getByText("أحسنت")).toBeVisible({ timeout: 15000 });

    await page.goto("/student");
    const learningButton = page.getByRole("button", { name: /ابدأ أنشطة مستواك|متابعة الأنشطة/ });
    await expect(learningButton).toBeEnabled({ timeout: 10000 });
    await learningButton.click();
    await expect(page).toHaveURL(/\/student\/activity\/\d+/, { timeout: 10000 });

    const activityRoot = page.getByTestId("activity-session");
    await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });
    await shot(page, "02-first-learning-activity");

    await page.reload();
    await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });

    let learningInteractions = 0;
    while ((await activityRoot.getAttribute("data-phase")) !== "done") {
      learningInteractions++;
      expect(learningInteractions, "Core path should terminate").toBeLessThan(100);

      const gapButton = page.getByRole("button", { name: "متابعة دون احتساب هذه الجولة" });
      const recordButton = page.getByRole("button", { name: "ابدأ القراءة" });
      const optionButtons = activityRoot.locator("button[aria-pressed]");

      await expect.poll(async () => {
        if ((await activityRoot.getAttribute("data-phase")) === "done") return "done";
        if (await gapButton.count()) return "gap";
        if (await recordButton.count()) return "record";
        if (await optionButtons.count()) return "options";
        return "waiting";
      }, { timeout: 10000 }).not.toBe("waiting");

      if ((await activityRoot.getAttribute("data-phase")) === "done") break;

      if (await gapButton.count()) {
        await gapButton.click();
      } else if (await recordButton.count()) {
        await recordButton.click();
        await page.waitForTimeout(700);
        await page.getByRole("button", { name: /إيقاف التسجيل/ }).click();
        const saveReading = page.getByRole("button", { name: "حفظ القراءة والمتابعة" });
        await expect(saveReading).toBeEnabled({ timeout: 5000 });
        await saveReading.click();
      } else {
        await expect(optionButtons.first()).toBeVisible({ timeout: 5000 });
        const verifyButton = page.getByRole("button", { name: "تحقق وتابع" });
        const optionCount = await optionButtons.count();
        for (let index = 0; index < optionCount; index++) {
          await optionButtons.nth(index).click();
          if (await verifyButton.isEnabled()) break;
        }
        await expect(verifyButton).toBeEnabled({ timeout: 3000 });
        await verifyButton.click();
      }

      await page.waitForTimeout(650);
      await expect(activityRoot).toHaveAttribute("data-phase", /^(active|done)$/, { timeout: 15000 });
    }

    await expect(page.getByText("أحسنت، أكملت أنشطة مستواك")).toBeVisible({ timeout: 15000 });
    await shot(page, "03-learning-complete");

    await context.clearCookies();
    await loginAsResearcher(request, context);
    await page.goto(`/admin/students/${studentId}`);
    await expect(page.getByText("10 من 10")).toBeVisible({ timeout: 10000 });
    const enablePosttest = page.getByRole("button", { name: "إتاحة الاختبار البعدي" });
    await expect(enablePosttest).toBeEnabled();
    await shot(page, "04-researcher-progress-10-of-10");

    await page.goto("/admin/students");
    await expect(page.getByText(studentName)).toBeVisible({ timeout: 5000 });
  });
});
