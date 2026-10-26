import { expect, test } from "@playwright/test";
import { randomUUID } from "node:crypto";

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


test("HV2-002: committed start and answer survive lost acknowledgements without duplicate progress", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

  const admin = await request.post(`${API_URL}/auth/login`, {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب فقد تأكيد اصطناعي ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;

  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");

  // The upstream response is 200 and commits the session. Only the browser
  // receives 503: this is not a mocked failure before the server-side write.
  let startAttempts = 0;
  let committedSessionId: number | null = null;
  let committedStartStatus: number | null = null;
  await page.route("**/api/v2/assessments/pretest/start", async route => {
    startAttempts += 1;
    if (startAttempts === 1) {
      const upstream = await route.fetch();
      committedStartStatus = upstream.status();
      const body = await upstream.json() as { session?: { session_id?: number } };
      committedSessionId = body.session?.session_id ?? null;
      return route.fulfill({ status: 503, json: { detail: "ack lost after server commit" } });
    }
    return route.continue();
  });
  await page.getByTestId("student-primary-action").click();
  await expect(page.locator("[data-testid='student-home'] [role='alert']")).toContainText("الاختبار غير متاح حاليًا");
  expect(committedStartStatus).toBe(200);
  expect(committedSessionId).toEqual(expect.any(Number));
  await expect(page.getByTestId("student-primary-action")).toBeEnabled();
  await page.getByTestId("student-primary-action").click();
  await expect(page).toHaveURL(/\/student\/assessment-v2\/\d+$/);
  const sessionId = Number(page.url().split("/").at(-1));
  expect(sessionId).toBe(committedSessionId);
  expect(startAttempts).toBe(2);
  await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");

  // Repeat the same failure *after* an answer has been persisted. The
  // subsequent retry must replay the original submit_key, not grade Q2.
  let committedAnswerStatus: number | null = null;
  let committedAnswerCount: number | null = null;
  const submittedKeys: string[] = [];
  await page.route(/\/api\/v2\/assessments\/sessions\/\d+\/answers(?:\?|$)/, async route => {
    const body = route.request().postDataJSON() as { submit_key: string };
    submittedKeys.push(body.submit_key);
    if (submittedKeys.length === 1) {
      const upstream = await route.fetch();
      committedAnswerStatus = upstream.status();
      const saved = await upstream.json() as { assessment?: { session?: { progress?: { answered?: number } } } };
      committedAnswerCount = saved.assessment?.session?.progress?.answered ?? null;
      return route.fulfill({ status: 503, json: { detail: "answer acknowledgement lost" } });
    }
    return route.continue();
  });
  await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
  await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
  await expect(page.getByRole("button", { name: "إعادة محاولة حفظ الإجابة" })).toBeVisible();
  await expect(page.getByRole("button", { name: "اختيار الخيار 1" })).toBeDisabled();
  expect(committedAnswerStatus).toBe(200);
  expect(committedAnswerCount).toBe(1);
  await page.getByRole("button", { name: "إعادة محاولة حفظ الإجابة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
  expect(submittedKeys).toHaveLength(2);
  expect(submittedKeys[0]).toBe(submittedKeys[1]);

  await page.reload();
  const resumed = await page.evaluate(async id => {
    const response = await fetch(`/api/v2/assessments/sessions/${id}`);
    return { status: response.status, progress: (await response.json()).session.progress.answered };
  }, sessionId);
  expect(resumed).toEqual({ status: 200, progress: 1 });
});


test("HV2-002: cross-student session ownership through the browser BFF stays private", async ({ page, request, context }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

  const supervisor = await request.post(`${API_URL}/auth/login`, {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(supervisor.status()).toBe(200);
  const created = [];
  // Create sequentially to avoid racing the server-side access-code allocator.
  for (const label of ["A", "B"]) {
    created.push(await request.post(`${API_URL}/researcher/students`, {
      data: { full_name: `طالب اختبار صلاحيات ${label} ${Date.now()}`, grade_level: 3 },
    }));
  }
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
  const submitKey = randomUUID();
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


test("HV2-002: mismatched assessment GET never renders another session and retry restores the owner", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

  const admin = await request.post(`${API_URL}/auth/login`, {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب تطابق جلسة اصطناعي ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;

  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");

  const started = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(started.status).toBe(200);
  const sessionId = started.data.session.session_id as number;
  let reads = 0;
  await page.route(`**/api/v2/assessments/sessions/${sessionId}`, async route => {
    if (route.request().method() !== "GET") return route.continue();
    reads += 1;
    if (reads === 1) {
      const upstream = await route.fetch();
      expect(upstream.status()).toBe(200);
      const original = (await upstream.json()) as { session: { session_id: number } };
      // The upstream GET is real; only the returned session identifier is
      // altered to reproduce a stale or cross-session response at the BFF.
      return route.fulfill({
        response: upstream,
        json: { ...original, session: { ...original.session, session_id: sessionId + 1 } },
      });
    }
    return route.continue();
  });

  await page.goto(`/student/assessment-v2/${sessionId}`);
  await expect(page.locator("main [role='alert']")).toContainText("تعذر استعادة التقييم");
  await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
  expect(reads).toBe(2);
  const recovered = await page.evaluate(async id => {
    const response = await fetch(`/api/v2/assessments/sessions/${id}`);
    return { status: response.status, data: await response.json() };
  }, sessionId);
  expect(recovered.status).toBe(200);
  expect(recovered.data.session.session_id).toBe(sessionId);
  expect(recovered.data.session.progress.answered).toBe(0);
});


for (const mismatch of ["session_id", "kind"] as const) {
  test("HV2-002: committed POST answer with wrong " + mismatch + " fails closed and resumes from GET", async ({ page, request }) => {
    test.setTimeout(150000);
    if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

    const admin = await request.post(API_URL + "/auth/login", {
      data: { username: USERNAME, password: PASSWORD },
    });
    expect(admin.status()).toBe(200);
    const created = await request.post(API_URL + "/researcher/students", {
      data: { full_name: "طالب اختبار تأكيد اصطناعي " + Date.now(), grade_level: 3 },
    });
    expect(created.status()).toBe(201);
    const code = (await created.json()).access_code as string;

    await page.goto("/student/login");
    await page.getByTestId("input-access-code").fill(code);
    await page.getByTestId("student-login-submit").click();
    await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");

    const started = await page.evaluate(async () => {
      const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
      return { status: response.status, data: await response.json() };
    });
    expect(started.status).toBe(200);
    const sessionId = started.data.session.session_id as number;
    let tamperedResponses = 0;
    await page.route(/\/api\/v2\/assessments\/sessions\/\d+\/answers(?:\?|$)/, async route => {
      const upstream = await route.fetch();
      expect(upstream.status()).toBe(200);
      const original = await upstream.json() as {
        assessment: { session: { session_id: number; kind: string } };
      };
      expect(original.assessment.session.session_id).toBe(sessionId);
      expect(original.assessment.session.kind).toBe("pretest");
      tamperedResponses += 1;
      const wrongSession = mismatch === "session_id"
        ? { ...original.assessment.session, session_id: sessionId + 1 }
        : { ...original.assessment.session, kind: "posttest" };
      // Persist the real answer upstream, but replace only the browser-facing
      // acknowledgement. No cross-student data or fake backend state is stored.
      await route.fulfill({
        response: upstream,
        json: { ...original, assessment: { ...original.assessment, session: wrongSession } },
      });
    });

    await page.goto("/student/assessment-v2/" + sessionId);
    await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
    await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
    await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();

    await expect(page.locator("main [role='alert']")).toContainText("تعذر تأكيد حفظ الإجابة");
    await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
    expect(tamperedResponses).toBe(1);
    await page.getByRole("button", { name: "إعادة المحاولة" }).click();
    await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
    const restored = await page.evaluate(async id => {
      const response = await fetch("/api/v2/assessments/sessions/" + id);
      const body = await response.json();
      return {
        status: response.status,
        sessionId: body.session.session_id,
        kind: body.session.kind,
        answered: body.session.progress.answered,
      };
    }, sessionId);
    expect(restored).toEqual({
      status: 200, sessionId, kind: "pretest", answered: 1,
    });
  });
}


for (const corruption of ["invalid_progress", "missing_summary"] as const) {
  test("HV2-002: malformed or stale committed answer acknowledgement (" + corruption + ") fails closed", async ({ page, request }) => {
    test.setTimeout(150000);
    if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
    const admin = await request.post(API_URL + "/auth/login", {
      data: { username: USERNAME, password: PASSWORD },
    });
    expect(admin.status()).toBe(200);
    const created = await request.post(API_URL + "/researcher/students", {
      data: { full_name: "طالب فحص سلامة استجابة اصطناعي " + Date.now(), grade_level: 3 },
    });
    expect(created.status()).toBe(201);
    const code = (await created.json()).access_code as string;

    await page.goto("/student/login");
    await page.getByTestId("input-access-code").fill(code);
    await page.getByTestId("student-login-submit").click();
    await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
    const started = await page.evaluate(async () => {
      const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
      return { status: response.status, data: await response.json() };
    });
    expect(started.status).toBe(200);
    const sessionId = started.data.session.session_id as number;
    let altered = 0;
    await page.route("**/api/v2/assessments/sessions/*/answers", async route => {
      const upstream = await route.fetch();
      expect(upstream.status()).toBe(200);
      const original = await upstream.json() as {
        assessment: { session: { session_id: number; progress: { answered: number; total: number } }; summary: { pending_review: number } };
      };
      expect(original.assessment.session.session_id).toBe(sessionId);
      expect(original.assessment.session.progress.answered).toBe(1);
      altered += 1;
      const assessment = corruption === "invalid_progress"
        ? { ...original.assessment, session: { ...original.assessment.session, progress: { ...original.assessment.session.progress, answered: -1 } } }
        : { ...original.assessment, summary: undefined };
      await route.fulfill({ response: upstream, json: { ...original, assessment } });
    });

    await page.goto("/student/assessment-v2/" + sessionId);
    await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
    await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
    await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
    await expect(page.locator("main [role='alert']")).toContainText("تعذر تأكيد حفظ الإجابة");
    await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
    expect(altered).toBe(1);
    await page.getByRole("button", { name: "إعادة المحاولة" }).click();
    await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
    const restored = await page.evaluate(async id => {
      const response = await fetch("/api/v2/assessments/sessions/" + id);
      const body = await response.json();
      return { status: response.status, id: body.session.session_id, answered: body.session.progress.answered };
    }, sessionId);
    expect(restored).toEqual({ status: 200, id: sessionId, answered: 1 });
  });
}

test("HV2-002: malformed GET assessment state fails closed and retry restores the session", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const admin = await request.post(API_URL + "/auth/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(API_URL + "/researcher/students", {
    data: { full_name: "طالب استعادة حمولة اصطناعي " + Date.now(), grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;
  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  const started = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(started.status).toBe(200);
  const sessionId = started.data.session.session_id as number;
  let reads = 0;
  await page.route("**/api/v2/assessments/sessions/" + sessionId, async route => {
    if (route.request().method() !== "GET") return route.continue();
    reads += 1;
    if (reads !== 1) return route.continue();
    const upstream = await route.fetch();
    expect(upstream.status()).toBe(200);
    const original = await upstream.json() as { session: { session_id: number; progress: { answered: number; total: number } } };
    return route.fulfill({ response: upstream, json: {
      ...original, session: { ...original.session, progress: null },
    } });
  });
  await page.goto("/student/assessment-v2/" + sessionId);
  await expect(page.locator("main [role='alert']")).toContainText("تعذر استعادة التقييم");
  await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
  expect(reads).toBe(2);
});

test("HV2-002: a structurally valid but regressed POST progress (2 to 1) fails closed after server commits answer three", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");

  const admin = await request.post(API_URL + "/auth/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(API_URL + "/researcher/students", {
    data: { full_name: "طالب اختبار تراجع اصطناعي " + Date.now(), grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;

  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  const started = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(started.status).toBe(200);
  const sessionId = started.data.session.session_id as number;

  await page.goto("/student/assessment-v2/" + sessionId);
  for (const [questionNumber, nextNumber] of [[1, 2], [2, 3]] as const) {
    await expect(page.getByTestId("v2-interaction-player")).toContainText(questionNumber + " من 30");
    await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
    await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
    await expect(page.getByTestId("v2-interaction-player")).toContainText(nextNumber + " من 30");
  }

  // Two answers are genuinely persisted. The third POST also commits upstream;
  // only its browser-facing acknowledgement is changed to a *valid* 1/30,
  // rather than an obviously invalid negative count.
  const before = await page.evaluate(async id => {
    const response = await fetch("/api/v2/assessments/sessions/" + id);
    return { status: response.status, answered: (await response.json()).session.progress.answered };
  }, sessionId);
  expect(before).toEqual({ status: 200, answered: 2 });

  let answerRequests = 0;
  await page.route(/\/api\/v2\/assessments\/sessions\/\d+\/answers(?:\?|$)/, async route => {
    answerRequests += 1;
    const upstream = await route.fetch();
    expect(upstream.status()).toBe(200);
    const original = await upstream.json() as {
      assessment: { session: { session_id: number; progress: { answered: number; total: number } } };
    };
    expect(original.assessment.session.session_id).toBe(sessionId);
    expect(original.assessment.session.progress.answered).toBe(3);
    await route.fulfill({
      response: upstream,
      json: {
        ...original,
        assessment: {
          ...original.assessment,
          session: {
            ...original.assessment.session,
            progress: { ...original.assessment.session.progress, answered: 1 },
          },
        },
      },
    });
  });

  await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
  await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
  await expect(page.locator("main [role='alert']")).toContainText("تعذر تأكيد حفظ الإجابة");
  await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
  expect(answerRequests).toBe(1);

  // Retry is GET-only: no second POST of the committed answer.
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("4 من 30");
  expect(answerRequests).toBe(1);
  await page.reload();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("4 من 30");
  const resumed = await page.evaluate(async id => {
    const response = await fetch("/api/v2/assessments/sessions/" + id);
    const data = await response.json();
    return { status: response.status, sessionId: data.session.session_id, answered: data.session.progress.answered };
  }, sessionId);
  expect(resumed).toEqual({ status: 200, sessionId, answered: 3 });
  expect(answerRequests).toBe(1);
});

test("HV2-002: same-session GET with a wrong question role fails closed before rendering", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const admin = await request.post(API_URL + "/auth/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(API_URL + "/researcher/students", {
    data: { full_name: "طالب تحقق دور السؤال اصطناعي " + Date.now(), grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;
  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  const started = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(started.status).toBe(200);
  const sessionId = started.data.session.session_id as number;
  let reads = 0;
  await page.route("**/api/v2/assessments/sessions/" + sessionId, async route => {
    if (route.request().method() !== "GET") return route.continue();
    reads += 1;
    if (reads !== 1) return route.continue();
    const upstream = await route.fetch();
    expect(upstream.status()).toBe(200);
    const original = await upstream.json() as {
      interaction: { question: { role: string } };
    };
    return route.fulfill({ response: upstream, json: {
      ...original,
      interaction: {
        ...original.interaction,
        question: { ...original.interaction.question, role: "posttest" },
      },
    } });
  });
  await page.goto("/student/assessment-v2/" + sessionId);
  await expect(page.locator("main [role='alert']")).toContainText("تعذر استعادة التقييم");
  await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
  expect(reads).toBe(2);
});

test("HV2-002: committed POST with stale question index recovers via GET without replay", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const admin = await request.post(API_URL + "/auth/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(API_URL + "/researcher/students", {
    data: { full_name: "طالب تحقق فهرس السؤال اصطناعي " + Date.now(), grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;
  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  const started = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(started.status).toBe(200);
  const sessionId = started.data.session.session_id as number;
  let answerPosts = 0;
  await page.route(/\/api\/v2\/assessments\/sessions\/\d+\/answers(?:\?|$)/, async route => {
    answerPosts += 1;
    const upstream = await route.fetch();
    expect(upstream.status()).toBe(200);
    const original = await upstream.json() as {
      assessment: { session: { progress: { answered: number } }; interaction: { progress: { index: number } } };
    };
    expect(original.assessment.session.progress.answered).toBe(1);
    expect(original.assessment.interaction.progress.index).toBe(2);
    return route.fulfill({ response: upstream, json: {
      ...original,
      assessment: {
        ...original.assessment,
        interaction: {
          ...original.assessment.interaction,
          progress: { ...original.assessment.interaction.progress, index: 1 },
        },
      },
    } });
  });
  await page.goto("/student/assessment-v2/" + sessionId);
  await expect(page.getByTestId("v2-interaction-player")).toContainText("1 من 30");
  await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
  await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
  await expect(page.locator("main [role='alert']")).toContainText("تعذر تأكيد حفظ الإجابة");
  await expect(page.getByTestId("v2-interaction-player")).toHaveCount(0);
  expect(answerPosts).toBe(1);
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
  await page.reload();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
  expect(answerPosts).toBe(1);
  const recovered = await page.evaluate(async id => {
    const response = await fetch("/api/v2/assessments/sessions/" + id);
    return { status: response.status, answered: (await response.json()).session.progress.answered };
  }, sessionId);
  expect(recovered).toEqual({ status: 200, answered: 1 });
});


test("HV2-002: delayed unauthorized assessment GET cannot redirect after leaving the route", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const admin = await request.post(API_URL + "/auth/login", {
    data: { username: USERNAME, password: PASSWORD },
  });
  expect(admin.status()).toBe(200);
  const created = await request.post(API_URL + "/researcher/students", {
    data: { full_name: "طالب عزل استجابة متأخرة اصطناعي " + Date.now(), grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;
  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  const started = await page.evaluate(async () => {
    const response = await fetch("/api/v2/assessments/pretest/start", { method: "POST" });
    return { status: response.status, data: await response.json() };
  });
  expect(started.status).toBe(200);
  const sessionId = started.data.session.session_id as number;

  let reads = 0;
  let releaseUnauthorized!: () => void;
  const held = new Promise<void>(resolve => { releaseUnauthorized = resolve; });
  let lateRequestSeen = false;
  let lateRequestSettled = false;
  await page.route("**/api/v2/assessments/sessions/" + sessionId, async route => {
    if (route.request().method() !== "GET") return route.continue();
    reads += 1;
    if (reads === 1) {
      // First response is malformed, leaving a retry screen with a Next Link.
      return route.fulfill({ status: 200, json: {} });
    }
    lateRequestSeen = true;
    await held;
    try {
      await route.fulfill({ status: 401, json: { detail: "expired test session" } });
    } catch {
      // Correct cancellation may close the intercepted request on unmount.
    } finally {
      lateRequestSettled = true;
    }
  });
  await page.goto("/student/assessment-v2/" + sessionId);
  await expect(page.locator("main [role='alert']")).toContainText("تعذر استعادة التقييم");
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect.poll(() => lateRequestSeen).toBe(true);

  // Client-side Next Link transition unmounts the assessment while GET is held.
  await page.getByRole("link", { name: "لوحة الطالب" }).click();
  await expect(page).toHaveURL(new RegExp("/student$"));
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  releaseUnauthorized();
  await expect.poll(() => lateRequestSettled).toBe(true);
  // A stale 401 must not push the new student page back to /student/login.
  await expect(page).toHaveURL(new RegExp("/student$"));
  await expect(page.getByTestId("student-home")).toBeVisible();
  expect(reads).toBe(2);
});
