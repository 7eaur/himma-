import {fireEvent, render, screen} from "@testing-library/react";
import V2ReviewCenterPage from "./page";

jest.mock("../v2-assessments/page", () => function AssessmentReview() { return <div>طابور الاختبارات</div>; });
jest.mock("../v2-lesson-review/page", () => function LessonReview() { return <div>طابور الدروس</div>; });
jest.mock("../v2-reviewed-recordings/page", () => function ReviewedArchive() { return <div>الأرشيف المقيّم</div>; });

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
