import { redirect } from "next/navigation";

// Keep historical staff bookmarks working, without a second human-review UI.
export default function LegacyReadingReviewRedirect() {
  redirect("/admin/v2-review-center");
}
