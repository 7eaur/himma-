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
