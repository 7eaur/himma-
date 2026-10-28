import { fireEvent, render, screen } from "@testing-library/react";
import ReportsPage from "./page";
import SkillReportsPage from "../skill-reports/page";

const report = {
  source: "himma_v2_persisted_evidence", methodology: "synthetic", skills: [],
  summary: { students: 1, official_pretests: 1, official_posttests: 0, paired: 0,
    average_pretest: 0, average_posttest: null, average_improvement_points: null },
  students: [{ student_id: 1, student_name: "طالب تقرير اصطناعي", current_level: null,
    journey_state: "in_progress", pretest: { score: 0, attempt_no: 1, release_version: "test" }, posttest: null,
    comparison_state: "pending", improvement_points: null, relative_improvement: null,
    progress: { completed_lessons: null, assigned_lessons: null, skipped_by_placement: null, percent: null },
    support: { total: 0, resolved: 0, waiting: 0, escalated: 0 }, pending_assessment_reviews: 1 }],
};
it("shows an official zero independently of an unapproved posttest and uses V2 export links", async () => {
  const fetcher = jest.fn().mockResolvedValue({ ok: true, json: async () => report });
  global.fetch = fetcher;
  render(<ReportsPage />);
  const table = await screen.findByTestId("v2-report-table");
  expect(table).toHaveTextContent("0%");
  expect(table).toHaveTextContent("بانتظار الاعتماد");
  expect(screen.getByRole("link", { name: /^Excel$/ })).toHaveAttribute("href", "/api/v2/reports/exports/cohort.xlsx");
  expect(fetcher.mock.calls.every(([url]) => url === "/api/v2/reports/summary")).toBe(true);
  expect(screen.queryByText("أرشيف تقارير V1")).not.toBeInTheDocument();
});
it("keeps a skills source failure unavailable without loading V1 evidence", async () => {
  const fetcher = jest.fn().mockResolvedValue({ ok: false });
  global.fetch = fetcher;
  render(<SkillReportsPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل تقارير V2");
  expect(fetcher.mock.calls.every(([url]) => url === "/api/v2/reports/summary")).toBe(true);
  expect(screen.queryByText("لا توجد أدلة مقيمة مطابقة")).not.toBeInTheDocument();
  expect(screen.queryByText("أرشيف مهارات V1")).not.toBeInTheDocument();
});

it("keeps the report short and searches a student without mixing in older rows", async () => {
  const students = Array.from({length: 21}, (_, index) => ({
    ...report.students[0], student_id: index + 1, student_name: `طالب تقرير ${index + 1}`,
  }));
  global.fetch = jest.fn().mockResolvedValue({ok: true, json: async () => ({...report, students})});
  render(<ReportsPage />);
  expect(await screen.findAllByText("طالب تقرير 1")).toHaveLength(2);
  expect(screen.getByTestId("v2-report-table").querySelectorAll("tbody tr")).toHaveLength(20);
  fireEvent.click(screen.getByRole("button", {name: "التالي"}));
  expect(screen.getByTestId("v2-report-table").querySelectorAll("tbody tr")).toHaveLength(1);
  expect(screen.getAllByText("طالب تقرير 21")).toHaveLength(2);
  fireEvent.change(screen.getByRole("textbox", {name: "بحث عن طالب أو معرّف"}), {target: {value: "تقرير 3"}});
  expect(screen.getByTestId("v2-report-table").querySelectorAll("tbody tr")).toHaveLength(1);
  expect(screen.getAllByText("طالب تقرير 3")).toHaveLength(2);
});
