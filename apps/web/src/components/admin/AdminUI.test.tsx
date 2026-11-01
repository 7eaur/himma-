import { fireEvent, render, screen } from "@testing-library/react";
import { AdminAction, AdminRequestStatus } from "./AdminUI";

it("does not navigate or export when an action link is disabled", () => {
  render(<>
    <AdminAction href="/api/v2/reports/exports/cohort.xlsx" disabled>تصدير مؤقتًا غير متاح</AdminAction>
    <AdminAction href="/admin/students" disabled>الطلاب غير متاح</AdminAction>
    <AdminAction disabled onClick={jest.fn()}>إجراء غير متاح</AdminAction>
  </>);
  expect(screen.queryByRole("link", {name: "تصدير مؤقتًا غير متاح"})).not.toBeInTheDocument();
  expect(screen.queryByRole("link", {name: "الطلاب غير متاح"})).not.toBeInTheDocument();
  expect(screen.getByText("تصدير مؤقتًا غير متاح")).toHaveAttribute("aria-disabled", "true");
  expect(screen.getByText("الطلاب غير متاح")).toHaveAttribute("aria-disabled", "true");
  expect(screen.getByRole("button", {name: "إجراء غير متاح"})).toBeDisabled();
});

it("keeps authorized local export and internal navigation links functional", () => {
  render(<>
    <AdminAction href="/api/v2/reports/exports/cohort.xlsx">تصدير</AdminAction>
    <AdminAction href="/admin/students">الطلاب</AdminAction>
  </>);
  expect(screen.getByRole("link", {name: "تصدير"})).toHaveAttribute("href", "/api/v2/reports/exports/cohort.xlsx");
  expect(screen.getByRole("link", {name: "الطلاب"})).toHaveAttribute("href", "/admin/students");
});

it("shows a single readable load status or recoverable error, never a fake empty data panel", () => {
  const retry = jest.fn();
  const {rerender} = render(<AdminRequestStatus loading error="" onRetry={retry} loadingText="جارٍ تحميل الطلاب..." />);
  expect(screen.getByRole("status")).toHaveTextContent("جارٍ تحميل الطلاب...");
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  rerender(<AdminRequestStatus loading={false} error="تعذر تحميل الطلاب" onRetry={retry} />);
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
  expect(screen.getByRole("alert")).toHaveTextContent("تعذر تحميل الطلاب");
  fireEvent.click(screen.getByRole("button",{name:"إعادة المحاولة"}));
  expect(retry).toHaveBeenCalledTimes(1);
  rerender(<AdminRequestStatus loading={false} error="" onRetry={retry} />);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
