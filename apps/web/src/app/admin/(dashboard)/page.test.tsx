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
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل لوحة V2");
  expect(screen.queryByText("إجمالي الطلاب")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
  await waitFor(() => expect(screen.getByTestId("admin-v2-students")).toBeInTheDocument());
  expect(fetcher).toHaveBeenCalledTimes(2);
});

it("rejects a legacy source without displaying its students", async () => {
  global.fetch = jest.fn().mockResolvedValue(response({ ...payload, source: "v1" }));
  render(<AdminDashboard />);
  expect(await screen.findByRole("alert")).toHaveTextContent("غير متطابق مع V2");
  expect(screen.queryByText("طالب اصطناعي")).not.toBeInTheDocument();
});
