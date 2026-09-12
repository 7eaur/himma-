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

async function createStudent(page: Page, request: APIRequestContext, name: string) {
  await page.goto("/admin/students/new");
  await page.getByTestId("input-student-name").fill(name);
  await page.getByTestId("submit-create-student").click();

  const codeEl = page.getByTestId("student-access-code");
  await expect(codeEl).toBeVisible({ timeout: 10000 });
  const accessCode = (await codeEl.textContent())?.trim() ?? "";
  expect(accessCode).toMatch(/^\d{6}$/);

  const studentsResponse = await request.get(`${API_URL}/researcher/students`);
  expect(studentsResponse.status()).toBe(200);
  const students: Array<{ id: number; access_code: string; full_name: string }> = await studentsResponse.json();
  const student = students.find((candidate) => candidate.access_code === accessCode);
  expect(student?.full_name).toBe(name);
  expect(student?.id).toBeTruthy();
  return student as { id: number; access_code: string; full_name: string };
}

async function failOnce(page: Page, urlPattern: string) {
  let calls = 0;
  await page.route(urlPattern, async (route) => {
    calls += 1;
    if (calls === 1) {
      await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "temporary test failure" }) });
      return;
    }
    await route.continue();
  });
  return () => calls;
}

test.describe("Student Detail partial-source truth states", () => {
  test.beforeEach(async ({ request, context }) => {
    await loginAsSupervisor(request, context);
  });

  test("rewards failure stays unavailable instead of becoming zero, then retry recovers", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب مكافآت جزئية ${Date.now()}`);
    const calls = await failOnce(page, `**/api/researcher/students/${student.id}/rewards`);

    await page.goto(`/admin/students/${student.id}`);
    await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible({ timeout: 10000 });

    const summary = page.getByRole("region", { name: "ملخص الطالب" });
    await expect(summary.getByText("النجوم")).toBeVisible();
    await expect(summary.getByText("—", { exact: true })).toBeVisible();

    const error = page.getByRole("status").filter({ hasText: "تعذر تحميل المكافآت" });
    await expect(error).toBeVisible();
    await error.getByRole("button", { name: "إعادة المحاولة" }).click();
    await expect(error).toBeHidden({ timeout: 10000 });
    expect(calls()).toBeGreaterThanOrEqual(2);
    await expect(summary.getByText("0", { exact: true })).toBeVisible();
  });

  test("journey failure does not fabricate progress and its retry restores canonical journey", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب مسار جزئي ${Date.now()}`);
    const calls = await failOnce(page, `**/api/researcher/students/${student.id}/journey`);

    await page.goto(`/admin/students/${student.id}`);
    await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: "المسار والتقدم" }).click();

    const error = page.getByRole("status").filter({ hasText: "تعذر تحميل المسار الأكاديمي" });
    await expect(error).toBeVisible();
    await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toHaveCount(0);

    await error.getByRole("button", { name: "إعادة المحاولة" }).click();
    await expect(error).toBeHidden({ timeout: 10000 });
    expect(calls()).toBeGreaterThanOrEqual(2);
    await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toBeVisible({ timeout: 10000 });
  });

  test("adaptation-history failure is explicit and retry restores the real empty state", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب سجل جزئي ${Date.now()}`);
    const calls = await failOnce(page, `**/api/researcher/students/${student.id}/adaptation/history`);

    await page.goto(`/admin/students/${student.id}`);
    await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: "التقوية والتكيف" }).click();

    const error = page.getByRole("status").filter({ hasText: "تعذر تحميل سجل التكيف" });
    await expect(error).toBeVisible();
    await expect(page.getByText("لا يوجد قرار تكيف محفوظ بعد.")).toHaveCount(0);

    await error.getByRole("button", { name: "إعادة المحاولة" }).click();
    await expect(error).toBeHidden({ timeout: 10000 });
    expect(calls()).toBeGreaterThanOrEqual(2);
    await expect(page.getByText("لا يوجد قرار تكيف محفوظ بعد.")).toBeVisible({ timeout: 10000 });
  });
});
