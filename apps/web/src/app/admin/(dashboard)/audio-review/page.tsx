import { redirect } from "next/navigation";

// Old bookmarks may use this path. Review decisions now belong to the
// assessment and lesson queues, which use the active learning release.
export default function AudioReviewRedirect() {
  redirect("/admin/v2-assessments");
}
