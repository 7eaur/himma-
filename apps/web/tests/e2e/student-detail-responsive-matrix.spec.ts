import { test, expect, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

const VIEWPORTS = [
  { name: "phone-320", width: 320, height: 720 },
  { name: "phone-360", width: 360, height: 800 },
  { name: "phone-390", width: 390, height: 844 },
  { name: "phone-430", width: 430, height: 932 },
  { name: "tablet-768", width: 768, height: 1024 },
  { name: "desktop-1440", width: 1440, height: 1000 },
] as const;

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

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
  }));

  expect(metrics.documentWidth, JSON.stringify(metrics)).toBeLessThanOrEqual(metrics.innerWidth + 1);
  expect(metrics.bodyWidth, JSON.stringify(metrics)).toBeLessThanOrEqual(metrics.innerWidth + 1);
}

async function expectUsableTarget(page: Page, testId: string) {
  const target = page.getByTestId(testId);
  await expect(target).toBeVisible();
  const box = await target.boundingBox();
  expect(box, `${testId} should have a measurable hit target`).not.toBeNull();
  expect(box?.height ?? 0, `${testId} should remain comfortably tappable`).toBeGreaterThanOrEqual(40);
}

test.describe("Student Detail deterministic responsive matrix", () => {
  test.beforeEach(async ({ request, context }) => {
    await loginAsSupervisor(request, context);
  });

  test("student detail, tabs, actions, and create form stay usable from 320px through desktop", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب استجابة ${Date.now()}`);

    for (const viewport of VIEWPORTS) {
      await test.step(viewport.name, async () => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });

        await page.goto(`/admin/students/${student.id}`);
        await expect(page.getByRole("heading", { name: student.full_name })).toBeVisible({ timeout: 10000 });
        await expectNoHorizontalOverflow(page);

        const journeyTab = page.getByRole("button", { name: "المسار والتقدم" });
        const adaptationTab = page.getByRole("button", { name: "التقوية والتكيف" });
        await expect(journeyTab).toBeVisible();
        await expect(adaptationTab).toBeVisible();

        await journeyTab.click();
        await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toBeVisible({ timeout: 10000 });
        await expectNoHorizontalOverflow(page);

        await adaptationTab.click();
        await expectNoHorizontalOverflow(page);

        await page.goto("/admin/students/new");
        await expect(page.getByTestId("input-student-name")).toBeVisible();
        await expectUsableTarget(page, "submit-create-student");
        await expectNoHorizontalOverflow(page);
      });
    }
  });
});
