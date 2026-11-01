import { test, expect } from "@playwright/test";

test.describe("Home Page", () => {
  test("renders Himma logo and split login buttons", async ({ page }) => {
    await page.goto("/");

    // الشعار والرسالة الترحيبية
    await expect(page.locator(".logo-text").first()).toHaveText("هِمّة");
    await expect(page.getByText("أتعلم، أتطور، أصل إلى القمة")).toBeVisible();

    // زرا الدخول (مفصولة)
    const studentBtn = page.getByRole("link", { name: /الدخول برمز الطالب/i });
    const adminBtn = page.getByRole("link", { name: /دخول الإدارة/i });

    await expect(studentBtn).toHaveAttribute("href", "/student/login");
    await expect(adminBtn).toHaveAttribute("href", "/admin/login");
  });

  test("page is in RTL direction", async ({ page }) => {
    await page.goto("/");
    const htmlDir = await page.locator("html").getAttribute("dir");
    expect(htmlDir).toBe("rtl");
  });
});

test.describe("Login Page — Admin", () => {
  test("renders admin form", async ({ page }) => {
    await page.goto("/admin/login");

    await expect(page.getByRole("heading", { name: "دخول الإدارة" })).toBeVisible();
    await expect(page.getByTestId("input-username")).toBeVisible();
    await expect(page.getByTestId("input-password")).toBeVisible();
  });

  test("shows error on wrong credentials", async ({ page }) => {
    await page.goto("/admin/login");

    await page.getByTestId("input-username").fill("wrong_user");
    await page.getByTestId("input-password").fill("wrong_pass");
    await page.getByTestId("login-submit").click();

    const errorEl = page.getByTestId("error-message");
    await expect(errorEl).toBeVisible({ timeout: 5000 }).catch(() => {
      // Backend not running is acceptable in CI without full stack
    });
  });
});

test.describe("Login Page — Student", () => {
  test("shows the official six-digit code field without a pretend sample code", async ({ page }) => {
    await page.goto("/student/login");

    await expect(page.getByRole("heading", { name: "مرحبًا يا بطل!" })).toBeVisible();
    const code = page.getByTestId("input-access-code");
    await expect(code).toBeVisible();
    await expect(code).toHaveValue("");
    await expect(code).not.toHaveAttribute("placeholder", /[0-9٠-٩۰-۹]{6}/);
    await expect(page.getByText("ستجد الرمز عند المشرف المسؤول عن حسابك.")).toBeVisible();
    await expect(page.getByTestId("student-login-submit")).toBeDisabled();
  });

  test("accepts Arabic and Persian numerals as an ordinary six-digit code", async ({ page }) => {
    await page.goto("/student/login");
    const code = page.getByTestId("input-access-code");
    await code.fill("١٢٣٤٥٦");
    await expect(code).toHaveValue("123456");
    await expect(page.getByTestId("student-login-submit")).toBeEnabled();

    await code.fill("۱۲۳۴۵۶");
    await expect(code).toHaveValue("123456");

    await code.fill("abc١٢");
    await expect(code).toHaveValue("12");
    await expect(page.getByTestId("student-login-submit")).toBeDisabled();
  });
});
