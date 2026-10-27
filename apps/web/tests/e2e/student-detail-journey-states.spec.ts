import { test, expect, APIRequestContext, BrowserContext, Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

type JourneyLevelState = "locked" | "active" | "completed" | "skipped" | "ready";

type JourneyLevel = {
  level_id: number;
  name: string;
  state: JourneyLevelState;
  completed_items: number;
  total_items: number;
  session_id: number | null;
};

type JourneySummary = {
  pretest_completed: boolean;
  starting_level: number | null;
  current_level: number;
  levels: JourneyLevel[];
  learning_journey_completed: boolean;
  posttest_enabled: boolean;
  posttest_completed: boolean;
  posttest_ready: boolean;
};

const LEVEL_NAMES: Record<number, string> = {
  1: "الاستعداد للقراءة",
  2: "بناء الكلمة",
  3: "الطلاقة والفهم",
};

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

function level(levelId: number, state: JourneyLevelState, completedItems = 0, sessionId: number | null = null): JourneyLevel {
  return {
    level_id: levelId,
    name: LEVEL_NAMES[levelId],
    state,
    completed_items: completedItems,
    total_items: 10,
    session_id: sessionId,
  };
}

function journey(overrides: Partial<JourneySummary> & Pick<JourneySummary, "levels">): JourneySummary {
  return {
    pretest_completed: true,
    starting_level: 1,
    current_level: 1,
    learning_journey_completed: false,
    posttest_enabled: false,
    posttest_completed: false,
    posttest_ready: false,
    ...overrides,
  };
}

async function openJourneyWithFixture(page: Page, studentId: number, summary: JourneySummary) {
  await page.route(`**/api/researcher/students/${studentId}/journey`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(summary),
    });
  });
  await page.goto(`/admin/students/${studentId}`);
  await page.getByRole("button", { name: "المسار والتقدم" }).click();
  await expect(page.getByRole("progressbar", { name: "تقدم الأنشطة الأساسية في المستوى النشط" })).toBeVisible({ timeout: 10000 });
}

function levelCard(page: Page, levelId: number) {
  return page.locator(`[data-level-state]`).filter({ hasText: `المستوى ${levelId}` });
}

test.describe("Student Detail canonical Journey states", () => {
  test.beforeEach(async ({ request, context }) => {
    await loginAsSupervisor(request, context);
  });

  test("placement-skipped levels stay skipped and are never presented as completed", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب مسار متجاوز ${Date.now()}`);
    await openJourneyWithFixture(page, student.id, journey({
      starting_level: 3,
      current_level: 3,
      levels: [level(1, "skipped"), level(2, "skipped"), level(3, "ready")],
    }));

    const level1 = levelCard(page, 1);
    const level2 = levelCard(page, 2);
    await expect(level1).toHaveAttribute("data-level-state", "skipped");
    await expect(level2).toHaveAttribute("data-level-state", "skipped");
    await expect(level1.getByText("تم تجاوزه وفق نقطة البداية", { exact: true })).toBeVisible();
    await expect(level2.getByText("تم تجاوزه وفق نقطة البداية", { exact: true })).toBeVisible();
    await expect(level1.getByText("مكتمل", { exact: true })).toHaveCount(0);
    await expect(level2.getByText("مكتمل", { exact: true })).toHaveCount(0);
  });

  test("manual override pointer does not manufacture historical completion", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب تجاوز يدوي ${Date.now()}`);
    await openJourneyWithFixture(page, student.id, journey({
      starting_level: 1,
      current_level: 3,
      levels: [level(1, "locked"), level(2, "locked"), level(3, "ready")],
    }));

    await expect(levelCard(page, 1)).toHaveAttribute("data-level-state", "locked");
    await expect(levelCard(page, 2)).toHaveAttribute("data-level-state", "locked");
    await expect(levelCard(page, 3)).toHaveAttribute("data-level-state", "ready");
    await expect(page.locator('[data-level-state="completed"]')).toHaveCount(0);
    await expect(levelCard(page, 3).getByText("جاهز للبدء", { exact: true })).toBeVisible();
  });

  test("early promotion completion remains completed even below ten core items", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب ترقية مبكرة ${Date.now()}`);
    await openJourneyWithFixture(page, student.id, journey({
      current_level: 2,
      levels: [level(1, "completed", 6, 101), level(2, "active", 2, 202), level(3, "locked")],
    }));

    const level1 = levelCard(page, 1);
    await expect(level1).toHaveAttribute("data-level-state", "completed");
    await expect(level1.getByText("مكتمل", { exact: true })).toBeVisible();
    await expect(level1.getByText("6 من 10 أساسي", { exact: true })).toBeVisible();
    await expect(levelCard(page, 2)).toHaveAttribute("data-level-state", "active");
    await expect(levelCard(page, 2).getByText("قيد التعلم", { exact: true })).toBeVisible();
  });

  test("completed L3 is rendered from canonical completion evidence", async ({ page, request }) => {
    const student = await createStudent(page, request, `طالب رحلة مكتملة ${Date.now()}`);
    await openJourneyWithFixture(page, student.id, journey({
      current_level: 3,
      learning_journey_completed: true,
      posttest_enabled: true,
      posttest_ready: true,
      levels: [level(1, "completed", 10, 301), level(2, "completed", 10, 302), level(3, "completed", 10, 303)],
    }));

    await expect(page.locator('[data-level-state="completed"]')).toHaveCount(3);
    await expect(levelCard(page, 3).getByText("مكتمل", { exact: true })).toBeVisible();
    await expect(levelCard(page, 3).getByText("10 من 10 أساسي", { exact: true })).toBeVisible();
  });
});
