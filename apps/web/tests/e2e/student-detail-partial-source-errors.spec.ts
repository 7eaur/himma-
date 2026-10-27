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

test.describe("V2 Student Detail source truth states", () => {
  test.beforeEach(async ({ request, context }) => {
    await loginAsSupervisor(request, context);
  });

  test("academic V2 failure shows an error, never a fabricated score, and retry recovers", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب مصدر V2 ${Date.now()}`);
    const calls = await failOnce(page, `**/api/v2/student/admin/students/${student.id}/home`);
    await page.goto(`/admin/students/${student.id}`);
    await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible();
    const error = page.getByRole("alert").filter({ hasText: "تعذر تحميل سجل هِمّة V2" });
    await expect(error).toBeVisible();
    await expect(page.getByTestId("supervisor-v2-level")).toHaveCount(0);
    await error.getByRole("button", { name: "إعادة المحاولة" }).click();
    await expect(page.getByTestId("supervisor-v2-action")).toContainText("ابدأ الاختبار القبلي");
    expect(calls()).toBeGreaterThanOrEqual(2);
  });

  test("failed account source cannot borrow a previous or V1 identity", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب حساب V2 ${Date.now()}`);
    const calls = await failOnce(page, `**/api/v2/student/admin/students/${student.id}/account`);
    await page.goto(`/admin/students/${student.id}`);
    await expect(page.getByRole("alert")).toContainText("temporary test failure");
    await expect(page.getByRole("heading", { name: student.full_name })).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible();
    expect(calls()).toBeGreaterThanOrEqual(2);
  });

  test("historical academic sources are not queried by the V2 profile", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب فصل تاريخي ${Date.now()}`);
    let oldRequests = 0;
    await page.route(`**/api/researcher/students/${student.id}/**`, route => {
      oldRequests += 1;
      return route.abort("failed");
    });
    await page.goto(`/admin/students/${student.id}`);
    await expect(page.getByTestId("supervisor-v2-action")).toContainText("ابدأ الاختبار القبلي");
    await expect(page.getByTestId("v2-star-total")).toHaveText("0 نجمة");
    expect(oldRequests).toBe(0);
    await expect(page.getByRole("button", { name: "أرشيف V1 التاريخي" })).toHaveCount(0);
  });
});
