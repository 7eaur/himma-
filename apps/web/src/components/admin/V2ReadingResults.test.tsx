import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import V2ReadingResults from "./V2ReadingResults";

const example = {
  job_id: 8, student_id: 12, student_name: "طالب تجريبي", question_id: "L2-04-GP-01",
  reference: "ذهب سامي إلى المدرسة.", kind: "sentence", session_kind: "lesson",
  result: "صحيحة", score_percent: 85.714, created_at: "2026-11-02T00:00:00Z",
  has_audio: true,
};
const page = { items: [example], total: 1, next_offset: null };

beforeEach(() => {
  global.fetch = jest.fn(async () => ({
    ok: true, status: 200, json: async () => page,
  })) as unknown as typeof fetch;
});
afterEach(() => { jest.restoreAllMocks(); });

test("shows educational result and protected audio without manual decision buttons", async () => {
  render(<V2ReadingResults />);
  expect(await screen.findByText("طالب تجريبي")).toBeInTheDocument();
  expect(screen.getByText("85.714% من الكلمات")).toBeInTheDocument();
  expect(screen.getByText("ذهب سامي إلى المدرسة.")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /اعتماد|رفض القراءة/ })).not.toBeInTheDocument();
  const audio = screen.getByLabelText("تسجيل قراءة طالب تجريبي");
  expect(audio).toHaveAttribute("preload", "none");
  expect(audio).toHaveAttribute("src", "/api/v2/reading/admin/jobs/8/audio");
});

test("filtering requests the correct native endpoint without loading old manual queues", async () => {
  render(<V2ReadingResults />);
  await screen.findByText("طالب تجريبي");
  fireEvent.click(screen.getByRole("button", { name: "تحتاج متابعة" }));
  await waitFor(() => {
    const requests = (global.fetch as jest.Mock).mock.calls.map(call => String(call[0]));
    expect(requests.some(url => url.includes("state=needs_attention"))).toBe(true);
    expect(requests.every(url => !url.includes("review-queue"))).toBe(true);
  });
});

test("failed refresh removes the previous child's data instead of showing stale audio", async () => {
  let failed = false;
  global.fetch = jest.fn(async () => failed
    ? { ok: false, status: 503, json: async () => ({ detail: "تعذر الاتصال" }) }
    : { ok: true, status: 200, json: async () => page },
  ) as unknown as typeof fetch;
  render(<V2ReadingResults />);
  await screen.findByText("طالب تجريبي");
  failed = true;
  fireEvent.click(screen.getByRole("button", { name: "تحديث النتائج" }));
  expect(await screen.findByRole("alert")).toBeInTheDocument();
  expect(screen.queryByText("طالب تجريبي")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("تسجيل قراءة طالب تجريبي")).not.toBeInTheDocument();
});
