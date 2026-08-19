import { test } from "@playwright/test";
import path from "path";
import fs from "fs";

const BASE = "http://localhost:3000";
const SCREENS_DIR = path.join(__dirname, "screenshots/p03");

const VIEWPORTS = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

const PAGES = [
  { route: "/", name: "welcome" },
  { route: "/admin/login", name: "admin-login" },
  { route: "/student/login", name: "student-login" },
];

test.describe("P03: Screenshots — all viewports", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENS_DIR, { recursive: true });
  });

  for (const vp of VIEWPORTS) {
    test(`Screenshots — ${vp.name} (${vp.width}px)`, async ({ browser }) => {
      const ctx = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        locale: "ar-SA",
      });
      const page = await ctx.newPage();

      for (const pg of PAGES) {
        await page.goto(`${BASE}${pg.route}`, { waitUntil: "networkidle" });
        await page.waitForTimeout(1000);
        const file = path.join(SCREENS_DIR, `${pg.name}-${vp.name}.png`);
        await page.screenshot({ path: file, fullPage: false });
        console.log(`[screenshot] ${pg.name}-${vp.name}.png`);
      }

      // Login to get admin screenshots
      await page.goto(`${BASE}/admin/login`, { waitUntil: "networkidle" });
      await page.locator('[data-testid="input-username"]').click();
      await page.keyboard.type("researcher1", { delay: 30 });
      await page.locator('[data-testid="input-password"]').click();
      await page.keyboard.type("securepass123", { delay: 30 });
      await page.locator('[data-testid="login-submit"]').click();
      await page.waitForTimeout(8000);

      const adminPages = [
        { route: "/admin", name: "admin-dashboard" },
        { route: "/admin/students", name: "admin-students" },
        { route: "/admin/students/new", name: "admin-create-student" },
        { route: "/admin/audio-review", name: "admin-audio-review" },
        { route: "/admin/reports", name: "admin-reports" },
        { route: "/admin/settings", name: "admin-settings" },
      ];
      for (const pg of adminPages) {
        await page.goto(`${BASE}${pg.route}`, { waitUntil: "networkidle" });
        await page.waitForTimeout(800);
        await page.screenshot({
          path: path.join(SCREENS_DIR, `${pg.name}-${vp.name}.png`),
          fullPage: false,
        });
        console.log(`[screenshot] ${pg.name}-${vp.name}.png`);
      }

      await ctx.close();
      console.log(`Done: ${vp.name}`);
    });
  }
});
