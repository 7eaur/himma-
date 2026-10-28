import { render, screen } from "@testing-library/react";
import StudentRerecordPage from "./page";

let mockTaskId = "23";
jest.mock("next/navigation", () => ({
  useParams: () => ({ taskId: mockTaskId }),
}));
jest.mock("@/components/learning/StudentRetryTasks", () => function MockRetry({ taskId }: { taskId: number }) {
  return <span data-testid="focused-retry">طلب رقم {taskId}</span>;
});

it("opens only the selected student rerecord task", () => {
  mockTaskId = "23";
  render(<StudentRerecordPage />);
  expect(screen.getByRole("heading", { name: "إعادة تسجيل القراءة" })).toBeVisible();
  expect(screen.getByTestId("focused-retry")).toHaveTextContent("طلب رقم 23");
  expect(screen.getByRole("link", { name: "العودة إلى لوحة الطالب" })).toHaveAttribute("href", "/student");
});

it("rejects malformed links without requesting any task", () => {
  mockTaskId = "not-an-id";
  render(<StudentRerecordPage />);
  expect(screen.getByRole("alert")).toHaveTextContent("رابط طلب القراءة غير صالح");
  expect(screen.queryByTestId("focused-retry")).not.toBeInTheDocument();
});
