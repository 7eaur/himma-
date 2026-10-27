import { test, expect, APIRequestContext, BrowserContext, Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function loginAsSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status()).toBe(200);
  const cookieMatch = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/);
  expect(cookieMatch?.[1]).toBeTruthy();
  await context.addCookies([{
    name: "access_token",
    value: cookieMatch?.[1] ?? "",
    domain: "localhost",
    path: "/",
    httpOnly: true,
    sameSite: "Lax",
    secure: false,
  }]);
}

async function createStudent(page: Page, request: APIRequestContext) {
  const name = `طالب تكامل الأجهزة ${Date.now()}`;
  await page.goto("/admin/students/new");
  await page.getByTestId("input-student-name").fill(name);
  await page.getByTestId("submit-create-student").click();
  const codeEl = page.getByTestId("student-access-code");
  await expect(codeEl).toBeVisible({ timeout: 10000 });
  const accessCode = (await codeEl.textContent())?.trim() ?? "";
  const studentsResponse = await request.get(`${API_URL}/researcher/students`);
  expect(studentsResponse.status()).toBe(200);
  const students: Array<{ id: number; access_code: string }> = await studentsResponse.json();
  const student = students.find((candidate) => candidate.access_code === accessCode);
  expect(student?.id).toBeTruthy();
  return student!.id;
}

async function assertCanonicalState(page: Page, studentId: number) {
  await page.goto(`/admin/students/${studentId}`);
  await expect(page.getByTestId("supervisor-v2-overview")).toBeVisible();
  await expect(page.getByTestId("supervisor-v2-progress")).toHaveText("2 من 10 درس");
  await expect(page.getByRole("progressbar", { name: "تقدم دروس همة V2" })).toHaveAttribute("aria-valuenow", "20");
  const cards = page.getByTestId("supervisor-v2-lesson");
  await expect(cards).toHaveCount(3);
  await expect(cards.nth(0)).toHaveAttribute("data-level-state", "completed");
  await expect(cards.nth(1)).toHaveAttribute("data-level-state", "current");
  await expect(cards.nth(2)).toHaveAttribute("data-level-state", "not_started");
  await expect(page.getByRole("button", { name: "أرشيف V1 التاريخي" })).toHaveCount(0);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(overflow).toBeFalsy();
}

test("canonical V2 Student Detail truth is identical on mobile, tablet, and desktop", async ({ page, request, context }) => {
  await loginAsSupervisor(request, context);
  const studentId = await createStudent(page, request);
  const homeReply = await request.get(`${API_URL}/v2/student/admin/students/${studentId}/home`);
  expect(homeReply.status()).toBe(200);
  const home = await homeReply.json();
  home.journey = { placement_state: "placed", current_level: 2 };
  home.progress = { ...home.progress, completed_lessons: 2, assigned_lessons: 10, display_percent: 20 };
  home.lesson_overview = { state: "ready", content_release_version: "test", items: [
    { lesson_id: "L1-01", title: "الأول", level: "L1", state: "completed", session_id: 1 },
    { lesson_id: "L1-02", title: "الثاني", level: "L1", state: "current", session_id: null },
    { lesson_id: "L1-03", title: "الثالث", level: "L1", state: "not_started", session_id: null },
  ] };
  await page.route(`**/api/v2/student/admin/students/${studentId}/home`, route =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(home) }));
  for (const viewport of [
    { width: 320, height: 800 },
    { width: 768, height: 900 },
    { width: 1440, height: 1000 },
  ]) {
    await page.setViewportSize(viewport);
    await assertCanonicalState(page, studentId);
  }
});

test("Student360 never displays the previous student's identity or code during a client-side profile switch", async ({ page, request, context }) => {
  test.setTimeout(120000);
  await loginAsSupervisor(request, context);
  const unique = Date.now();
  const firstReply = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب عزل أ ${unique}`, grade_level: 3 },
  });
  const secondReply = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب عزل ب ${unique}`, grade_level: 3 },
  });
  expect(firstReply.status()).toBe(201);
  expect(secondReply.status()).toBe(201);
  const first = await firstReply.json() as { id: number; full_name: string; access_code: string };
  const second = await secondReply.json() as { id: number; full_name: string; access_code: string };
  expect(first.id).toBeGreaterThan(0);
  expect(second.id).toBeGreaterThan(0);

  await page.goto(`/admin/students/${first.id}`);
  await expect(page.getByRole("heading", { name: first.full_name })).toBeVisible();
  await page.getByRole("button", { name: "الحساب", exact: true }).click();
  await page.getByRole("button", { name: "إظهار الرمز" }).click();
  await expect(page.getByText(first.access_code, { exact: true })).toBeVisible();

  // Native history.pushState only changes the URL; it is not a reliable
  // Next dynamic-route transition for useParams. Exercise actual client-side
  // <Link> navigation through the supervisor's student list.
  const navigateViaStudentsList = async (name: string) => {
    await page.getByRole("link", { name: "العودة إلى الطلاب" }).click();
    await expect(page.getByRole("heading", { name: "الطلاب" })).toBeVisible();
    await page.getByRole("textbox", { name: "البحث عن طالب بالاسم" }).fill(name);
    await page.getByRole("link", { name, exact: true }).first().click();
  };

  let releaseSecond!: () => void;
  let secondIntercepted = false;
  const secondGate = new Promise<void>(resolve => { releaseSecond = resolve; });
  await page.route(`**/api/v2/student/admin/students/${second.id}/account`, async route => {
    secondIntercepted = true;
    await secondGate;
    await route.continue();
  });
  try {
    await navigateViaStudentsList(second.full_name);
    // Pending B identity must never render A's revealed access code.
    await expect.poll(() => secondIntercepted, { timeout: 15000 }).toBe(true);
    await expect(page).toHaveURL(new RegExp("/admin/students/" + second.id + "$"));
    await expect(page.getByRole("heading", { name: first.full_name })).toHaveCount(0);
    await expect(page.getByText(first.access_code, { exact: true })).toHaveCount(0);
  } finally {
    releaseSecond();
  }
  await expect(page.getByRole("heading", { name: second.full_name })).toBeVisible();
  await expect(page.getByText(first.access_code, { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "الحساب", exact: true }).click();
  await expect(page.getByText(second.access_code, { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "إظهار الرمز" }).click();
  await expect(page.getByText(second.access_code, { exact: true })).toBeVisible();
  await expect(page.getByText(first.access_code, { exact: true })).toHaveCount(0);

  // Repeat the real Link transition B -> A with delayed identity response.
  let releaseFirst!: () => void;
  let firstIntercepted = false;
  const firstGate = new Promise<void>(resolve => { releaseFirst = resolve; });
  await page.route(`**/api/v2/student/admin/students/${first.id}/account`, async route => {
    firstIntercepted = true;
    await firstGate;
    await route.continue();
  });
  try {
    await navigateViaStudentsList(first.full_name);
    await expect.poll(() => firstIntercepted, { timeout: 15000 }).toBe(true);
    await expect(page).toHaveURL(new RegExp("/admin/students/" + first.id + "$"));
    await expect(page.getByRole("heading", { name: second.full_name })).toHaveCount(0);
    await expect(page.getByText(second.access_code, { exact: true })).toHaveCount(0);
  } finally {
    releaseFirst();
  }
  await expect(page.getByRole("heading", { name: first.full_name })).toBeVisible();
  await page.getByRole("button", { name: "الحساب", exact: true }).click();
  await expect(page.getByText(first.access_code, { exact: true })).toHaveCount(0);

});

test("Student360 keeps identity visible when its V2 academic source fails and recovers", async ({ page, request, context }) => {
  await loginAsSupervisor(request, context);
  const reply = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب مصدر مستقل ${Date.now()}`, grade_level: 3 },
  });
  expect(reply.status()).toBe(201);
  const student = await reply.json() as { id: number; full_name: string };
  let requests = 0;
  await page.route(`**/api/v2/student/admin/students/${student.id}/home`, async route => {
    requests += 1;
    if (requests === 1) return route.abort("failed");
    await route.continue();
  });
  await page.goto(`/admin/students/${student.id}`);
  await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible();
  const error = page.getByRole("alert").filter({ hasText: "تعذر الاتصال" });
  await expect(error).toBeVisible();
  await expect(page.getByTestId("supervisor-v2-progress")).toHaveCount(0);
  await error.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByTestId("supervisor-v2-action")).toContainText("ابدأ الاختبار القبلي");
  expect(requests).toBeGreaterThanOrEqual(2);
  await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible();
});
