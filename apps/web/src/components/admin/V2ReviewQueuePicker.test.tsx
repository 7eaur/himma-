import { fireEvent, render, screen } from "@testing-library/react";
import V2ReviewQueuePicker from "./V2ReviewQueuePicker";

const items = [
  {response_id: 1, student_id: 10, student_name: "طالب أول", question_id: "L1-01-IC", lesson_id: "L1-01", retry_state: null},
  {response_id: 2, student_id: 11, student_name: "طالب ثان", question_id: "L1-02-IC", lesson_id: "L1-02", retry_state: "submitted" as const},
];

test("review picker handles one recording with prev/next and scoped student link", () => {
  const onSelect = jest.fn();
  const {rerender} = render(<V2ReviewQueuePicker items={items} selectedResponseId={null}
    onSelect={onSelect} busy={false} label="الدروس" />);
  expect(screen.getByText(/1 من 2 في الصفحة الحالية/)).toBeInTheDocument();
  expect(screen.getByRole("link", {name: "ملف الطالب"})).toHaveAttribute("href", "/admin/students/10?tab=recordings");
  fireEvent.click(screen.getByRole("button", {name: "التالي"}));
  expect(onSelect).toHaveBeenCalledWith(2);
  rerender(<V2ReviewQueuePicker items={items} selectedResponseId={2}
    onSelect={onSelect} busy={false} label="الدروس" />);
  expect(screen.getByRole("link", {name: "ملف الطالب"})).toHaveAttribute("href", "/admin/students/11?tab=recordings");
  expect(screen.getByText(/2 من 2 في الصفحة الحالية/)).toBeInTheDocument();
  expect(screen.getByRole("button", {name: "التالي"})).toBeDisabled();
});

test("review picker disables switching when saving and never reveals credentials", () => {
  const onSelect = jest.fn();
  render(<V2ReviewQueuePicker items={items} selectedResponseId={1}
    onSelect={onSelect} busy={true} label="الاختبارات" />);
  expect(screen.getByRole("combobox", {name:"الطالب والتسجيل"})).toBeDisabled();
  expect(screen.getByRole("button", {name:"التالي"})).toBeDisabled();
  expect(screen.queryByText("123456")).not.toBeInTheDocument();
});
