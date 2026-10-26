import { expect, test } from "@playwright/test";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

const lessons = [
  { lesson_id: "L1-01", title: "الحرف وصوته", level: "L1", state: "current", preview_enabled: true, session_id: null },
  { lesson_id: "L2-01", title: "أبني وأكتب كلمة بسيطة", level: "L2", state: "locked", preview_enabled: false, session_id: null },
  { lesson_id: "L3-03", title: "أفهم المعلومات المباشرة في النص", level: "L3", state: "locked", preview_enabled: false, session_id: null },
];

const SCREENSHOT_DIR = path.join(process.cwd(), "playwright-report", "screenshots", "p05");
const VIDEO_FIXTURE = path.resolve(process.cwd(), "../../services/api/test_fixtures/himma-v2-video-test-only.mp4");
const CAPTIONS_FIXTURE = path.resolve(process.cwd(), "../../services/api/test_fixtures/himma-v2-video-test-only.vtt");

function payload(stage: "intro" | "teaching_video" | "guided_practice" | "support_practice", savedPosition = 0) {
  return {
    lesson_id: "L1-01", title: "الحرف وصوته", level: "L1", skill_group: "S1",
    objective: "أربط الحرف بصوته عند رؤيته أو سماعه.",
    intro: { title: "الحرف وصوته", text: "لكل حرف شكل نراه وصوت نسمعه.", button: "التالي" },
    video: { asset_id: "VID-L1-01", url: "/api/v2/lessons/test-fixtures/video/VID-L1-01", test_only: true, state: "ready" },
    practice: { count: 4, first_question_id: "L1-01-GP-01" },
    independent_check: { count: 4 },
    session: { session_id: 44, stage, status: "in_progress", step_index: 0, intro_seen: stage !== "intro", video_seen: stage === "guided_practice" || stage === "support_practice", video_position_seconds: stage === "guided_practice" || stage === "support_practice" ? 6 : savedPosition, video_duration_seconds: 6, version: 2, updated_at: "2026-10-21T12:00:00Z" },
    adaptation: stage === "support_practice" ? { state: "targeted_support", message: "لديك مساعدة قصيرة ثم تعود إلى مسارك.", support: { support_id: "SUP-01", title: "الحرف والصوت والتمييز", focus: "sound_mapping", mode: "targeted_support" } } : null,
    interaction: stage === "guided_practice" || stage === "support_practice" ? {
      question: {
        question_id: "L1-01-GP-01", owner_id: "L1-01", role: "guided_practice", interaction: "listen_choose_one",
        prompt: "استمع ثم اختر الحرف.", stimulus: { text: null, media: [] },
        options: [{ id: "a", text: "ب", media: [] }, { id: "b", text: "م", media: [] }, { id: "c", text: "س", media: [] }],
        skill_group: "S1", evidence_type: "sound_to_letter", presentation: {}, hint: "استمع إلى بداية كلمة بَاب.",
      },
      media: {}, progress: { index: 1, total: stage === "support_practice" ? 2 : 4, stage }, attempts: 0, draft: null,
    } : null,
  };
}

test("P03/P04 runtime and P05 targeted support remain responsive", async ({ page, request, context }) => {
  await mkdir(SCREENSHOT_DIR, { recursive: true });
  const videoBytes = await readFile(VIDEO_FIXTURE);
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

  let stage: "intro" | "teaching_video" | "guided_practice" | "support_practice" = "intro";
  let savedPosition = 0;
  let holdNextProgressResponse = false;
  let dropFirstCompletionAcknowledgment = true;
  const completionEventKeys: string[] = [];
  let releaseDelayedCheckpoint: (() => void) | undefined;
  let signalDelayedCheckpointStarted: (() => void) | undefined;
  const delayedCheckpointStarted = new Promise<void>((resolve) => { signalDelayedCheckpointStarted = resolve; });
  await page.route("**/api/v2/lessons/**", async (route) => {
    const url = new URL(route.request().url());
    // The M09 gate deliberately runs the API as `trial`, where TEST_ONLY media
    // is blocked. Fulfil only the already-mocked browser fixture here so the UI
    // contract stays deterministic without weakening the backend fail-closed test.
    if (url.pathname.endsWith("/test-fixtures/video/VID-L1-01/captions")) {
      return route.fulfill({ path: CAPTIONS_FIXTURE, contentType: "text/vtt; charset=utf-8" });
    }
    if (url.pathname.endsWith("/test-fixtures/video/VID-L1-01")) {
      const range = route.request().headers().range?.match(/^bytes=(\d+)-(\d*)$/);
      if (range) {
        const start = Number(range[1]);
        const requestedEnd = range[2] ? Number(range[2]) : videoBytes.length - 1;
        const end = Math.min(requestedEnd, videoBytes.length - 1);
        const body = videoBytes.subarray(start, end + 1);
        return route.fulfill({
          status: 206,
          contentType: "video/mp4",
          headers: {
            "Accept-Ranges": "bytes",
            "Content-Range": `bytes ${start}-${end}/${videoBytes.length}`,
            "Content-Length": String(body.length),
          },
          body,
        });
      }
      return route.fulfill({
        contentType: "video/mp4",
        headers: { "Accept-Ranges": "bytes", "Content-Length": String(videoBytes.length) },
        body: videoBytes,
      });
    }
    if (url.pathname.endsWith("/catalog")) return route.fulfill({ json: { mode: "candidate_preview", test_only: true, release_version: "candidate", lessons } });
    if (url.pathname.endsWith("/L1-01/start")) return route.fulfill({ json: payload(stage, savedPosition) });
    if (url.pathname.endsWith("/sessions/44/interaction") && route.request().method() === "GET") return route.fulfill({ json: payload(stage, savedPosition) });
    if (url.pathname.endsWith("/sessions/44/events")) {
      const body = route.request().postDataJSON();
      if (body.event_type === "video_progress") savedPosition = body.position_seconds;
      stage = body.event_type === "video_ended" ? "guided_practice" : body.event_type === "intro_complete" ? "teaching_video" : stage;
      const responsePayload = payload(stage, savedPosition);
      if (body.event_type === "video_ended") {
        completionEventKeys.push(body.event_key);
        if (dropFirstCompletionAcknowledgment) {
          // Simulate a committed server event whose acknowledgment was lost.
          // Retrying must not force the child to replay the video.
          dropFirstCompletionAcknowledgment = false;
          return route.fulfill({ status: 503, json: { detail: "Temporary completion acknowledgment failure" } });
        }
      }
      if (body.event_type === "video_progress" && holdNextProgressResponse) {
        holdNextProgressResponse = false;
        // Hold an earlier video-stage checkpoint until AFTER video_ended.
        // A stale reply must never move the UI back from practice to video.
        await new Promise<void>((resolve) => {
          releaseDelayedCheckpoint = resolve;
          signalDelayedCheckpointStarted?.();
        });
      }
      return route.fulfill({ json: responsePayload });
    }
    if (url.pathname.endsWith("/sessions/44/answers")) {
      return route.fulfill({ json: {
        status: "ok",
        submission: { question_id: "L1-01-GP-01", status: "graded", accepted: true, retry_required: true, correct: false, hint: "استمع إلى بداية كلمة بَاب.", message: "اقتربت! اقرأ التلميح ثم حاول مرة أخرى." },
        lesson: payload("guided_practice", savedPosition),
      } });
    }
    return route.fallback();
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/student/learning-v2");
  await expect(page.getByRole("heading", { name: "رحلة درس واضحة ومحفوظة" })).toBeVisible();
  await expect(page.getByRole("button", { name: "ابدأ الدرس" })).toHaveCount(1);
  await expect(page.getByRole("button", { name: "غير متاح الآن" })).toHaveCount(2);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "mobile-390-catalog.png"), fullPage: true });

  // P09.0 coverage expansion: same student, same pinned lesson state, varying
  // viewport without manufacturing success or a new completed lesson.
  for (const viewport of [
    { name: "phone-360", width: 360, height: 800 },
    { name: "phone-430", width: 430, height: 932 },
    { name: "tablet-768", width: 768, height: 1024 },
    { name: "desktop-1440", width: 1440, height: 900 },
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await expect(page.getByRole("button", { name: "ابدأ الدرس" })).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-catalog.png`), fullPage: true });
  }
  await page.setViewportSize({ width: 390, height: 844 });

  await page.getByRole("button", { name: "ابدأ الدرس" }).click();
  await expect(page).toHaveURL(/\/student\/learning-v2\/44$/);
  await expect(page.getByRole("heading", { name: "الحرف وصوته", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: /التالي/ }).click();
  const player = page.getByTestId("v2-video-player");
  await expect(player).toBeVisible();
  await expect(player.getByText(/TEST ONLY/)).toBeVisible();
  await expect(player.locator("video")).toHaveAttribute("controls", "");
  await expect.poll(() => player.locator("video").evaluate((element) => (element as HTMLVideoElement).duration)).toBeGreaterThan(0);

  const checkpointResponse = page.waitForResponse((response) => response.url().endsWith("/sessions/44/events") && response.request().postData()?.includes("video_progress") === true);
  await Promise.all([
    checkpointResponse,
    player.locator("video").evaluate((element) => {
      const video = element as HTMLVideoElement;
      // Chromium may not expose a seekable range for a route-fulfilled MP4 even
      // though its metadata is valid. Pin the observed time so this checks the
      // React checkpoint contract, while the following reload checks real resume.
      Object.defineProperty(video, "currentTime", { configurable: true, get: () => 5 });
      video.dispatchEvent(new Event("timeupdate", { bubbles: true }));
    }),
  ]);
  await page.reload();
  const resumedPlayer = page.getByTestId("v2-video-player");
  await expect(resumedPlayer).toBeVisible();
  await expect.poll(() => resumedPlayer.locator("video").evaluate((element) => (element as HTMLVideoElement).duration)).toBeGreaterThan(0);
  await expect.poll(() => resumedPlayer.locator("video").evaluate((element) => (element as HTMLVideoElement).currentTime)).toBeGreaterThanOrEqual(4.9);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "mobile-390-video-resumed.png"), fullPage: true });

  await resumedPlayer.locator("video").evaluate((video) => video.dispatchEvent(new Event("error")));
  await expect(resumedPlayer.getByRole("alert")).toContainText("تعذر تشغيل الفيديو");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "mobile-390-video-error.png"), fullPage: true });
  await resumedPlayer.getByRole("button", { name: "إعادة المحاولة" }).click();
  await expect(resumedPlayer.getByRole("alert")).toHaveCount(0);
  // load() resets media metadata; firing ended before duration is available
  // made this browser test flaky and skipped the real onEnded callback.
  await expect.poll(() => resumedPlayer.locator("video").evaluate((element) =>
    (element as HTMLVideoElement).duration)).toBeGreaterThan(0);

  // Reproduce a network race: an older playback checkpoint returns only
  // after the completion event has advanced the learner to guided practice.
  holdNextProgressResponse = true;
  await resumedPlayer.locator("video").evaluate((element) => {
    const video = element as HTMLVideoElement;
    Object.defineProperty(video, "currentTime", { configurable: true, get: () => 0 });
    video.dispatchEvent(new Event("timeupdate", { bubbles: true }));
  });
  await delayedCheckpointStarted;
  await resumedPlayer.locator("video").evaluate((element) => {
    const video = element as HTMLVideoElement;
    Object.defineProperty(video, "currentTime", { configurable: true, get: () => video.duration });
    video.dispatchEvent(new Event("ended", { bubbles: true }));
  });
  await expect(resumedPlayer.getByRole("alert")).toContainText("تعذر تأكيد حفظ المشاهدة");
  await expect(resumedPlayer.getByText("أكملت الشرح")).toHaveCount(0);
  await resumedPlayer.getByRole("button", { name: "إعادة حفظ المشاهدة" }).click();
  const interaction = page.getByTestId("v2-interaction-player");
  await expect(interaction).toBeVisible();
  expect(completionEventKeys).toHaveLength(2);
  expect(completionEventKeys[0]).toBe(completionEventKeys[1]);
  const delayedResponse = page.waitForResponse((response) =>
    response.url().endsWith("/sessions/44/events") &&
    response.request().postData()?.includes("video_progress") === true);
  releaseDelayedCheckpoint?.();
  await delayedResponse;
  // Allow the fetch continuation and React commit to run before asserting
  // that a stale checkpoint did not remount the video stage.
  await page.evaluate(() => new Promise<void>((resolve) =>
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await expect(interaction).toBeVisible();
  await expect(page.getByTestId("v2-video-player")).toHaveCount(0);
  await expect(interaction.getByRole("heading", { name: "استمع ثم اختر الحرف." })).toBeVisible();
  await interaction.getByRole("button", { name: "اختيار الخيار 2" }).click();
  await interaction.getByRole("button", { name: "تحقق من الإجابة" }).click();
  await expect(interaction.getByText("حاول مرة أخرى", { exact: true })).toBeVisible();
  await expect(interaction.getByText(/تلميح: استمع إلى بداية كلمة بَاب/)).toBeVisible();
  await expect(page.getByRole("button", { name: /تجاوز|إكمال الدرس/ })).toHaveCount(0);

  await page.setViewportSize({ width: 1440, height: 900 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "desktop-1440-guided-practice.png"), fullPage: true });

  stage = "support_practice";
  await page.reload();
  await expect(page.getByText("مساعدة قصيرة وليست خفضًا للمستوى")).toBeVisible();
  await expect(page.getByRole("heading", { name: "الحرف والصوت والتمييز" })).toBeVisible();
  await expect(page.getByText("مساعدة مركزة")).toBeVisible();
  await expect(page.getByText("لديك مساعدة قصيرة ثم تعود إلى مسارك.")).toBeVisible();
  await expect(page.getByText(/فشل|رسوب|نزول مستوى/)).toHaveCount(0);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "desktop-1440-targeted-support.png"), fullPage: true });
  for (const viewport of [
    { name: "phone-360", width: 360, height: 800 },
    { name: "phone-390", width: 390, height: 844 },
    { name: "tablet-768", width: 768, height: 1024 },
  ]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await expect(page.getByText("مساعدة قصيرة وليست خفضًا للمستوى")).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${viewport.name}-targeted-support.png`), fullPage: true });
  }
});
