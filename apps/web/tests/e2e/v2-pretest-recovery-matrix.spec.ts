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
  await expect(page.locator("[data-testid=\"student-home\"] [role=\"alert\"]")).toContainText("الاختبار غير متاح حاليًا");
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


test("HV2-002: cross-student session ownership through the browser BFF stays private", async ({ page, request, context }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

  const supervisor = await request.post(`${API_URL}/auth/login`, {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(supervisor.status()).toBe(200);
  const created = await Promise.all(["A", "B"].map(label =>
    request.post(`${API_URL}/researcher/students`, {
      data: { full_name: `طالب اختبار صلاحيات ${label} ${Date.now()}`, grade_level: 3 },
    }),
  ));
  for (const response of created) expect(response.status()).toBe(201);
  const codes = await Promise.all(created.map(async response =>
    (await response.json()).access_code as string,
  ));
  const tokens: string[] = [];
  for (const code of codes) {
    const signedIn = await request.post(`${API_URL}/auth/student-login`, {
      data: { access_code: code },
    });
    expect(signedIn.status()).toBe(200);
    const token = signedIn.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
    expect(token).toBeTruthy();
    tokens.push(token!);
  }

  const switchStudent = async (token: string) => {
    await context.addCookies([{
      name: "access_token", value: token, domain: "localhost", path: "/",
      httpOnly: true, secure: false, sameSite: "Lax",
    }]);
    await page.goto("/student");
    await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  };

  await switchStudent(tokens[0]);
  const first = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(first.status).toBe(200);
  const sessionId = first.data.session.session_id as number;
  const optionId = first.data.interaction.question.options[0].id as string;
  const submitKey = crypto.randomUUID();
  const answer = { submit_key: submitKey, selected_option_ids: [optionId] };
  const saved = await page.evaluate(async ({ id, body }) => {
    const response = await fetch(`/api/v2/assessments/sessions/${id}/answers`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return { status: response.status, data: await response.json() };
  }, { id: sessionId, body: answer });
  expect(saved.status).toBe(200);
  expect(saved.data.assessment.session.progress.answered).toBe(1);

  await switchStudent(tokens[1]);
  const denied = await page.evaluate(async ({ id, body }) => {
    const get = await fetch(`/api/v2/assessments/sessions/${id}`);
    const post = await fetch(`/api/v2/assessments/sessions/${id}/answers`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const missing = await fetch("/api/v2/assessments/sessions/999999999");
    return {
      getStatus: get.status, getBody: await get.json(),
      postStatus: post.status, postBody: await post.json(),
      missingStatus: missing.status, missingBody: await missing.json(),
    };
  }, { id: sessionId, body: answer });
  expect(denied.getStatus).toBe(404);
  expect(denied.postStatus).toBe(404);
  expect(denied.missingStatus).toBe(404);
  expect(denied.getBody).toEqual(denied.missingBody);
  expect(denied.postBody).toEqual(denied.missingBody);

  await switchStudent(tokens[0]);
  const restored = await page.evaluate(async ({ id, body }) => {
    const get = await fetch(`/api/v2/assessments/sessions/${id}`);
    const post = await fetch(`/api/v2/assessments/sessions/${id}/answers`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return {
      getStatus: get.status, progress: (await get.json()).session.progress.answered,
      replayStatus: post.status, replay: (await post.json()).status,
    };
  }, { id: sessionId, body: answer });
  expect(restored).toEqual({ getStatus: 200, progress: 1, replayStatus: 200, replay: "replayed" });
});
