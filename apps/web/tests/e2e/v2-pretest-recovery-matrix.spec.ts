import { expect, test } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

test("HV2-002: pretest start and answer recover from 503 without a duplicate submission", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

  const admin = await request.post(`${API_URL}/auth/login`, {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب تعافٍ اصطناعي ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;

  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");

  let startFailures = 0;
  await page.route("**/api/v2/assessments/pretest/start", async route => {
    if (startFailures++ === 0) {
      return route.fulfill({ status: 503, json: { detail: "temporary unavailable" } });
    }
    return route.continue();
  });
  await page.getByTestId("student-primary-action").click();
  await expect(page.getByRole("alert")).toContainText("الاختبار غير متاح حاليًا");
  await expect(page.getByTestId("student-primary-action")).toBeEnabled();
  await page.getByTestId("student-primary-action").click();
  await expect(page).toHaveURL(/\/student\/assessment-v2\/\d+$/);
  const sessionId = Number(page.url().split("/").at(-1));
  await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
  expect(startFailures).toBe(2);

  let answerFailures = 0;
  const submittedKeys: string[] = [];
  await page.route(/\/api\/v2\/assessments\/sessions\/\d+\/answers(?:\?|$)/, async route => {
    const body = route.request().postDataJSON() as { submit_key: string };
    submittedKeys.push(body.submit_key);
    if (answerFailures++ === 0) {
      return route.fulfill({ status: 503, json: { detail: "temporary unavailable" } });
    }
    return route.continue();
  });
  await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
  await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
  await expect(page.getByRole("button", { name: "إعادة محاولة حفظ الإجابة" })).toBeVisible();
  await expect(page.getByRole("button", { name: "اختيار الخيار 1" })).toBeDisabled();
  await page.getByRole("button", { name: "إعادة محاولة حفظ الإجابة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
  expect(submittedKeys).toHaveLength(2);
  expect(submittedKeys[0]).toBe(submittedKeys[1]);
  await page.reload();
  const resumed = await page.evaluate(async id => {
    const response = await fetch(`/api/v2/assessments/sessions/${id}`);
    return { status: response.status, data: await response.json() };
  }, sessionId);
  expect(resumed.status).toBe(200);
  expect(resumed.data.session.progress.answered).toBe(1);
  await page.unroute("**/api/v2/assessments/pretest/start");
});
