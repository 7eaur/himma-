import { test, expect } from "@playwright/test";

// Former archive bookmark now lands on one native, read-only results surface.
// This test protects privacy, error recovery and mobile layout after the
// historic supervisor-review archive was retired from navigation.
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME;
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

test("old reviewed-recordings bookmark opens one native reading result list", async ({ page }) => {
  if (!SUPERVISOR_USERNAME || !SUPERVISOR_PASSWORD) throw new Error("E2E supervisor credentials required");
  await page.goto("/admin/login");
  await page.getByTestId("input-username").fill(SUPERVISOR_USERNAME);
  await page.getByTestId("input-password").fill(SUPERVISOR_PASSWORD);
  await page.getByTestId("login-submit").click();
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 20000 });

  let mode: "empty" | "results" | "error" = "results";
  await page.route("**/api/v2/reading/admin/results?*", route => {
    if (mode === "error") return route.fulfill({
      status: 503, json: { detail: "الخدمة غير متاحة" },
    });
    return route.fulfill({ json: mode === "empty"
      ? { items: [], total: 0, next_offset: null }
      : { items: [{
        job_id: 10001, student_id: 21, student_name: "طالب قراءة",
        question_id: "V2-PRE-Q08", reference: "وردة", kind: "word",
        session_kind: "assessment", result: "صحيحة", score_percent: null,
        created_at: "2026-11-02T11:00:00Z", has_audio: true,
      }], total: 1, next_offset: null } });
  });
  const resultsPanel = page.locator("section").filter({
    has: page.getByRole("heading", { name: "التسجيلات والنتائج", exact: true }),
  });
  for (const width of [360, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 850 });
    mode = "results";
    await page.goto("/admin/v2-reviewed-recordings");
    await expect(page).toHaveURL(/\/admin\/v2-review-center$/);
    await expect(page.getByRole("heading", { name: "متابعة القراءة الصوتية" })).toBeVisible();
    await expect(page.getByText("طالب قراءة")).toBeVisible();
    await expect(page.getByLabel("تسجيل قراءة طالب قراءة")).toHaveAttribute(
      "src", "/api/v2/reading/admin/jobs/10001/audio",
    );
    await expect(page.getByRole("button", { name: "القراءة صحيحة" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "طلب إعادة التسجيل" })).toHaveCount(0);
    const overflow = await page.evaluate(() => ({
      scroll: document.documentElement.scrollWidth, viewport: innerWidth,
    }));
    expect(overflow.scroll, JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.viewport + 1);
    mode = "error";
    await page.getByRole("button", { name: "تحديث النتائج" }).click();
    // Require the exact source error, not any unrelated page-level alert.
    // Refresh uses the always-visible header action; the transient inline
    // retry button is covered by an isolated component test. This removes a
    // race between error recovery and repeated viewport navigation.
    await expect(resultsPanel.getByRole("alert").filter({ hasText: "الخدمة غير متاحة" })).toBeVisible();
    await expect(page.getByText("طالب قراءة")).toHaveCount(0);
    await expect(page.locator("audio")).toHaveCount(0);
    mode = "empty";
    await page.getByRole("button", { name: "تحديث النتائج" }).click();
    await expect(page.getByText("لا توجد نتائج لهذه التصفية")).toBeVisible();
    // The framework may keep a separate empty route-announcement alert.
    // Require all request errors to disappear within the actual results panel.
    await expect(resultsPanel.getByRole("alert")).toHaveCount(0);
  }
});
