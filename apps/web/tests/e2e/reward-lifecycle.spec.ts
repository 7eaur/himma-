import { execFileSync } from "child_process";
import path from "path";
import { test, expect, APIRequestContext, BrowserContext } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

type RewardFixture = {
  student_id: number;
  access_code: string;
  name: string;
};

async function installCookie(context: BrowserContext, response: Awaited<ReturnType<APIRequestContext["post"]>>) {
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

async function loginAsStudent(request: APIRequestContext, context: BrowserContext, accessCode: string) {
  const response = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(response.status()).toBe(200);
  await installCookie(context, response);
}

async function loginAsSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status()).toBe(200);
  await installCookie(context, response);
}

function createV2RewardFixture(): RewardFixture {
  const apiRoot = path.resolve(__dirname, "../../../../services/api");
  // This fixture rejects non-local databases and only creates an approved V2
  // journey/lesson evidence. The retired W6 fixture created a V1 core session.
  const script = path.join(apiRoot, "tests/support/v2_reward_fixture.py");
  const output = execFileSync("python", [script], {
    cwd: apiRoot,
    env: process.env,
    encoding: "utf8",
  }).trim();
  const payload = JSON.parse(output.split(/\r?\n/).at(-1) ?? "{}") as RewardFixture;
  expect(payload.student_id).toBeGreaterThan(0);
  expect(payload.access_code).toMatch(/^\d{6}$/);
  return payload;
}

test("W6 V2 rewards award once, survive refresh, and never reopen V1 reward routes", async ({ page, context, request }) => {
  const fixture = createV2RewardFixture();

  await loginAsStudent(request, context, fixture.access_code);
  await page.goto("/student");
  await expect(page.getByTestId("student-home")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
  await expect(page.getByTestId("v2-star-total")).toHaveText("0 نجمة");

  // The old rewards route cannot be used to earn V1 achievements in V2.
  const legacyStatus = await page.evaluate(async () =>
    (await fetch("/api/rewards", { cache: "no-store" })).status
  );
  expect(legacyStatus).toBe(409);
  await expect(page.getByTestId("student-badges")).toHaveCount(0);
  await expect(page.locator('[data-reward-key="level:1:core-complete"]')).toHaveCount(0);

  await context.clearCookies();
  await loginAsSupervisor(request, context);
  await page.goto(`/admin/students/${fixture.student_id}`);
  await expect(page.getByRole("heading", { name: fixture.name })).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("supervisor-v2-overview")).toBeVisible();
  await expect(page.getByTestId("v2-star-total")).toHaveText("0 نجمة");

  await page.getByRole("button", { name: "مزامنة الاستحقاقات المثبتة" }).click();
  await expect(page.getByTestId("v2-star-total")).toHaveText("3 نجمة");
  await page.getByRole("button", { name: "مزامنة الاستحقاقات المثبتة" }).click();
  await expect(page.getByText("تم التحقق من الاستحقاقات. منح جديدة: 0.")).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("v2-star-total")).toHaveText("3 نجمة");
  await expect(page.getByRole("button", { name: "أرشيف V1 التاريخي" })).toHaveCount(0);
  await expect(page.getByTestId("canonical-reward-badge")).toHaveCount(0);

  const adminHome = await request.get(`${API_URL}/v2/student/admin/students/${fixture.student_id}/home`);
  expect(adminHome.status()).toBe(200);
  const persisted = (await adminHome.json()).rewards;
  expect(persisted.source).toBe("himma_v2_reward_ledger");
  expect(persisted.total_stars).toBe(3);
  expect(persisted.lessons).toHaveLength(1);
  expect(persisted.badges).toHaveLength(0);

  const asset = await request.get(`${BASE_URL}/assets/rewards/svg/hem-bdg-04-letter-explorer.svg`);
  expect(asset.status()).toBe(200);
  expect(asset.headers()["content-type"] ?? "").toContain("image/svg+xml");

  await context.clearCookies();
  await loginAsStudent(request, context, fixture.access_code);
  await page.goto("/student");
  await expect(page.getByTestId("v2-star-total")).toHaveText("3 نجمة");
  await page.reload();
  await expect(page.getByTestId("v2-star-total")).toHaveText("3 نجمة");
  const studentHome = await request.get(`${API_URL}/v2/student/home`);
  expect(studentHome.status()).toBe(200);
  expect((await studentHome.json()).rewards).toEqual(persisted);
});
