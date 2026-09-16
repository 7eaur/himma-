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

test("W6 public entry routes expose security headers and pass broad axe WCAG A/AA blocking scan", async ({ page }) => {
  const landing = await page.goto("/");
  expect(landing).not.toBeNull();
  const headers = landing!.headers();
  const csp = headers["content-security-policy"] ?? "";
  expect(csp).toContain("default-src 'self'");
  expect(csp).toContain("frame-ancestors 'none'");
  expect(csp).toContain("object-src 'none'");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers["permissions-policy"]).toContain("microphone=(self)");
  await expect(page.locator("main")).toBeVisible();
  await expectNoBlockingAxeViolations(page, "landing");

  await page.goto("/student/login");
  await expect(page.getByRole("heading", { name: "مرحبًا يا بطل!" })).toBeVisible();
  await expectNoBlockingAxeViolations(page, "student login");

  await page.goto("/admin/login");
  await expect(page.getByRole("heading", { name: "مرحبًا بك" })).toBeVisible();
  await expectNoBlockingAxeViolations(page, "admin login");
});
