import { test, expect } from "@playwright/test";

test.describe("Full Vertical Slice - Stage 02 Gate", () => {
  test("Admin creates student -> Student takes test -> Admin grades", async ({ page, context }) => {
    // 1. Admin Login
    await page.goto("/admin/login");
    await page.getByTestId("input-username").fill("researcher1");
    await page.getByTestId("input-password").fill("securepass123");
    await page.getByTestId("login-submit").click();
    await expect(page).toHaveURL(/\/admin/);

    // 2. Create Student
    await page.goto("/admin/students/new");
    await page.getByTestId("input-student-name").fill("Student Playwright");
    // select grade 1
    await page.getByTestId("input-student-grade").selectOption("1");
    await page.getByTestId("btn-create-student").click();

    // Extract access code
    const codeElement = page.locator("code").first();
    await expect(codeElement).toBeVisible();
    const accessCode = await codeElement.textContent();
    expect(accessCode).toBeTruthy();

    // 3. Logout Admin
    await page.goto("/admin/account");
    await page.getByRole("button", { name: "تسجيل الخروج" }).click();
    await expect(page).toHaveURL(/\/admin\/login/);

    // 4. Student Login
    await page.goto("/student/login");
    await page.getByTestId("input-access-code").fill(accessCode as string);
    await page.getByRole("button", { name: "دخول" }).click();
    await expect(page).toHaveURL(/\/student/);

    // 5. Student Dashboard
    await expect(page.getByText("أهلاً بك")).toBeVisible();
    
    // Start Assessment (It will redirect to /student/session/[id])
    await page.getByRole("button", { name: "ابدأ اختبار تحديد المستوى" }).click();
    await expect(page).toHaveURL(/\/student\/session\/\d+/);

    // 6. Answer 30 questions
    for (let i = 0; i < 30; i++) {
      // Wait for question to load
      await expect(page.getByText(/السؤال \d+ من 30/)).toBeVisible({ timeout: 10000 });
      
      // Determine if it's Audio or MCQ by checking for recording button
      const recordBtn = page.getByRole("button", { name: /ابدأ التسجيل/ });
      const hasAudio = await recordBtn.isVisible().catch(() => false);

      if (hasAudio) {
        // Audio Question
        await recordBtn.click();
        await expect(page.getByRole("button", { name: /إيقاف التسجيل/ })).toBeVisible();
        // Wait 2 seconds for fake media stream to capture something
        await page.waitForTimeout(2000);
        await page.getByRole("button", { name: /إيقاف التسجيل/ }).click();
        
        // Submit audio
        await page.getByRole("button", { name: /إرسال التسجيل/ }).click();
      } else {
        // MCQ Question
        // Just click the first option available
        const options = page.locator("button.optionBtn, button[class*='optionBtn']");
        await expect(options.first()).toBeVisible();
        await options.first().click();
      }
    }

    // 7. Verify Completion
    await expect(page.getByText("أحسنت! انتهيت من الاختبار")).toBeVisible({ timeout: 10000 });

    // 8. Admin Login to Grade
    await page.goto("/admin/login");
    await page.getByTestId("input-username").fill("researcher1");
    await page.getByTestId("input-password").fill("securepass123");
    await page.getByTestId("login-submit").click();

    // 9. Audio Review
    await page.goto("/admin/audio-review");
    
    // We should see audio submissions here. Let's grade the first one.
    const gradeCorrectBtn = page.getByRole("button", { name: "✅ قراءة صحيحة" }).first();
    await expect(gradeCorrectBtn).toBeVisible();
    await gradeCorrectBtn.click();
    
    // Test passed completely!
  });
});
