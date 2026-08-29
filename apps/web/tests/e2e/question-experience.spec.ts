import { expect, test, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function loginStudent(request: APIRequestContext, context: BrowserContext, accessCode: string) {
  const response = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

async function answerVisibleChoice(page: Page) {
  const imageGroup = page.getByTestId("image-options");
  if (await imageGroup.count()) {
    await imageGroup.getByRole("button").first().click();
  } else {
    const option = page.locator('button[aria-pressed="false"]').first();
    await expect(option).toBeVisible();
    await option.click();
  }
  const confirm = page.getByRole("button", { name: "تأكيد والمتابعة" });
  await expect(confirm).toBeEnabled();
  await confirm.click();
}

async function assertQuestionHierarchy(page: Page) {
  const root = page.getByTestId("assessment-session");
  await expect(root).toHaveAttribute("data-phase", /^(question|submitting)$/);
  await expect(root.getByText("مهمة واحدة في كل مرة", { exact: true })).toHaveCount(0);

  const heading = root.locator("main section h1").first();
  await expect(heading).toBeVisible();
  const instruction = (await heading.textContent())?.trim() ?? "";
  expect(instruction.length).toBeGreaterThan(12);
  expect(instruction).not.toBe("اختر الإجابة الصحيحة.");
  expect(instruction).not.toBe("استمع جيدًا، ثم اختر الإجابة الصحيحة.");

  const headingBox = await heading.boundingBox();
  const imageGroup = page.getByTestId("image-options");
  const firstAnswer = (await imageGroup.count())
    ? imageGroup.getByRole("button").first()
    : page.locator('button[aria-pressed="false"]').first();
  await expect(firstAnswer).toBeVisible();
  const answerBox = await firstAnswer.boundingBox();
  expect(headingBox).toBeTruthy();
  expect(answerBox).toBeTruthy();
  if (headingBox && answerBox) expect(answerBox.y).toBeGreaterThan(headingBox.y + headingBox.height - 2);
}

test.describe("student question experience", () => {
  test("first readiness questions are explicit, complete, and visually ordered", async ({ page, context, request }) => {
    test.setTimeout(120000);
    await loginStudent(request, context, "STU001");

    const start = await request.post(`${API_URL}/assessment/start`, { data: { session_type: "pretest" } });
    expect([200, 409]).toContain(start.status());
    const startPayload = await start.json().catch(() => null);
    let sessionId = startPayload?.id ?? startPayload?.session_id;
    if (!sessionId) {
      await page.goto("/student");
      const button = page.getByRole("button", { name: "ابدأ الاختبار" });
      await expect(button).toBeEnabled();
      await button.click();
      sessionId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
    }
    expect(sessionId).toBeTruthy();

    await page.goto(`/student/session/${sessionId}`);
    for (let index = 0; index < 10; index += 1) {
      const root = page.getByTestId("assessment-session");
      await expect(root).toHaveAttribute("data-phase", "question", { timeout: 15000 });
      await assertQuestionHierarchy(page);

      if (index === 2) {
        const optionButtons = page.locator('button[aria-pressed="false"]');
        expect(await optionButtons.count()).toBeGreaterThanOrEqual(4);
        await page.screenshot({ path: "playwright-report/screenshots/qx-letter-form-options.png", fullPage: true });
      }
      if (index === 4) {
        const text = (await root.locator("main section h1").first().textContent()) ?? "";
        expect(text).toContain("الصورة");
        expect(text).toContain("يبدأ اسمها");
        await page.screenshot({ path: "playwright-report/screenshots/qx-listen-starting-image.png", fullPage: true });
      }
      if (index === 6) {
        const text = (await root.locator("main section h1").first().textContent()) ?? "";
        expect(text).toMatch(/آخرها|نهايتها/u);
        await page.screenshot({ path: "playwright-report/screenshots/qx-final-sound.png", fullPage: true });
      }

      await answerVisibleChoice(page);
    }
  });
});
