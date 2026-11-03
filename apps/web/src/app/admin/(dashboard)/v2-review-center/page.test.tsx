import { render, screen } from "@testing-library/react";
import V2ReviewCenterPage from "./page";

jest.mock("@/components/admin/V2ReadingResults", () => function Results() {
  return <main><h1>متابعة القراءة الصوتية</h1><p>نتائج القراءة</p></main>;
});

test("review center renders one native results surface without manual approval queues", () => {
  render(<V2ReviewCenterPage />);
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.getByRole("heading", { name: "متابعة القراءة الصوتية" })).toBeInTheDocument();
  expect(screen.getByText("نتائج القراءة")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /اعتماد|رفض|طلب إعادة/ })).not.toBeInTheDocument();
});
