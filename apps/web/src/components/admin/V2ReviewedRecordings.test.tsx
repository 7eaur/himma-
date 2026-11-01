import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import V2ReviewedRecordings from "./V2ReviewedRecordings";

const item = {
  audio_id: 1, response_id: 3, student_id: 4, student_name: "طالب اصطناعي",
  question_id: "Q-01", lesson_id: "L1-01", kind: "lesson",
  is_correct: true, reviewed_at: null, duration_seconds: null,
  evaluation_source: "supervisor", audio_url: "/api/v2/review/recordings/1/audio",
};
it("uses one retryable read error and never disguises malformed results as empty evidence", async () => {
  const fetcher = jest.fn().mockResolvedValueOnce({
    ok: true, json: async () => ({ items: null, next_offset: null }),
  }).mockResolvedValue({
    ok: true, json: async () => ({ items: [item], next_offset: null }),
  });
  global.fetch = fetcher;
  render(<V2ReviewedRecordings />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر قراءة بيانات التسجيلات");
  expect(screen.queryByText("لا توجد تسجيلات مقيّمة لهذه التصفية")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name: "إعادة المحاولة"}));
  await waitFor(() => expect(screen.getByText("طالب اصطناعي")).toBeVisible());
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.queryByText("طالب #4")).not.toBeInTheDocument();
  fireEvent.click(screen.getByText("مرجع التسجيل"));
  expect(screen.getByText("السؤال: Q-01")).toBeVisible();
});

it("never reveals raw server diagnostics for a failed recording request", async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: false, status: 503, json: async () => ({detail:"SQL timeout V2"}),
  });
  render(<V2ReviewedRecordings />);
  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("تعذر تحميل التسجيلات المقيّمة");
  expect(alert).not.toHaveTextContent("SQL");
  expect(screen.queryByText("طالب اصطناعي")).not.toBeInTheDocument();
});
