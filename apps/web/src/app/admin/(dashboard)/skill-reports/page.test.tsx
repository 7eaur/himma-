import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import SkillReportsPage from "./page";

const report = {
  source: "himma_v2_persisted_evidence",
  methodology: "synthetic",
  summary: { students: 1, official_pretests: 0, official_posttests: 0, paired: 0,
    average_pretest: null, average_posttest: null, average_improvement_points: null },
  students: [{ student_id: 1, student_name: "طالب اصطناعي", pretest: null, posttest: null,
    improvement_points: null, progress: { assigned_lessons: null, completed_lessons: null },
    support: { total: 0, mastered: 0, needs_followup: 0 } }],
  skills: Array.from({ length: 30 }, (_, index) => ({
    student_id: 1, phase: index % 2 === 0 ? "pretest" : "learning",
    skill_group: `مهارة رقم ${index + 1}`, graded: 2, correct: 1,
    observed_accuracy_percent: 50,
  })),
};

it("paginates dense skill evidence without rendering every card at once", async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => report });
  render(<SkillReportsPage />);
  await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(24));
  expect(screen.getByText("مهارة رقم 1", {exact: false})).toBeInTheDocument();
  expect(screen.queryByText("مهارة رقم 30", {exact: false})).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "التالي" }));
  expect(screen.getAllByRole("article")).toHaveLength(6);
  expect(screen.getByText("مهارة رقم 30", {exact: false})).toBeInTheDocument();
});

it("resets pagination when the supervisor changes the evidence phase", async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => report });
  render(<SkillReportsPage />);
  await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(24));
  fireEvent.click(screen.getByRole("button", { name: "التالي" }));
  fireEvent.change(screen.getByRole("combobox", { name: "مرحلة الدليل" }), { target: { value: "pretest" } });
  expect(screen.getAllByRole("article")).toHaveLength(15);
  expect(screen.queryByRole("button", { name: "التالي" })).not.toBeInTheDocument();
  expect(screen.getByText("15 نتيجة مهارة مطابقة")).toBeInTheDocument();
});

it("shows a recoverable empty state when filters exclude all available evidence", async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({
    ...report, skills: report.skills.filter(row => row.phase === "pretest"),
  }) });
  render(<SkillReportsPage />);
  await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(15));
  fireEvent.change(screen.getByRole("combobox", { name: "مرحلة الدليل" }), { target: { value: "posttest" } });
  expect(screen.getByText("لا توجد أدلة مطابقة للتصفية")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "مسح التصفية" }));
  expect(screen.getAllByRole("article")).toHaveLength(15);
});
