import { expect, test } from "@playwright/test";

test("serves Arabic typography without runtime Google Fonts requests", async ({ page }) => {
  const runtimeGoogleFontRequests: string[] = [];

  page.on("request", (request) => {
    const url = request.url();
    if (url.includes("fonts.googleapis.com") || url.includes("fonts.gstatic.com")) {
      runtimeGoogleFontRequests.push(url);
    }
  });

  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");

  const fontState = await page.locator("html").evaluate((node) => {
    const rootStyle = getComputedStyle(node);
    const bodyStyle = getComputedStyle(document.body);
    return {
      studentVariable: rootStyle.getPropertyValue("--font-tajawal").trim(),
      researcherVariable: rootStyle
        .getPropertyValue("--font-ibm-plex-sans-arabic")
        .trim(),
      bodyFamily: bodyStyle.fontFamily,
    };
  });

  expect(fontState.studentVariable).not.toBe("");
  expect(fontState.researcherVariable).not.toBe("");
  expect(fontState.bodyFamily).not.toBe("");
  expect(runtimeGoogleFontRequests).toEqual([]);
});
