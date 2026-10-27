import { fireEvent, render, screen } from "@testing-library/react";
import AssessmentReviews from "@/app/admin/(dashboard)/v2-assessments/page";
import LessonReviews from "@/app/admin/(dashboard)/v2-lesson-review/page";

const blocked = {
  response_id: 90, session_id: 80, student_id: 7, student_name: "اصطناعي",
  reason: "content_release_unavailable", detail: "نسخة أصلية غير محفوظة",
  content_release_id: 4, release_version: "historical", release_checksum: "0".repeat(64),
};
it.each([
  { name: "assessment", Component: AssessmentReviews },
  { name: "lesson", Component: LessonReviews },
])("$name keeps an unavailable historical bank visible but hides stale data after refresh failure", async ({ Component }) => {
  let failed = false;
  global.fetch = jest.fn(async (url: string) => {
    const queue = url.includes("review-queue") || url.includes("lesson-queue");
    const status = queue && failed ? 503 : 200;
    return { ok: status === 200, status, json: async () => queue
      ? failed ? { detail: "تعذر الاتصال" } : { items: [], blocked_items: [blocked], next_offset: null }
      : url.includes("placement-queue") ? { items: [], next_offset: null }
      : { counts: {}, averages: { pretest: null, posttest: null } } };
  }) as unknown as typeof fetch;
  render(<Component />);
  expect(await screen.findByTestId("v2-blocked-reviews")).toHaveTextContent("سجلات تحتاج استعادة إصدار المحتوى");
  expect(screen.queryByRole("button", { name: /اعتماد/ })).not.toBeInTheDocument();
  failed = true;
  fireEvent.click(screen.getByRole("button", { name: /تحديث/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر الاتصال");
  expect(screen.queryByTestId("v2-blocked-reviews")).not.toBeInTheDocument();
});
