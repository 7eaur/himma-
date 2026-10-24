import { expect, test, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ADMIN_USER = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const ADMIN_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function authenticate(request: APIRequestContext, context: BrowserContext,
                            endpoint: string, body: Record<string, string>) {
  const response = await request.post(`${API_URL}/auth/${endpoint}`, { data: body });
  expect(response.status()).toBe(200);
  const cookie = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{
    name: "access_token", value: cookie!, domain: "localhost",
    path: "/", httpOnly: true, sameSite: "Lax", secure: false,
  }]);
}

async function newStudent(page: Page, request: APIRequestContext, context: BrowserContext) {
  if (!ADMIN_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD required");
  await authenticate(request, context, "login", { username: ADMIN_USER, password: ADMIN_PASSWORD });
  await page.goto("/admin/students/new");
  await page.getByTestId("input-student-name").fill(`طالب حفظ مسودة V2 ${Date.now()}`);
  await page.getByTestId("submit-create-student").click();
  const code = (await page.getByTestId("student-access-code").textContent())?.trim() ?? "";
  expect(code).toMatch(/^\d{6}$/);
  await context.clearCookies();
  await authenticate(request, context, "student-login", { access_code: code });
}

test("P08 student rewrite draft survives refresh, does not become graded", async ({ page, request, context }) => {
  test.setTimeout(90000);
  await page.setViewportSize({ width: 390, height: 844 });
  await newStudent(page, request, context);

  // Stub only the P08 retry endpoints; student login/dashboard stay real.
  let privateDraft = "كلمة أولية";
  let saved = 0;
  let submitted = 0;
  await page.route("**/api/v2/retries/student/tasks?*", async (route) => {
    await route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        items: [{
          task_id: 151, kind: "lesson", session_id: 43,
          question_id: "L2-01-GP-03", status: "requested",
          request_kind: "rewrite", reason: "راجع الكلمة واكتبها بوضوح",
          prompt: "اكتب الكلمة مرة أخرى", draft_text: privateDraft,
        }], next_offset: null,
      }),
    });
  });
  await page.route("**/api/v2/retries/student/tasks/151/draft", async (route) => {
    expect(route.request().method()).toBe("POST");
    const payload = route.request().postDataJSON() as { text_response: string };
    privateDraft = payload.text_response;
    saved += 1;
    await route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ status: "draft_saved", task_id: 151, length: privateDraft.length }),
    });
  });
  await page.route("**/api/v2/retries/student/tasks/151/submit", async (route) => {
    submitted += 1;
    await route.fulfill({ status: 500, body: "Draft should not submit" });
  });

  await page.goto("/student");
  await expect(page.getByTestId("v2-active-retry-tasks")).toBeVisible();
  const answer = page.getByLabel("إجابتك الجديدة");
  await expect(answer).toHaveValue("كلمة أولية");
  await answer.fill("الجواب المحفوظ الخاص بالطالب");
  await page.getByRole("button", { name: "حفظ مسودة الكتابة" }).click();
  await expect(page.getByRole("status").filter({ hasText: "حُفظت مسودتك" })).toBeVisible();
  expect(saved).toBe(1);
  expect(submitted).toBe(0);

  await page.reload();
  await expect(page.getByTestId("v2-active-retry-tasks")).toBeVisible();
  await expect(page.getByLabel("إجابتك الجديدة")).toHaveValue("الجواب المحفوظ الخاص بالطالب");
  expect(saved).toBe(1);
  expect(submitted).toBe(0);
  const documentWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(documentWidth).toBeLessThanOrEqual(391);
});
