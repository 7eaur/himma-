import { expect, test } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

test("first pretest question shows instructions, character and a saved answer without a hint", async ({ page, request }) => {
  test.setTimeout(120000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const admin = await request.post(`${API_URL}/auth/login`, { data: { username: USERNAME, password: PASSWORD } });
  expect(admin.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب فحص السؤال ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;
  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  await page.getByTestId("student-primary-action").click();
  await expect(page).toHaveURL(/\/student\/assessment-v2\/\d+$/);
  const question = page.getByTestId("v2-interaction-player");
  await expect(question).toContainText("1 من 30");
  await expect(page.getByTestId("v2-question-coach")).toBeVisible();
  await expect(question.getByText(/تلميح:/)).toHaveCount(0);
  await question.getByRole("button", { name: "اختيار الخيار 1" }).click();
  await page.screenshot({ path: "playwright-report/screenshots/v2-first-question-character.png", fullPage: true });
  await question.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
  await expect(question).toContainText("2 من 30");
  await page.reload();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
});
