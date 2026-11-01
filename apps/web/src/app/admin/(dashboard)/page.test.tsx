import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import AdminDashboard from "./page";

const payload = {
  source: "himma_v2_readmodel",
  counts: { students: 8, active_accounts: 5, learning: 3, ready_for_posttest: 1,
    completed: 2, assessment_reviews: 4, lesson_reviews: 6, placements: 1 },
  recent_students: [{ id: 7, full_name: "طالب اصطناعي", status: "active", data_status: "ready",
    journey: { current_level: 1, placement_state: "placed" },
    current_action: { action: "lesson_catalog", label: "متابعة الدرس" },
    progress: { completed_lessons: 3, assigned_lessons: 19, display_percent: 15.8 } }],
};
const response = (data: unknown, status = 200) => ({ ok: status === 200, status, json: async () => data });

it("reads only the V2 overview and renders lessons without credential columns", async () => {
  const fetcher = jest.fn().mockResolvedValue(response(payload));
  global.fetch = fetcher;
  render(<AdminDashboard />);
  expect(await screen.findByTestId("admin-v2-students")).toHaveTextContent("3 / 19 درس");
  expect(screen.queryByText("رمز الدخول", { exact: true })).not.toBeInTheDocument();
  expect(screen.queryByText("تقدم الأنشطة")).not.toBeInTheDocument();
  expect(fetcher.mock.calls.every(([url]) => url === "/api/v2/student/admin/overview")).toBe(true);
  expect(screen.getByText("4 · قراءات الاختبارات")).toBeInTheDocument();
});

it("hides unavailable counts and allows an explicit retry after a source failure", async () => {
  const fetcher = jest.fn().mockResolvedValueOnce(response({}, 503)).mockResolvedValueOnce(response(payload));
  global.fetch = fetcher;
  render(<AdminDashboard />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل لوحة المتابعة");
  expect(screen.queryByText("إجمالي الطلاب")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
  await waitFor(() => expect(screen.getByTestId("admin-v2-students")).toBeInTheDocument());
  expect(fetcher).toHaveBeenCalledTimes(2);
});

it("rejects a legacy source without displaying its students", async () => {
  global.fetch = jest.fn().mockResolvedValue(response({ ...payload, source: "v1" }));
  render(<AdminDashboard />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر التحقق من بيانات المتابعة الحالية");
  expect(screen.queryByText("طالب اصطناعي")).not.toBeInTheDocument();
});

it("shows automatic placement as a system step rather than a supervisor review", async () => {
  global.fetch = jest.fn().mockResolvedValue(response({ ...payload, recent_students: [
    { ...payload.recent_students[0], current_action: {
      action: "assessment", state: "placement_pending_review", label: "عرض حالة المراجعة",
    } },
  ] }));
  render(<AdminDashboard />);
  expect(await screen.findByTestId("admin-v2-students")).toHaveTextContent("جارٍ تحديد المستوى تلقائيًا");
  expect(screen.queryByText("عرض حالة المراجعة")).not.toBeInTheDocument();
});

it("takes the supervisor to the matching review-center tab, not duplicate standalone pages", async () => {
  global.fetch = jest.fn().mockResolvedValue(response(payload));
  render(<AdminDashboard />);
  const exams = await screen.findByRole("link", { name: /4 · قراءات الاختبارات/ });
  const lessons = screen.getByRole("link", { name: /6 · قراءات الدروس/ });
  expect(exams).toHaveAttribute("href", "/admin/v2-review-center?tab=assessments");
  expect(lessons).toHaveAttribute("href", "/admin/v2-review-center?tab=lessons");
});

it("does not create an actionable warning from zero pending records", async () => {
  const idle = { ...payload, counts: { ...payload.counts,
    assessment_reviews: 0, lesson_reviews: 0, ready_for_posttest: 0 } };
  global.fetch = jest.fn().mockResolvedValue(response(idle));
  render(<AdminDashboard />);
  expect(await screen.findByText("لا توجد مراجعات تحتاج إلى إجراء الآن")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /0 · قراءات/ })).not.toBeInTheDocument();
});
