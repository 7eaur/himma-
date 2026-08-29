import { test, expect, Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const RESEARCHER_USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const RESEARCHER_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function loginSupervisor(page: Page) {
  if (!RESEARCHER_USERNAME || !RESEARCHER_PASSWORD) {
    throw new Error("E2E_RESEARCHER_USERNAME and E2E_RESEARCHER_PASSWORD are required");
  }

  await page.goto("/admin/login");
  await page.getByTestId("input-username").fill(RESEARCHER_USERNAME);
  await page.getByTestId("input-password").fill(RESEARCHER_PASSWORD);
  await page.getByTestId("login-submit").click();
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20_000 });
}

async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }));
  expect(metrics.document).toBeLessThanOrEqual(metrics.viewport + 1);
  expect(metrics.body).toBeLessThanOrEqual(metrics.viewport + 1);
}

test("Speech Lab exposes non-academic pronunciation and acoustic calibration evidence responsively", async ({ page }) => {
  const screenshots = path.join(process.cwd(), "playwright-report", "speech-lab-pronunciation");
  await mkdir(screenshots, { recursive: true });

  await loginSupervisor(page);
  await page.goto("/admin/speech-lab");
  await expect(page.getByTestId("pronunciation-reference-panel")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("acoustic-evidence-panel")).toBeVisible({ timeout: 15_000 });

  const search = page.getByPlaceholder("كلمة، مهارة، أو رمز المحتوى");
  await search.fill("كَتَبَ");

  const target = page.getByRole("button").filter({ hasText: /كَتَبَ/u }).first();
  await expect(target).toBeVisible({ timeout: 10_000 });
  await target.click();

  const pronunciationPanel = page.getByTestId("pronunciation-reference-panel");
  await expect(pronunciationPanel).toContainText("المرجع النطقي التجريبي");
  await expect(pronunciationPanel).toContainText("الحكم الصوتي على الحركة: غير معاير بعد");
  await expect(pronunciationPanel).toContainText("الحركة: فتحة");
  await expect(pronunciationPanel).toContainText("لا توجد درجة للحرف أو الحركة");

  const acousticPanel = page.getByTestId("acoustic-evidence-panel");
  await expect(acousticPanel).toContainText("خطة الأدلة الصوتية التجريبية");
  await expect(acousticPanel).toContainText("غير معاير — لا توجد درجة معتمدة");
  await expect(acousticPanel).toContainText("ثقة Azure ونتيجة التعرف النصي لا تتحولان إلى درجة نطق أو حركة");
  await expect(acousticPanel).toContainText("الحركة المرجعية: فتحة");
  await expect(acousticPanel).toContainText("لا تغيّر درجة الطالب ولا التكيف ولا التقوية");
  await expect(page.getByTestId("acoustic-score-0")).toHaveText("الدرجة الصوتية: —");
  await expect(page.getByTestId("acoustic-score-1")).toHaveText("الدرجة الصوتية: —");
  await expect(page.getByTestId("acoustic-score-2")).toHaveText("الدرجة الصوتية: —");

  await page.setViewportSize({ width: 1440, height: 900 });
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: path.join(screenshots, "desktop-1440x900-kataba.png"),
    fullPage: true,
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(pronunciationPanel).toBeVisible();
  await expect(acousticPanel).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.screenshot({
    path: path.join(screenshots, "mobile-390x844-kataba.png"),
    fullPage: true,
  });
});
