import axe from "axe-core";
import { expect, test, type Page } from "@playwright/test";

type Violation = { id: string; impact: string | null; help: string; nodes: Array<{ target: string[] }> };
type AxeApi = { run: (root: Document, options: Record<string, unknown>) => Promise<{ violations: Violation[] }> };

async function expectNoBlockingAxeViolations(page: Page, label: string) {
  await page.addScriptTag({ content: axe.source });
  const violations = await page.evaluate(async () => {
    const api = (window as unknown as Window & { axe: AxeApi }).axe;
    const result = await api.run(document, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    return result.violations;
  });
  const blocking = violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical");
  expect(blocking, `${label}: ${JSON.stringify(blocking)}`).toEqual([]);
}

test("W6 public entry routes pass broad axe WCAG A/AA blocking scan", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("main")).toBeVisible();
  await expectNoBlockingAxeViolations(page, "landing");

  await page.goto("/student/login");
  await expect(page.getByRole("heading", { name: "مرحبًا يا بطل!" })).toBeVisible();
  await expectNoBlockingAxeViolations(page, "student login");

  await page.goto("/admin/login");
  await expect(page.getByRole("heading", { name: "مرحبًا بك" })).toBeVisible();
  await expectNoBlockingAxeViolations(page, "admin login");
});
