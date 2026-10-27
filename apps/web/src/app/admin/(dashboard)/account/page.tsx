import { redirect } from "next/navigation";

/**
 * Historical compatibility route.
 *
 * The canonical researcher account/security/supervisor surface is
 * `/admin/settings`. Keep this route only so old bookmarks do not strand a
 * signed-in researcher on the retired duplicate account UI.
 */
export default function AccountPage() {
  redirect("/admin/settings");
}
