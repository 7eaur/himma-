import {fireEvent, render, screen} from "@testing-library/react";
import V2ReviewCenterPage from "./page";

const push = jest.fn((href: string) => window.history.pushState({}, "", href));
jest.mock("next/navigation", () => ({
  useRouter: () => ({push}),
  usePathname: () => "/admin/v2-review-center",
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

jest.mock("../v2-assessments/page", () => function AssessmentReview({ embedded }: { embedded?: boolean }) { return <div>{!embedded && <h1>عنوان الاختبارات المستقل</h1>}طابور الاختبارات</div>; });
jest.mock("../v2-lesson-review/page", () => function LessonReview({ embedded }: { embedded?: boolean }) { return <div>{!embedded && <h1>عنوان الدروس المستقل</h1>}طابور الدروس</div>; });
jest.mock("../v2-reviewed-recordings/page", () => function ReviewedArchive({ embedded }: { embedded?: boolean }) { return <div>{!embedded && <h1>عنوان الأرشيف المستقل</h1>}الأرشيف المقيّم</div>; });

afterEach(() => { push.mockClear(); });
beforeEach(() => { window.history.replaceState({}, "", "/admin/v2-review-center"); });

test("switches the unified reviewer view without mounting every child queue", () => {
  render(<V2ReviewCenterPage />);
  expect(screen.getAllByRole("tab")).toHaveLength(3);
  expect(screen.getByText("طابور الاختبارات")).toBeInTheDocument();
  expect(screen.queryByText("طابور الدروس")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", {name: "قراءات الدروس"}));
  expect(screen.getByText("طابور الدروس")).toBeInTheDocument();
  expect(window.location.search).toBe("?tab=lessons");
  fireEvent.click(screen.getByRole("tab", {name: "تم تقييمها"}));
  expect(screen.getByText("الأرشيف المقيّم")).toBeInTheDocument();
  expect(screen.queryByText("طابور الدروس")).not.toBeInTheDocument();
});

test("URL deep-link opens the reviewed recordings tab", async () => {
  window.history.replaceState({}, "", "/admin/v2-review-center?tab=reviewed&student_id=17");
  render(<V2ReviewCenterPage />);
  expect(await screen.findByText("الأرشيف المقيّم")).toBeInTheDocument();
  expect(window.location.search).toContain("student_id=17");
});

test("restores the requested review tab after Next navigation or browser Back", () => {
  const view = render(<V2ReviewCenterPage />);
  fireEvent.click(screen.getByRole("tab",{name:"قراءات الدروس"}));
  expect(push).toHaveBeenCalledWith("/admin/v2-review-center?tab=lessons",{scroll:false});
  expect(screen.getByText("طابور الدروس")).toBeInTheDocument();
  window.history.replaceState({}, "", "/admin/v2-review-center?tab=reviewed");
  view.rerender(<V2ReviewCenterPage />);
  expect(screen.getByText("الأرشيف المقيّم")).toBeInTheDocument();
});

test("shows one supervisor review heading across all tabs without removing their content", () => {
  render(<V2ReviewCenterPage />);
  const title = () => screen.getAllByRole("heading", { level: 1 });
  expect(title()).toHaveLength(1);
  expect(title()[0]).toHaveTextContent("مركز مراجعة التسجيلات");
  fireEvent.click(screen.getByRole("tab", {name: "قراءات الدروس"}));
  expect(title()).toHaveLength(1);
  expect(screen.getByText("طابور الدروس")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", {name: "تم تقييمها"}));
  expect(title()).toHaveLength(1);
  expect(screen.getByText("الأرشيف المقيّم")).toBeInTheDocument();
});
