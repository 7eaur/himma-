import { expect, test } from "@playwright/test";

test.describe("approved media fidelity", () => {
  test("serves real educational images and audio through the web proxy", async ({ page, request }) => {
    const imageResponse = await request.get("/api/media/VOC-01");
    expect(imageResponse.status()).toBe(200);
    expect(imageResponse.headers()["content-type"]).toContain("image/");
    expect((await imageResponse.body()).byteLength).toBeGreaterThan(1_000);

    const audioResponse = await request.get("/api/media/LET-01");
    expect(audioResponse.status()).toBe(200);
    expect(audioResponse.headers()["content-type"]).toContain("audio/");
    expect((await audioResponse.body()).byteLength).toBeGreaterThan(500);

    await page.setContent(`
      <main dir="rtl">
        <img id="approved-image" src="/api/media/VOC-01" alt="موزة" />
        <audio id="approved-audio" src="/api/media/LET-01"></audio>
      </main>
    `);

    const image = page.locator("#approved-image");
    await expect(image).toBeVisible();
    await expect.poll(async () => image.evaluate((element) => (element as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);

    const audio = page.locator("#approved-audio");
    await expect.poll(async () => audio.evaluate((element) => (element as HTMLMediaElement).readyState)).toBeGreaterThan(0);
  });
});
