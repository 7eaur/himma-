import { redirect } from "next/navigation";

// Old bookmarks remain reachable, but only the V2 native reading-results
// surface is active. The obsolete assessment tab no longer exists.
export default function AudioReviewRedirect() {
  redirect("/admin/v2-review-center");
}
