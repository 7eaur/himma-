import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const DIR = path.join(process.cwd(), "playwright-report", "screenshots", "p09-v2-assessment");

type AssessmentState = "answering" | "waiting_review" | "placement_pending_review" | "completed";

// TEST_ONLY geometric asset. It verifies that image-based choices remain
// visible after selection; it is not an educational image or answer key.
const TEST_ONLY_IMAGE = "data:image/svg+xml," + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="60"><rect x="8" y="8" width="64" height="44" rx="8" fill="#347fd9"/></svg>'
);

function assessment(state: AssessmentState) {
  return {
    session: { session_id: 777, kind: "pretest", state, progress: { answered: state === "answering" ? 11 : 30, total: 30 } },
    interaction: state === "answering" ? {
      question: {
        question_id: "V2-PRE-Q12", role: "pretest", interaction: "build_word",
        prompt: "رتّب الحروف لتكوّن اسم الأداة التي نكتب بها.",
        stimulus: { text: null, media: [] },
        options: [
          { id: "tile_01", text: "م", media: [{ media_id: "visual-test-only", kind: "image" }] },
          { id: "tile_02", text: "ق", media: [] },
          { id: "tile_03", text: "ل", media: [] },
        ],
        hint: null,
      },
      media: { "visual-test-only": { kind: "image", state: "ready", url: TEST_ONLY_IMAGE } },
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
  // The pending-review child view also requests the global retry inbox.
  // Fixture this read-only API too; a fake assessment ID must not turn the
  // screenshot into a 404/error-state by accident.
  await page.route(/\/api\/v2\/retries\/student\/tasks\?/, route =>
    route.fulfill({ json: { items: [], next_offset: null } })
  );
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
        // Exercise the real ordered-choice UI at every approved breakpoint,
        // rather than capturing only an empty tray. The selected image must
        // remain visible, its remove button must be touch-friendly, and
        // removing it must restore the original choice.
        await page.getByRole("button", { name: "اختيار الخيار 1" }).click();
        await page.getByRole("button", { name: "اختيار الخيار 2" }).click();
        const tray = page.getByLabel("الترتيب المختار");
        await expect(tray.getByRole("button")).toHaveCount(2);
        await expect(tray.getByRole("img", { name: "صورة العنصر 1" })).toBeVisible();
        const selectedBoxes = await tray.getByRole("button").evaluateAll((nodes) =>
          nodes.map((node) => {
            const rect = node.getBoundingClientRect();
            return { width: rect.width, height: rect.height, left: rect.left, right: rect.right };
          }),
        );
        for (const box of selectedBoxes) {
          expect(box.height, JSON.stringify({ size, box })).toBeGreaterThanOrEqual(44);
          expect(box.left, JSON.stringify({ size, box })).toBeGreaterThanOrEqual(-1);
          expect(box.right, JSON.stringify({ size, box })).toBeLessThanOrEqual(size.width + 1);
        }
        await page.screenshot({
          path: path.join(DIR, `${size.width}x${size.height}-answering-selected-image.png`),
          fullPage: true,
        });
        await tray.getByRole("button", { name: "إزالة العنصر 1 من الترتيب" }).click();
        await expect(page.getByRole("button", { name: "اختيار الخيار 1" })).toBeEnabled();
        await expect(tray.getByRole("img", { name: "صورة العنصر 1" })).toHaveCount(0);
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
