import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const DIR = path.join(process.cwd(), "playwright-report", "screenshots", "p09-v2-assessment");

type AssessmentState = "answering" | "waiting_review" | "placement_pending_review" | "completed";

function assessment(state: AssessmentState) {
  return {
    session: { session_id: 777, kind: "pretest", state, progress: { answered: state === "answering" ? 11 : 30, total: 30 } },
    interaction: state === "answering" ? {
      question: {
        question_id: "V2-PRE-Q12", role: "pretest", interaction: "build_word",
        prompt: "رتّب الحروف لتكوّن اسم الأداة التي نكتب بها.",
        stimulus: { text: null, media: [] },
        options: [
          { id: "tile_01", text: "م", media: [] },
          { id: "tile_02", text: "ق", media: [] },
          { id: "tile_03", text: "ل", media: [] },
        ],
        hint: null,
      },
      media: {},
      progress: { index: 12, total: 30, stage: "pretest" },
      attempts: 0,
      draft: null,
    } : null,
    summary: { pending_review: state === "waiting_review" ? 1 : 0 },
    outcome: state === "completed" ? { score_percent: null, skills: {} } : undefined,
  };
}

test("P09.0 V2 pretest states are readable without answer leakage at mobile, tablet and desktop sizes", async ({ page, request, context }) => {
  test.setTimeout(150000);
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  await mkdir(DIR, { recursive: true });
  const supervisor = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(supervisor.status()).toBe(200);
  const created = await request.post(`${API_URL}/researcher/students`, {
    data: { full_name: `طالب فحص الواجهات ${Date.now()}`, grade_level: 3 },
  });
  expect(created.status()).toBe(201);
  const accessCode = (await created.json()).access_code as string;
  const signedIn = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(signedIn.status()).toBe(200);
  const token = signedIn.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(token).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: token!, domain: "localhost", path: "/", httpOnly: true, secure: false, sameSite: "Lax" }]);

  let state: AssessmentState = "answering";
  await page.route("**/api/v2/assessments/sessions/777", route => route.fulfill({ json: assessment(state) }));
  const sizes = [
    { width: 360, height: 800 },
    { width: 390, height: 844 },
    { width: 430, height: 932 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ];
  const states: AssessmentState[] = ["answering", "waiting_review", "placement_pending_review", "completed"];
  for (const size of sizes) {
    await page.setViewportSize(size);
    for (const mode of states) {
      state = mode;
      await page.goto("/student/assessment-v2/777");
      await expect(page.getByRole("heading", { name: "الاختبار القبلي", exact: true })).toBeVisible();
      if (mode === "answering") {
        await expect(page.getByText("رتّب الحروف لتكوّن اسم الأداة التي نكتب بها.")).toBeVisible();
        await expect(page.getByText(/تلميح:/)).toHaveCount(0);
      } else {
        const sectionName = {
          waiting_review: "إجاباتك محفوظة وتنتظر المراجعة",
          placement_pending_review: "اكتمل الاختبار وينتظر التسكين",
          completed: "اكتمل الاختبار القبلي",
        }[mode];
        await expect(page.getByRole("heading", { name: sectionName })).toBeVisible();
      }
      const bounds = await page.evaluate(() => ({
        scroll: document.documentElement.scrollWidth, viewport: window.innerWidth,
      }));
      expect(bounds.scroll, JSON.stringify({ size, mode, bounds })).toBeLessThanOrEqual(bounds.viewport + 1);
      await page.screenshot({
        path: path.join(DIR, `${size.width}x${size.height}-${mode}.png`),
        fullPage: true,
      });
    }
  }
});
