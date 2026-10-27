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

const canonicalJourney = {
  pretest_completed: true,
  starting_level: 1,
  current_level: 2,
  learning_journey_completed: false,
  posttest_enabled: false,
  posttest_completed: false,
  posttest_ready: false,
  levels: [
    { level_id: 1, name: "الاستعداد للقراءة", state: "completed", completed_items: 6, total_items: 10, session_id: 501 },
    { level_id: 2, name: "بناء الكلمة", state: "active", completed_items: 2, total_items: 10, session_id: 502 },
    { level_id: 3, name: "الطلاقة والفهم", state: "locked", completed_items: 0, total_items: 10, session_id: null },
  ],
};

async function assertCanonicalState(page: Page, studentId: number) {
  await page.goto(`/admin/students/${studentId}`);
  if (await page.getByRole("button", { name: "أرشيف V1 التاريخي", exact: true }).getAttribute("aria-expanded") === "false")
    await page.getByRole("button", { name: "أرشيف V1 التاريخي", exact: true }).click();
  await page.getByRole("button", { name: "المسار والتقدم" }).click();
  const cards = page.locator("[data-level-state]");
  await expect(cards).toHaveCount(3);
  await expect(cards.filter({ hasText: "المستوى 1" })).toHaveAttribute("data-level-state", "completed");
  await expect(cards.filter({ hasText: "المستوى 1" }).getByText("6 من 10 أساسي", { exact: true })).toBeVisible();
  await expect(cards.filter({ hasText: "المستوى 2" })).toHaveAttribute("data-level-state", "active");
  await expect(cards.filter({ hasText: "المستوى 3" })).toHaveAttribute("data-level-state", "locked");
  await expect(page.locator('[data-level-state="skipped"]')).toHaveCount(0);
  await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toHaveAttribute("aria-valuenow", "2");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(overflow).toBeFalsy();
}

test("canonical Student Detail truth is identical on mobile, tablet, and desktop", async ({ page, request, context }) => {
  await loginAsSupervisor(request, context);
  const studentId = await createStudent(page, request);

  await page.route(`**/api/researcher/students/${studentId}/journey`, async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(canonicalJourney) });
  });

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

test("Student360 keeps the selected profile visible when an optional V1 source fails at network level", async ({ page, request, context }) => {
  await loginAsSupervisor(request, context);
  const reply = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب مصدر مستقل ${Date.now()}`, grade_level: 3 },
  });
  expect(reply.status()).toBe(201);
  const student = await reply.json() as { id: number; full_name: string };
  let journeyRequests = 0;
  await page.route(`**/api/researcher/students/${student.id}/journey`, async route => {
    journeyRequests += 1;
    if (journeyRequests === 1) {
      await route.abort("failed");
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(canonicalJourney) });
  });

  await page.goto(`/admin/students/${student.id}`);
  // Before the fix Promise.all rejected the whole profile when any
  // optional legacy source had a network error.
  await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible();
  await expect(page.getByTestId("supervisor-v2-overview")).toBeVisible();
  if (await page.getByRole("button", { name: "أرشيف V1 التاريخي", exact: true }).getAttribute("aria-expanded") === "false")
    await page.getByRole("button", { name: "أرشيف V1 التاريخي", exact: true }).click();
  await page.getByRole("button", { name: "المسار والتقدم" }).click();
  const failure = page.getByRole("status").filter({ hasText: "تعذر تحميل المسار الأكاديمي" });
  await expect(failure).toBeVisible();
  await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toHaveCount(0);
  await failure.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toBeVisible();
  expect(journeyRequests).toBeGreaterThanOrEqual(2);
  await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible();
});
