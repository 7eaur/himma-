import { render, screen } from "@testing-library/react";
import { AdminAction } from "./AdminUI";

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
