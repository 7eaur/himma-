import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

const lessons = [
  { lesson_id: "L1-01", title: "الحرف وصوته", level: "L1", state: "current", preview_enabled: true, session_id: null },
  { lesson_id: "L2-01", title: "أبني وأكتب كلمة بسيطة", level: "L2", state: "locked", preview_enabled: true, session_id: null },
  { lesson_id: "L3-03", title: "أفهم المعلومات المباشرة في النص", level: "L3", state: "locked", preview_enabled: true, session_id: null },
];

const SCREENSHOT_DIR = path.join(process.cwd(), "playwright-report", "screenshots", "p03");

function payload(stage: "intro" | "teaching_video" | "guided_practice", savedPosition = 0) {
  return {
    lesson_id: "L1-01", title: "الحرف وصوته", level: "L1", skill_group: "S1",
    objective: "أربط الحرف بصوته عند رؤيته أو سماعه.",
    intro: { title: "الحرف وصوته", text: "لكل حرف شكل نراه وصوت نسمعه.", button: "التالي" },
    video: { asset_id: "VID-L1-01", url: "/api/v2/lessons/test-fixtures/video/VID-L1-01", test_only: true, state: "ready" },
    practice: { count: 4, first_question_id: "L1-01-GP-01" },
    independent_check: { count: 4 },
    session: { session_id: 44, stage, status: "in_progress", step_index: 0, intro_seen: stage !== "intro", video_seen: stage === "guided_practice", video_position_seconds: stage === "guided_practice" ? 6 : savedPosition, video_duration_seconds: 6, version: 2, updated_at: "2026-10-21T12:00:00Z" },
  };
}

test("P03 lesson catalog, video state and P04 boundary remain responsive", async ({ page, request, context }) => {
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const supervisor = await request.post(`${API_URL}/auth/login`, { data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD } });
  expect(supervisor.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, { data: { full_name: `طالب P03 ${Date.now()}`, grade_level: 3 } });
  expect(created.status()).toBe(201);
  const accessCode = (await created.json()).access_code as string;
  const student = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(student.status()).toBe(200);
  const cookie = student.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(cookie).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: cookie!, domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);

  let stage: "intro" | "teaching_video" | "guided_practice" = "intro";
  let savedPosition = 0;
  await page.route("**/api/v2/lessons/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/catalog")) return route.fulfill({ json: { mode: "candidate_preview", test_only: true, release_version: "candidate", lessons } });
    if (url.pathname.endsWith("/L1-01/start")) return route.fulfill({ json: payload(stage, savedPosition) });
    if (url.pathname.endsWith("/sessions/44") && route.request().method() === "GET") return route.fulfill({ json: payload(stage, savedPosition) });
    if (url.pathname.endsWith("/sessions/44/events")) {
      const body = route.request().postDataJSON();
      if (body.event_type === "video_progress") savedPosition = body.position_seconds;
      stage = body.event_type === "video_ended" ? "guided_practice" : body.event_type === "intro_complete" ? "teaching_video" : stage;
      return route.fulfill({ json: payload(stage, savedPosition) });
    }
    return route.fallback();
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/student/learning-v2");
  await expect(page.getByRole("heading", { name: "رحلة درس واضحة ومحفوظة" })).toBeVisible();
  await expect(page.getByRole("button", { name: "معاينة الدرس" })).toHaveCount(3);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "mobile-390-catalog.png"), fullPage: true });

  await page.getByRole("button", { name: "معاينة الدرس" }).first().click();
  await expect(page).toHaveURL(/\/student\/learning-v2\/44$/);
  await expect(page.getByRole("heading", { name: "الحرف وصوته", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: /التالي/ }).click();
  const player = page.getByTestId("v2-video-player");
  await expect(player).toBeVisible();
  await expect(player.getByText(/TEST ONLY/)).toBeVisible();
  await expect(player.locator("video")).toHaveAttribute("controls", "");
  await expect.poll(() => player.locator("video").evaluate((element) => (element as HTMLVideoElement).duration)).toBeGreaterThan(0);

  const checkpointResponse = page.waitForResponse((response) => response.url().endsWith("/sessions/44/events") && response.request().postData()?.includes("video_progress") === true);
  await player.locator("video").evaluate((element) => {
    const video = element as HTMLVideoElement;
    video.currentTime = 5.5;
    video.dispatchEvent(new Event("timeupdate"));
  });
  await checkpointResponse;
  await page.reload();
  const resumedPlayer = page.getByTestId("v2-video-player");
  await expect(resumedPlayer).toBeVisible();
  await expect.poll(() => resumedPlayer.locator("video").evaluate((element) => (element as HTMLVideoElement).duration)).toBeGreaterThan(0);
  await expect.poll(() => resumedPlayer.locator("video").evaluate((element) => (element as HTMLVideoElement).currentTime)).toBeGreaterThanOrEqual(5.4);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "mobile-390-video-resumed.png"), fullPage: true });

  await resumedPlayer.locator("video").evaluate((video) => video.dispatchEvent(new Event("error")));
  await expect(resumedPlayer.getByRole("alert")).toContainText("تعذر تشغيل الفيديو");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "mobile-390-video-error.png"), fullPage: true });
  await resumedPlayer.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(resumedPlayer.getByRole("alert")).toHaveCount(0);

  await resumedPlayer.locator("video").evaluate((element) => {
    const video = element as HTMLVideoElement;
    video.currentTime = video.duration;
    video.dispatchEvent(new Event("ended"));
  });
  await expect(page.getByRole("heading", { name: /أصبح التدريب الموجّه جاهزًا/ })).toBeVisible();
  await expect(page.getByText(/حد P03 \/ P04/)).toBeVisible();
  await expect(page.getByRole("button", { name: /تجاوز|إكمال الدرس/ })).toHaveCount(0);

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "desktop-1440-guided-practice-boundary.png"), fullPage: true });
});
