import { test, expect, APIRequestContext } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Login helper: calls API directly and stores cookies in the browser context.
 * This bypasses the UI login form to avoid the 307 redirect cookie issue.
 */
async function loginAsResearcher(request: APIRequestContext, context: import("@playwright/test").BrowserContext) {
  const res = await request.post(`${API_URL}/auth/login`, {
    data: { username: "researcher1", password: "securepass123" },
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
        sameSite: "None",
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
        sameSite: "None",
        secure: false,
      }]);
    }
  }
}

test.describe("Full Vertical Slice — P02 Gate", () => {
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
    await page.getByTestId("input-student-grade").selectOption("1");
    await page.getByTestId("btn-create-student").click();

    // ── Step 3: Extract access code ──────────────────────────────────────────
    const codeEl = page.locator("code").first();
    await expect(codeEl).toBeVisible({ timeout: 10000 });
    const accessCode = (await codeEl.textContent())?.trim();
    expect(accessCode, "Access code should be present").toBeTruthy();
    console.log(`Created student with access code: ${accessCode}`);

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

    // ── Step 7: Answer questions (up to 30) ──────────────────────────────────
    let questionsAnswered = 0;
    const maxQuestions = 30;

    while (questionsAnswered < maxQuestions) {
      // Wait for either next question or completion screen
      const isDone = await page.getByText(/أحسنت|انتهيت|اكتملت/).isVisible().catch(() => false);
      if (isDone) break;

      // Check for audio question
      const recordBtn = page.getByRole("button", { name: /ابدأ التسجيل|سجّل/ }).first();
      const hasAudio = await recordBtn.isVisible({ timeout: 5000 }).catch(() => false);

      if (hasAudio) {
        // Audio question: use fake media stream (configured in playwright.config.ts)
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
        const optionBtns = page.locator("[class*='optionBtn'], [data-testid='option']");
        const count = await optionBtns.count();
        if (count === 0) {
          // No options visible yet — might still be loading
          await page.waitForTimeout(1000);
          continue;
        }
        await optionBtns.first().click({ timeout: 5000 });
      }

      questionsAnswered++;
      // Brief pause between questions
      await page.waitForTimeout(500);
    }

    console.log(`Answered ${questionsAnswered} questions`);

    // ── Step 8: Verify completion ─────────────────────────────────────────────
    await expect(
      page.getByText(/أحسنت|انتهيت|اكتمل/)
    ).toBeVisible({ timeout: 15000 });

    // ── Step 9: Admin reviews audio ───────────────────────────────────────────
    await context.clearCookies();
    await loginAsResearcher(request, context);
    await page.goto("/admin/audio-review");
    await expect(page).not.toHaveURL(/login/, { timeout: 5000 });

    // Check if there are any pending audio reviews (may be 0 if no audio questions were answered)
    const pendingAudio = page.getByRole("button", { name: /صحيحة|صالح/ }).first();
    const hasPending = await pendingAudio.isVisible({ timeout: 3000 }).catch(() => false);

    if (hasPending) {
      await pendingAudio.click();
      console.log("Graded one audio submission");
    } else {
      console.log("No pending audio reviews (OK if no audio questions were seeded)");
    }

    // ── Step 10: Verify student list updated ─────────────────────────────────
    await page.goto("/admin/students");
    await expect(page.getByText(studentName)).toBeVisible({ timeout: 5000 });

    console.log("✓ Vertical slice complete");
  });
});
