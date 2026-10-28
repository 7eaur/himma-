import { render, screen } from "@testing-library/react";
import StudentsPage from "./page";

it("distinguishes reading review from automatic placement in the V2 student list", async () => {
  const student = {
    grade_level: 2, created_at: "2026-10-28T00:00:00Z", status: "active",
    journey: null, progress: { completed_lessons: 0, assigned_lessons: null,
      skipped_by_placement: 0, pending_review: 0, display_percent: null },
    data_status: "ready",
  };
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({
    source: "himma_v2_readmodel", total: 2, offset: 0, limit: 30,
    items: [
      { ...student, id: 1, full_name: "طالب قراءة", current_action: { action: "assessment", state: "waiting_review", label: "عرض حالة المراجعة" } },
      { ...student, id: 2, full_name: "طالب تسكين", current_action: { action: "assessment", state: "placement_pending_review", label: "عرض حالة المراجعة" } },
    ],
  }) });
  render(<StudentsPage />);
  expect(await screen.findAllByText("بانتظار مراجعة القراءة")).toHaveLength(2);
  expect(screen.getAllByText("جارٍ تحديد المستوى تلقائيًا")).toHaveLength(2);
  expect(screen.queryByText("بانتظار اعتماد التسكين")).not.toBeInTheDocument();
});
