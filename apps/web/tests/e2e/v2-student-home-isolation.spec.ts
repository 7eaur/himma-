import { expect, test } from "@playwright/test";
import path from "node:path";
import { mkdir } from "node:fs/promises";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const OUTPUT = path.join(process.cwd(), "playwright-report", "screenshots", "p09-v2-home");

test("P09.1-C: enrolled V2 dashboard never mixes historic progress or rewards", async ({ page, request, context }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const login = await request.post(`${API_URL}/auth/login`, { data: { username: USERNAME, password: PASSWORD } });
  expect(login.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب واجهة V2 ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;
  const signedIn = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: code } });
  expect(signedIn.status()).toBe(200);
  const token = signedIn.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(token).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: token!, domain: "localhost", path: "/", httpOnly: true, secure: false, sameSite: "Lax" }]);

  await mkdir(OUTPUT, { recursive: true });
  const oldCalls: string[] = [];
  await page.route(/\/api\/(profile|activities\/status|journey|rewards)(?:\?|$)/, route => {
    oldCalls.push(new URL(route.request().url()).pathname);
    return route.fulfill({ status: 503, json: { detail: "V1 should not be used for a V2 learner" } });
  });
  const home = {
    mode: "v2", test_only: true,
    student: { id: 90001, full_name: "طالب التجربة", grade_level: 3 },
    current_action: { action: "lesson_catalog", href: "/student/learning-v2", label: "متابعة الرحلة التعليمية" },
    journey: {
      placement_state: "placed", current_level: 2,
      current_lesson_id: "L2-01", content_release_version: "v2-candidate",
    },
    progress: {
      completed_lessons: 3, assigned_lessons: 14,
      skipped_by_placement: 5, pending_review: 0, display_percent: 21.4,
    },
    assessments: { pretest: { session_id: 70, state: "completed", official: true, score_percent: 85 }, posttest: null },
    rewards: { state: "not_implemented_v2" }, data_status: "ready",
  };
  await page.route("**/api/v2/student/home", route => route.fulfill({ json: home }));
  await page.route("**/api/v2/retries/student/tasks?*", route => route.fulfill({ json: { items: [], next_offset: null } }));

  for (const size of [{ width: 360, height: 800 }, { width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(size);
    await page.goto("/student");
    await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
    await expect(page.getByRole("heading", { name: "مرحبًا يا طالب" })).toBeVisible();
    await expect(page.getByTestId("student-v2-progress")).toContainText("3 من 14");
    await expect(page.getByTestId("student-v2-progress")).toContainText("21.4%");
    await expect(page.getByTestId("student-journey-status")).toHaveText("الحركات والكلمات");
    await expect(page.getByTestId("student-primary-action")).toHaveText("متابعة الرحلة التعليمية");
    await expect(page.getByText("لا نعرض نجومًا قبل اعتماد نظام مكافآت V2.")).toBeVisible();
    await expect(page.locator("[data-testid='student-badges']")).toHaveCount(0);
    await expect(page.locator("[data-testid='v2-learning-preview']")).toHaveCount(0);
    const widths = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
    expect(widths[0], JSON.stringify({ size, widths })).toBeLessThanOrEqual(widths[1] + 1);
    await page.screenshot({ path: path.join(OUTPUT, `${size.width}x${size.height}-v2-home.png`), fullPage: true });
  }
  expect(oldCalls).toEqual([]);
});

test("P09.1-C: an awaiting pretest never displays fictitious scores or stars", async ({ page, request, context }) => {
  test.setTimeout(90000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const supervisor = await request.post(`${API_URL}/auth/login`, { data: { username: USERNAME, password: PASSWORD } });
  expect(supervisor.status()).toBe(200);
  const student = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب قبلي V2 ${Date.now()}`, grade_level: 3 },
  });
  expect(student.status()).toBe(201);
  const code = (await student.json()).access_code as string;
  const signedIn = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: code } });
  expect(signedIn.status()).toBe(200);
  const token = signedIn.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(token).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: token!, domain: "localhost", path: "/", httpOnly: true, secure: false, sameSite: "Lax" }]);

  await page.route("**/api/v2/student/home", route => route.fulfill({ json: {
    mode: "v2", test_only: true,
    student: { id: 90002, full_name: "طالب جديد", grade_level: 3 },
    current_action: {
      action: "assessment", state: "placement_pending_review", kind: "pretest",
      href: "/student/assessment-v2/80", label: "عرض حالة المراجعة",
    },
    journey: {
      placement_state: "in_progress", current_level: 1,
      current_lesson_id: null, content_release_version: "v2-candidate",
    },
    progress: {
      completed_lessons: 0, assigned_lessons: null, skipped_by_placement: 0,
      pending_review: 0, display_percent: null,
    },
    assessments: { pretest: { session_id: 80, state: "placement_pending_review", official: false, score_percent: null }, posttest: null },
    rewards: { state: "not_implemented_v2" }, data_status: "ready",
  } }));
  await page.route("**/api/v2/retries/student/tasks?*", route => route.fulfill({ json: { items: [], next_offset: null } }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/student");
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  await expect(page.getByRole("heading", { name: "بانتظار تحديد مستواك" })).toBeVisible();
  await expect(page.getByText("يظهر تقدم الدروس بعد اعتماد التسكين.")).toBeVisible();
  await expect(page.getByTestId("student-primary-action")).toHaveText("عرض حالة المراجعة");
  await expect(page.locator("[data-testid='student-progress-overview']")).toHaveCount(0);
  await expect(page.getByText("0%", { exact: true })).toHaveCount(0);
});


test("P0: first real login starts V2 pretest and resumes a saved answer after refresh", async ({ page, request }) => {
  test.setTimeout(150000);
  if (!PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  const admin = await request.post(`${API_URL}/auth/login`, { data: { username: USERNAME, password: PASSWORD } });
  expect(admin.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب P0 تجريبي ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const code = (await created.json()).access_code as string;

  const previousApis: string[] = [];
  page.on("request", req => {
    if (/\/api\/(profile|activities\/status|journey|rewards)(?:\?|$)/.test(req.url())) previousApis.push(req.url());
  });
  await page.goto("/student/login");
  await page.getByTestId("input-access-code").fill(code);
  await page.getByTestId("student-login-submit").click();
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  await expect(page.getByTestId("student-primary-action")).toHaveText("ابدأ الاختبار القبلي");
  const startReply = page.waitForResponse(reply =>
    reply.request().method() === "POST" &&
    new URL(reply.url()).pathname === "/api/v2/assessments/pretest/start");
  await page.getByTestId("student-primary-action").click();
  const opened = await startReply;
  const startBody = await opened.json().catch(() => null);
  expect(opened.status(), JSON.stringify({
    status: opened.status(),
    detail: typeof startBody?.detail === "string" ? startBody.detail : null,
    request_id: opened.headers()["x-request-id"] ?? null,
  })).toBe(200);
  await expect(page).toHaveURL(/\/student\/assessment-v2\/\d+$/);
  const sessionId = Number(page.url().split("/").at(-1));
  const first = await page.evaluate(async id => {
    const response = await fetch(`/api/v2/assessments/sessions/${id}`);
    return { status: response.status, data: await response.json() };
  }, sessionId);
  expect(first.status).toBe(200);
  expect(first.data.interaction.question.question_id).toBe("V2-PRE-Q01");
  expect(first.data.session.progress.answered).toBe(0);
  const question = first.data.interaction.question;
  expect(["choose_one", "listen_choose_one", "choose_image"]).toContain(question.interaction);
  expect(question.options.length).toBeGreaterThan(0);
  await expect(page.getByTestId("v2-interaction-player")).toBeVisible();
  await page.getByRole("link", { name: "لوحة الطالب" }).click();
  await expect(page).toHaveURL(/\/student$/);
  await page.getByTestId("student-primary-action").click();
  await expect(page).toHaveURL(new RegExp(`/student/assessment-v2/${sessionId}$`));
  const answerReply = page.waitForResponse(reply =>
    reply.request().method() === "POST" &&
    new URL(reply.url()).pathname === `/api/v2/assessments/sessions/${sessionId}/answers`);
  await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
  await page.getByRole("button", { name: "حفظ الإجابة والمتابعة" }).click();
  const answer = await answerReply;
  const answerBody = await answer.json();
  expect(answer.status(), JSON.stringify({ status: answer.status(), detail: answerBody?.detail ?? null })).toBe(200);
  expect(answerBody.assessment.session.progress.answered).toBe(1);
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
  await page.reload();
  const resumed = await page.evaluate(async id => {
    const response = await fetch(`/api/v2/assessments/sessions/${id}`);
    return { status: response.status, data: await response.json() };
  }, sessionId);
  expect(resumed.status).toBe(200);
  expect(resumed.data.session.session_id).toBe(sessionId);
  expect(resumed.data.session.progress.answered).toBe(1);
  expect(resumed.data.interaction.question.question_id).not.toBe(question.question_id);
  // A temporary read outage must not strand the child on a permanent error screen.
  let failOnce = true;
  await page.route(`**/api/v2/assessments/sessions/${sessionId}`, async route => {
    if (failOnce) {
      failOnce = false;
      return route.fulfill({ status: 503, json: { detail: "temporary outage" } });
    }
    return route.continue();
  });
  await page.goto(`/student/assessment-v2/${sessionId}`);
  await expect(page.getByRole("alert")).toContainText("تعذر استعادة التقييم");
  await expect(page.getByRole("button", { name: "إعادة المحاولة" })).toBeVisible();
  await page.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("v2-interaction-player")).toContainText("2 من 30");
  await page.unroute(`**/api/v2/assessments/sessions/${sessionId}`);
  await page.goto("/student");
  await expect(page.getByTestId("student-primary-action")).toHaveText("متابعة الاختبار");
  await page.getByTestId("student-primary-action").click();
  await expect(page).toHaveURL(new RegExp(`/student/assessment-v2/${sessionId}$`));
  expect(previousApis).toEqual([]);
});
