import { fireEvent, render, screen } from "@testing-library/react";
import StudentRerecordPage from "./page";

let mockTaskId = "23";
const mockReplace = jest.fn();
jest.mock("next/navigation", () => ({
  useParams: () => ({ taskId: mockTaskId }),
  useRouter: () => ({ replace: mockReplace }),
}));
jest.mock("@/components/learning/StudentRetryTasks", () => function MockRetry({ taskId, onCompleted }: { taskId: number; onCompleted: () => void }) {
  return <button type="button" data-testid="focused-retry" onClick={onCompleted}>طلب رقم {taskId}</button>;
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

it("returns home and announces success only after the submitted recording is acknowledged", () => {
  mockTaskId = "24";
  mockReplace.mockClear();
  const received: string[] = [];
  const handler = (event: Event) => received.push((event as CustomEvent<{text:string}>).detail.text);
  window.addEventListener("himma:feedback", handler);
  try {
    render(<StudentRerecordPage />);
    expect(mockReplace).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("focused-retry"));
    expect(mockReplace).toHaveBeenCalledWith("/student");
    expect(received).toEqual(["تم إرسال تسجيلك بنجاح. سيُراجعه المشرف."]);
  } finally { window.removeEventListener("himma:feedback", handler); }
});
