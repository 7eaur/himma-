import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;
const DIR = path.join(process.cwd(), "playwright-report", "screenshots", "p09-reviewed-recordings");

async function login(page: Page) {
  if (!USERNAME || !PASSWORD) throw new Error("E2E supervisor credentials required");
  await page.goto("/admin/login");
  await page.getByTestId("input-username").fill(USERNAME);
  await page.getByTestId("input-password").fill(PASSWORD);
  await page.getByTestId("login-submit").click();
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20000 });
}

const syntheticResults = {
  items: [
    {
      audio_id: 10001,
      response_id: 70001,
      student_id: 90001,
      student_name: "طالب تجريبي",
      question_id: "L1-01-IC-A03",
      lesson_id: "L1-01",
      kind: "lesson",
      is_correct: true,
      reviewed_at: "2026-10-25T17:00:00Z",
      duration_seconds: 11,
      evaluation_source: "supervisor",
      audio_url: "/api/v2/review/lessons/70001/audio",
    },
    {
      audio_id: 10002,
      response_id: 70002,
      student_id: 90002,
      student_name: "طالب تجريبي آخر",
      question_id: "V2-PRE-Q11",
      lesson_id: null,
      kind: "pretest",
      is_correct: false,
      reviewed_at: "2026-10-25T17:10:00Z",
      duration_seconds: 9,
      evaluation_source: "supervisor",
      audio_url: "/api/v2/assessments/admin/responses/70002/audio",
    },
  ],
  next_offset: null,
};

test("P09.0 reviewed audio archive visual states have private players and no overflow", async ({ page }) => {
  test.setTimeout(150000);
  await mkdir(DIR, { recursive: true });
  await login(page);

  const states = ["empty", "reviewed", "failed"] as const;
  let mode: typeof states[number] = "empty";
  await page.route("**/api/v2/review/reviewed-recordings?*", async route => {
    if (mode === "failed") return route.fulfill({
      status: 503, contentType: "application/json", body: JSON.stringify({ detail: "تعذر الاتصال بالأرشيف التجريبي" }),
    });
    await route.fulfill({ json: mode === "reviewed" ? syntheticResults : { items: [], next_offset: null } });
  });

  for (const size of [
    { width: 360, height: 800 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(size);
    for (const state of states) {
      mode = state;
      await page.goto("/admin/v2-reviewed-recordings");
      await expect(page.getByRole("heading", { level: 1, name: "التسجيلات التي اكتمل تقييمها" })).toBeVisible();
      if (state === "empty") {
        await expect(page.getByText("لا توجد تسجيلات مقيّمة لهذه التصفية")).toBeVisible();
        await expect(page.locator("audio")).toHaveCount(0);
      }
      if (state === "reviewed") {
        await expect(page.getByText("طالب تجريبي · L1-01-IC-A03")).toBeVisible();
        await expect(page.getByText("طالب تجريبي آخر · V2-PRE-Q11")).toBeVisible();
        await expect(page.getByText("تم تقييمه بواسطة المشرف")).toHaveCount(2);
        await expect(page.locator("audio")).toHaveCount(2);
        const urls = await page.locator("audio").evaluateAll(nodes =>
          nodes.map(node => (node as HTMLAudioElement).getAttribute("src"))
        );
        expect(urls).toEqual([
          "/api/v2/review/lessons/70001/audio",
          "/api/v2/assessments/admin/responses/70002/audio",
        ]);
        expect(JSON.stringify(urls)).not.toContain("storage_key");
      }
      if (state === "failed") {
        await expect(page.getByRole("alert")).toContainText("تعذر الاتصال بالأرشيف التجريبي");
        await expect(page.locator("audio")).toHaveCount(0);
        await expect(page.getByText("تعذر عرض التسجيلات")).toBeVisible();
      }
      const bounds = await page.evaluate(() => ({
        pageWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      }));
      expect(bounds.pageWidth, JSON.stringify({ size, state, bounds })).toBeLessThanOrEqual(bounds.innerWidth + 1);
      await page.screenshot({
        path: path.join(DIR, `${size.width}x${size.height}-${state}.png`),
        fullPage: false,
      });
    }
  }

  // Regression: a populated archive must not remain visible if a new
  // refresh fails. The previous student's player and pagination disappear.
  mode = "reviewed";
  await page.goto("/admin/v2-reviewed-recordings");
  await expect(page.locator("audio")).toHaveCount(2);
  mode = "failed";
  await page.getByRole("button", { name: "تحديث" }).click();
  await expect(page.getByRole("alert")).toContainText("تعذر الاتصال بالأرشيف التجريبي");
  await expect(page.locator("audio")).toHaveCount(0);
  await expect(page.getByText("تعذر عرض التسجيلات")).toBeVisible();

  // Out-of-order filter responses must not reintroduce an older student's audio.
  // Route handlers deliberately finish in reverse order.
  let openOld!: () => void;
  let sawOld!: () => void;
  let oldCompleted!: () => void;
  const holdOld = new Promise<void>(resolve => { openOld = resolve; });
  const oldStarted = new Promise<void>(resolve => { sawOld = resolve; });
  const oldFinished = new Promise<void>(resolve => { oldCompleted = resolve; });
  await page.route("**/api/v2/review/reviewed-recordings?*", async route => {
    const kind = new URL(route.request().url()).searchParams.get("kind");
    if (kind === "lesson") {
      sawOld();
      await holdOld;
      await route.fulfill({ json: { items: [syntheticResults.items[0]], next_offset: null } });
      oldCompleted();
      return;
    }
    await route.fulfill({ json: { items: [syntheticResults.items[1]], next_offset: null } });
  });
  await page.getByLabel("نوع النشاط").selectOption("lesson");
  await oldStarted;
  await page.getByLabel("نوع النشاط").selectOption("pretest");
  await expect(page.getByText("طالب تجريبي آخر · V2-PRE-Q11")).toBeVisible();
  openOld();
  await oldFinished;
  await expect(page.getByText("طالب تجريبي آخر · V2-PRE-Q11")).toBeVisible();
  await expect(page.getByText("طالب تجريبي · L1-01-IC-A03")).toHaveCount(0);
  await expect(page.locator("audio")).toHaveCount(1);
});
