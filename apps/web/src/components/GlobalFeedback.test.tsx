import { act, fireEvent, render, screen } from "@testing-library/react";
import GlobalFeedback from "./GlobalFeedback";
import { notifyFeedback } from "@/lib/feedback";

it("shows accessible success, warning and error toasts and permits dismissal", () => {
  render(<GlobalFeedback />);
  act(() => notifyFeedback("success", "تم إرسال التسجيل بنجاح"));
  expect(screen.getByRole("status")).toHaveTextContent("تم إرسال التسجيل بنجاح");
  expect(screen.getByTestId("himma-feedback-host")).toHaveAttribute("popover", "manual");
  act(() => notifyFeedback("warning", "استمع إلى التسجيل كاملًا"));
  expect(screen.getByRole("status")).toHaveTextContent("استمع إلى التسجيل كاملًا");
  act(() => notifyFeedback("error", "تعذر حفظ القرار"));
  expect(screen.getByRole("alert")).toHaveTextContent("تعذر حفظ القرار");
  fireEvent.click(screen.getByRole("button", { name: "إغلاق الإشعار" }));
  expect(screen.queryByTestId("himma-feedback-host")).not.toBeInTheDocument();
});
