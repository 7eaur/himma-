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
  reward_count_before: number;
  completion_session_id: number;
  promotion_decision_id: number;
};

type Reward = {
  id: number;
  type: "stars" | "badge";
  key: string | null;
  label: string;
  catalog_version: string | null;
  asset_id: string | null;
  asset_path: string | null;
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

function createRewardFixture(): RewardFixture {
  const apiRoot = path.resolve(__dirname, "../../../../services/api");
  const script = path.join(apiRoot, "tests/support/w6_reward_fixture.py");
  const output = execFileSync("python", [script], {
    cwd: apiRoot,
    env: process.env,
    encoding: "utf8",
  }).trim();
  const payload = JSON.parse(output.split(/\r?\n/).at(-1) ?? "{}") as RewardFixture;
  expect(payload.student_id).toBeGreaterThan(0);
  expect(payload.access_code).toMatch(/^\d{6}$/);
  expect(payload.reward_count_before).toBe(0);
  return payload;
}

async function rewardsFromCurrentBrowser(page: import("@playwright/test").Page, url: string): Promise<Reward[]> {
  return page.evaluate(async (target) => {
    const response = await fetch(target, { cache: "no-store" });
    if (!response.ok) throw new Error(`Reward request failed: ${response.status}`);
    return response.json();
  }, url);
}

test("W6 reward lifecycle awards once, resolves the canonical asset, and survives Student/Admin refresh", async ({ page, context, request }) => {
  const fixture = createRewardFixture();

  await loginAsStudent(request, context, fixture.access_code);
  await page.goto("/student");
  await expect(page.getByTestId("student-home")).toBeVisible({ timeout: 15000 });

  const studentBadge = page.locator('[data-reward-key="level:1:core-complete"]');
  await expect(studentBadge).toHaveCount(1);
  await expect(studentBadge).toContainText("مستكشف الحروف");
  const studentBadgeImage = studentBadge.getByRole("img", { name: "شارة مستكشف الحروف" });
  await expect(studentBadgeImage).toBeVisible();
  await expect(studentBadgeImage).toHaveAttribute("src", /hem-bdg-04-letter-explorer\.svg/);

  const firstRewards = await rewardsFromCurrentBrowser(page, "/api/rewards");
  const firstBadge = firstRewards.filter((reward) => reward.key === "level:1:core-complete");
  expect(firstBadge).toHaveLength(1);
  expect(firstBadge[0]).toMatchObject({
    type: "badge",
    label: "مستكشف الحروف",
    catalog_version: "HIMMA_REWARD_CATALOG_1.0.0",
    asset_id: "BDG-04",
    asset_path: "/assets/rewards/svg/hem-bdg-04-letter-explorer.svg",
  });

  const assetResponse = await request.get(`${BASE_URL}${firstBadge[0].asset_path}`);
  expect(assetResponse.status()).toBe(200);
  expect(assetResponse.headers()["content-type"] ?? "").toContain("image/svg+xml");

  const secondRewards = await rewardsFromCurrentBrowser(page, "/api/rewards");
  const secondBadge = secondRewards.filter((reward) => reward.key === "level:1:core-complete");
  expect(secondBadge).toHaveLength(1);
  expect(secondBadge[0].id).toBe(firstBadge[0].id);

  await page.reload();
  await expect(page.locator('[data-reward-key="level:1:core-complete"]')).toHaveCount(1);

  await context.clearCookies();
  await loginAsSupervisor(request, context);
  await page.goto(`/admin/students/${fixture.student_id}`);
  await expect(page.getByRole("heading", { name: fixture.name })).toBeVisible({ timeout: 15000 });

  const adminBadge = page.getByTestId("canonical-reward-badge").filter({ hasText: "مستكشف الحروف" });
  await expect(adminBadge).toHaveCount(1);
  await expect(adminBadge).toHaveAttribute("data-reward-key", "level:1:core-complete");
  await expect(adminBadge.getByRole("img", { name: "شارة مستكشف الحروف" })).toBeVisible();

  const adminRewards = await rewardsFromCurrentBrowser(page, `/api/researcher/students/${fixture.student_id}/rewards`);
  const adminBadgePayload = adminRewards.filter((reward) => reward.key === "level:1:core-complete");
  expect(adminBadgePayload).toHaveLength(1);
  expect(adminBadgePayload[0].id).toBe(firstBadge[0].id);

  await page.reload();
  await expect(page.getByTestId("canonical-reward-badge").filter({ hasText: "مستكشف الحروف" })).toHaveCount(1);
});
