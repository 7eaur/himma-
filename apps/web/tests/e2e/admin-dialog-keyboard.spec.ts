import { test, expect, APIRequestContext, BrowserContext } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

async function loginAsSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, {
    data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD },
  });
  expect(response.status()).toBe(200);
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

test("mobile admin dialog traps keyboard focus, closes on Escape, and restores trigger focus", async ({ page, context, request }) => {
  await loginAsSupervisor(request, context);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: /مرحبًا،/ })).toBeVisible({ timeout: 10000 });

  const trigger = page.getByRole("button", { name: "فتح القائمة" });
  await trigger.focus();
  await expect(trigger).toBeFocused();
  await expect(trigger).toHaveAttribute("aria-expanded", "false");

  await trigger.press("Enter");
  const dialog = page.getByRole("dialog", { name: "قائمة لوحة المشرف" });
  await expect(dialog).toBeVisible();
  await expect(trigger).toHaveAttribute("aria-expanded", "true");

  const closeButton = dialog.getByRole("button", { name: "إغلاق القائمة" });
  await expect(closeButton).toBeFocused();
  await expect(page.locator("body")).toHaveCSS("overflow", "hidden");

  // Shift+Tab from the first focusable item must wrap to the final focusable item inside the dialog.
  await page.keyboard.press("Shift+Tab");
  const activeAfterBackwardWrap = await page.evaluate(() => {
    const dialogElement = document.querySelector('[role="dialog"][aria-label="قائمة لوحة المشرف"]');
    return Boolean(dialogElement && dialogElement.contains(document.activeElement));
  });
  expect(activeAfterBackwardWrap).toBe(true);
  await expect(dialog.getByRole("button", { name: "تسجيل الخروج" })).toBeFocused();

  // Tab from the final item wraps back to the first focusable item.
  await page.keyboard.press("Tab");
  await expect(closeButton).toBeFocused();

  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
});
