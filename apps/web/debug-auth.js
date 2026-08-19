const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture network
  const requests = [];
  page.on('response', async (r) => {
    if (r.url().includes('/api/')) {
      const cookie = r.headers()['set-cookie'] || '';
      requests.push({ url: r.url(), status: r.status(), setCookie: cookie.substring(0, 60) });
    }
  });

  await page.goto('http://localhost:3000/admin/login');
  await page.locator('[data-testid="input-username"]').fill('researcher1');
  await page.locator('[data-testid="input-password"]').fill('securepass123');
  await page.locator('[data-testid="login-submit"]').click();
  
  await page.waitForTimeout(3000);
  
  console.log('Current URL:', page.url());
  console.log('Cookies:', await context.cookies('http://localhost:3000'));
  console.log('Network /api calls:', JSON.stringify(requests, null, 2));
  
  await browser.close();
})();
