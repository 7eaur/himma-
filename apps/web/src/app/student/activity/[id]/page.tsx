import { redirect } from "next/navigation";

// Historical activity IDs cannot be treated as current lesson session IDs.
export default function OldStudentActivityRedirect() {
  redirect("/student");
}
