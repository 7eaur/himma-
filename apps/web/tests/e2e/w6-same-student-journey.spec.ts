import { execFileSync } from "child_process";
import path from "path";
import { expect, test, type APIRequestContext, type BrowserContext, type Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUPERVISOR_USERNAME = process.env.E2E_RESEARCHER_USERNAME ?? "admin";
const SUPERVISOR_PASSWORD = process.env.E2E_RESEARCHER_PASSWORD;

type RichItem = {
  id: number;
  interaction_type: string;
  steps: Array<{
    id: number;
    options: Array<{ id: number; text: string; order_index: number }>;
  }>;
};

async function addAuthCookie(context: BrowserContext, response: Awaited<ReturnType<APIRequestContext["post"]>>) {
  const value = response.headers()["set-cookie"]?.match(/access_token=([^;]+)/)?.[1];
  expect(value).toBeTruthy();
  await context.addCookies([{ name: "access_token", value: value ?? "", domain: "localhost", path: "/", httpOnly: true, sameSite: "Lax", secure: false }]);
}

async function loginSupervisor(request: APIRequestContext, context: BrowserContext) {
  if (!SUPERVISOR_PASSWORD) throw new Error("E2E_RESEARCHER_PASSWORD is required");
  const response = await request.post(`${API_URL}/auth/login`, { data: { username: SUPERVISOR_USERNAME, password: SUPERVISOR_PASSWORD } });
  expect(response.status()).toBe(200);
  await addAuthCookie(context, response);
}

async function loginStudent(request: APIRequestContext, context: BrowserContext, accessCode: string) {
  const response = await request.post(`${API_URL}/auth/student-login`, { data: { access_code: accessCode } });
  expect(response.status()).toBe(200);
  await addAuthCookie(context, response);
}

async function waitForAssessmentPhase(page: Page) {
  const root = page.getByTestId("assessment-session");
  await expect(root).toHaveAttribute("data-phase", /^(question|waiting_audio_review|done|error)$/, { timeout: 20000 });
  const phase = await root.getAttribute("data-phase");
  if (phase === "error") throw new Error((await root.textContent()) || "Assessment runtime error");
  return phase;
}

async function recordReading(page: Page) {
  const record = page.getByTestId("record-reading");
  await expect(record).toHaveAttribute("aria-label", "بدء التسجيل", { timeout: 5000 });
  await record.click();
  await page.waitForTimeout(850);
  await expect(page.getByTestId("record-reading")).toHaveAttribute("aria-label", "إيقاف التسجيل");
  await page.getByTestId("record-reading").click();
  const submit = page.getByRole("button", { name: /إرسال التسجيل/ });
  await expect(submit).toBeEnabled({ timeout: 7000 });
  await submit.click();
}

async function answerVisibleQuestion(page: Page, item: RichItem) {
  const interaction = item.interaction_type;
  const step = item.steps[0];
  if (!step) throw new Error(`Assessment item ${item.id} has no step`);

  if (interaction === "read_aloud" || interaction === "timed_read_aloud") {
    await recordReading(page);
    return;
  }

  if (["sequence", "memory_sequence", "path_sequence", "build_word"].includes(interaction)) {
    const confirm = page.getByRole("button", { name: "تأكيد والمتابعة" });
    const images = page.getByTestId("sequence-image-options");
    if (await images.count()) {
      const buttons = images.getByRole("button");
      for (let index = 0; index < await buttons.count() && !(await confirm.isEnabled()); index += 1) {
        await buttons.nth(index).click();
      }
    } else {
      for (const option of [...step.options].sort((a, b) => a.order_index - b.order_index)) {
        if (await confirm.isEnabled()) break;
        const button = page.getByRole("button", { name: option.text, exact: true }).first();
        if (await button.count()) await button.click();
      }
    }
    await expect(confirm).toBeEnabled({ timeout: 5000 });
    await confirm.click();
    return;
  }

  const imageGroup = page.getByTestId("image-options");
  const many = interaction === "choose_many" || interaction === "listen_choose_many";
  if (await imageGroup.count()) {
    const buttons = imageGroup.getByRole("button");
    const selections = many ? Math.min(2, await buttons.count()) : 1;
    for (let index = 0; index < selections; index += 1) await buttons.nth(index).click();
  } else {
    const buttons = page.locator('button[aria-pressed="false"]');
    await expect(buttons.first()).toBeVisible({ timeout: 5000 });
    const selections = many ? Math.min(2, await buttons.count()) : 1;
    for (let index = 0; index < selections; index += 1) await buttons.nth(index).click();
  }
  await page.getByRole("button", { name: "تأكيد والمتابعة" }).click();
}

async function reviewPendingAudio(page: Page, request: APIRequestContext, context: BrowserContext, accessCode: string, sessionId: string) {
  await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "waiting_audio_review", { timeout: 10000 });
  await context.clearCookies();
  await loginSupervisor(request, context);
  await page.goto("/admin/audio-review");
  const start = page.getByRole("button", { name: "بدء المراجعة" }).first();
  await expect(start).toBeVisible({ timeout: 15000 });
  await start.click();
  const save = page.getByRole("button", { name: "حفظ التقييم" });
  await expect(save).toBeEnabled({ timeout: 7000 });
  await save.click();
  await context.clearCookies();
  await loginStudent(request, context, accessCode);
  await page.goto(`/student/session/${sessionId}`);
  return waitForAssessmentPhase(page);
}

async function completeAssessment(page: Page, request: APIRequestContext, context: BrowserContext, accessCode: string, sessionId: string) {
  let answered = 0;
  let audioReviews = 0;
  while (answered < 30) {
    const phase = await waitForAssessmentPhase(page);
    if (phase === "done") break;
    expect(phase).toBe("question");

    const next = await request.get(`${API_URL}/assessment/session/${sessionId}/next`);
    expect(next.status()).toBe(200);
    const item: RichItem | null = await next.json();
    expect(item).toBeTruthy();
    if (!item) break;

    const reading = item.interaction_type === "read_aloud" || item.interaction_type === "timed_read_aloud";
    await answerVisibleQuestion(page, item);
    answered += 1;

    if (reading) {
      const waiting = await waitForAssessmentPhase(page);
      expect(waiting).toBe("waiting_audio_review");
      const resumed = await reviewPendingAudio(page, request, context, accessCode, sessionId);
      audioReviews += 1;
      if (answered < 30) expect(resumed).toBe("question");
    }
  }
  expect(answered).toBe(30);
  expect(audioReviews).toBeGreaterThan(0);
  await expect(page.getByTestId("assessment-session")).toHaveAttribute("data-phase", "done", { timeout: 20000 });
}

function completeLearningHistory(studentId: number) {
  const apiRoot = path.resolve(__dirname, "../../../../services/api");
  const script = path.join(apiRoot, "tests/support/w6_complete_learning_fixture.py");
  const output = execFileSync("python", [script, String(studentId)], { cwd: apiRoot, env: process.env, encoding: "utf8" }).trim();
  const result = JSON.parse(output.split(/\r?\n/).at(-1) ?? "{}");
  expect(result.student_id).toBe(studentId);
  expect(result.learning_journey_completed).toBe(true);
  expect(result.current_level).toBe(3);
  expect(result.posttest_enabled).toBe(false);
  expect(result.posttest_completed).toBe(false);
  return result;
}

test("W6 keeps one student identity from live pretest through learning handoff to live posttest", async ({ page, context, request }) => {
  test.setTimeout(420000);

  await loginSupervisor(request, context);
  await page.goto("/admin/students/new");
  const studentName = `طالب رحلة W6 ${Date.now()}`;
  await page.getByTestId("input-student-name").fill(studentName);
  await page.getByTestId("submit-create-student").click();
  const codeEl = page.getByTestId("student-access-code");
  await expect(codeEl).toBeVisible({ timeout: 10000 });
  const accessCode = (await codeEl.textContent())?.trim() ?? "";
  expect(accessCode).toMatch(/^\d{6}$/);

  const students = await request.get(`${API_URL}/researcher/students`);
  expect(students.status()).toBe(200);
  const rows: Array<{ id: number; access_code: string; full_name: string }> = await students.json();
  const student = rows.find((row) => row.access_code === accessCode);
  expect(student?.full_name).toBe(studentName);
  const studentId = student!.id;

  await context.clearCookies();
  await loginStudent(request, context, accessCode);
  await page.goto("/student");
  await page.getByRole("button", { name: "ابدأ الاختبار" }).click();
  await expect(page).toHaveURL(/\/student\/session\/\d+/, { timeout: 10000 });
  const pretestId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
  expect(pretestId).toBeTruthy();
  await completeAssessment(page, request, context, accessCode, pretestId!);

  await page.goto("/student");
  await expect(page.getByRole("button", { name: /ابدأ أنشطة مستواك|متابعة الأنشطة/ })).toBeEnabled({ timeout: 10000 });

  const accelerated = completeLearningHistory(studentId);
  expect(accelerated.level_states[2]).toBe("completed");

  await context.clearCookies();
  await loginSupervisor(request, context);
  await page.goto(`/admin/students/${studentId}`);
  await expect(page.getByRole("heading", { name: studentName })).toBeVisible({ timeout: 10000 });
  await page.getByRole("button", { name: "المسار والتقدم" }).click();
  await expect(page.locator('[data-level-state="completed"]')).toHaveCount(3 - Number(accelerated.starting_level) + 1);

  await page.getByRole("button", { name: "الاختبارات" }).click();
  const openPosttest = page.getByRole("button", { name: "فتح الاختبار البعدي" });
  await expect(openPosttest).toBeEnabled();
  await openPosttest.click();
  await expect(page.getByText("تم فتح الاختبار البعدي للطالب.")).toBeVisible({ timeout: 7000 });

  await context.clearCookies();
  await loginStudent(request, context, accessCode);
  await page.goto("/student");
  const posttestButton = page.getByRole("button", { name: "ابدأ الاختبار البعدي" });
  await expect(posttestButton).toBeEnabled({ timeout: 10000 });
  await posttestButton.click();
  await expect(page).toHaveURL(/\/student\/session\/\d+/, { timeout: 10000 });
  const posttestId = page.url().match(/\/student\/session\/(\d+)/)?.[1];
  expect(posttestId).toBeTruthy();
  expect(posttestId).not.toBe(pretestId);
  await completeAssessment(page, request, context, accessCode, posttestId!);

  await page.goto("/student");
  await expect(page.getByRole("heading", { name: "أكملت رحلتك" })).toBeVisible({ timeout: 10000 });

  await context.clearCookies();
  await loginSupervisor(request, context);
  const report = await request.get(`${API_URL}/researcher/reports/students/${studentId}`);
  expect(report.status()).toBe(200);
  const reportPayload = await report.json();
  expect(reportPayload.pretest?.score).not.toBeNull();
  expect(reportPayload.posttest?.score).not.toBeNull();
});
