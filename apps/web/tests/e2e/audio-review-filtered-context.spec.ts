import { test, expect, type APIRequestContext, type BrowserContext } from "@playwright/test";

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

test.describe("Filtered audio review context", () => {
  test.beforeEach(async ({ request, context }) => {
    await loginAsSupervisor(request, context);
  });

  test("keeps student context through valid grading, rerecord request, and profile navigation", async ({ page }) => {
    const studentId = 4242;
    const filteredQueueRequests: string[] = [];
    const gradePayloads: Array<{ id: number; body: Record<string, unknown> }> = [];
    const submissions = [
      {
        id: 9101,
        storage_key: "tests/ui-valid.webm",
        status: "uploaded",
        submitted_at: "2026-09-13T00:00:00Z",
        student_id: studentId,
        student_name: "طالب سياق المراجعة",
        session_type: "pretest",
        item_title: "قراءة أولى",
        expected_reading_text: "نص القراءة الأولى",
      },
      {
        id: 9102,
        storage_key: "tests/ui-rerecord.webm",
        status: "uploaded",
        submitted_at: "2026-09-13T00:01:00Z",
        student_id: studentId,
        student_name: "طالب سياق المراجعة",
        session_type: "pretest",
        item_title: "قراءة ثانية",
        expected_reading_text: "نص القراءة الثانية",
      },
    ];

    await page.route("**/api/review/pending-audio?student_id=4242", async (route) => {
      filteredQueueRequests.push(route.request().url());
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(submissions) });
    });

    await page.route("**/api/review/audio/*/grade", async (route) => {
      const id = Number(route.request().url().match(/\/audio\/(\d+)\/grade/)?.[1]);
      const body = route.request().postDataJSON() as Record<string, unknown>;
      gradePayloads.push({ id, body });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: body.is_valid ? "graded" : "rerecord_required" }),
      });
    });

    await page.goto(`/admin/audio-review?student_id=${studentId}`);

    await expect(page.getByRole("heading", { name: "مراجعة التسجيلات" })).toBeVisible();
    await expect(page.getByText(`تسجيلات الطالب #${studentId} التي تنتظر قرار المشرف.`)).toBeVisible();
    await expect(page.getByText("القائمة مفلترة لهذا الطالب فقط.")).toBeVisible();
    await expect(page.getByRole("link", { name: "عرض جميع التسجيلات" })).toHaveAttribute("href", "/admin/audio-review");
    await expect(page.getByRole("link", { name: "فتح ملف الطالب" }).first()).toHaveAttribute("href", `/admin/students/${studentId}`);
    expect(filteredQueueRequests.length).toBeGreaterThan(0);
    expect(filteredQueueRequests.every((url) => url.includes(`student_id=${studentId}`))).toBe(true);

    const reviewButtons = page.getByRole("button", { name: "بدء المراجعة" });
    await expect(reviewButtons).toHaveCount(2);

    await reviewButtons.nth(0).click();
    await page.getByRole("button", { name: "اعتماد القراءة" }).click();
    await page.getByRole("button", { name: "حفظ واعتماد القراءة" }).click();
    await expect(page.getByText("تم اعتماد التسجيل وحفظ نتيجة المراجعة بنجاح.")).toBeVisible();
    await expect(page.getByText("قراءة أولى")).toHaveCount(0);

    await page.getByRole("button", { name: "بدء المراجعة" }).click();
    await page.getByRole("button", { name: "طلب إعادة تسجيل", exact: true }).click();
    await expect(page.getByText("الطالب سيشاهد مهمة إعادة التسجيل بشكل مستقل في مساره. لن يُجبر على ترك السؤال أو النشاط الحالي، وسيبقى التسجيل السابق محفوظًا في سجل المراجعة.")).toBeVisible();
    await page.getByRole("button", { name: "إرسال طلب إعادة التسجيل" }).click();
    await expect(page.getByText("تم إرسال مهمة إعادة تسجيل للطالب دون إيقاف مساره، مع الاحتفاظ بالتسجيل السابق في السجل.")).toBeVisible();
    await expect(page.getByText("قراءة ثانية")).toHaveCount(0);

    expect(gradePayloads).toHaveLength(2);
    expect(gradePayloads[0].id).toBe(9101);
    expect(gradePayloads[0].body.is_valid).toBe(true);
    expect(gradePayloads[1].id).toBe(9102);
    expect(gradePayloads[1].body.is_valid).toBe(false);
  });
});
