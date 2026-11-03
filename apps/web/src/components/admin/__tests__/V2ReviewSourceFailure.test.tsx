import AssessmentReviews from "@/app/admin/(dashboard)/v2-assessments/page";
import LessonReviews from "@/app/admin/(dashboard)/v2-lesson-review/page";

const redirect = jest.fn();
jest.mock("next/navigation", () => ({
  redirect: (href: string) => redirect(href),
}));

// Legacy manual-review pages no longer render their own queue or stale
// student evidence; they preserve bookmarks by opening one protected,
// read-only V2 reading results surface.
it.each([
  { name: "assessment", Page: AssessmentReviews },
  { name: "lesson", Page: LessonReviews },
])("$name bookmark does not revive human grade or review queues", ({ Page }) => {
  redirect.mockClear();
  Page();
  expect(redirect).toHaveBeenCalledTimes(1);
  expect(redirect).toHaveBeenCalledWith("/admin/v2-review-center");
});
