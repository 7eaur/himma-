import { redirect } from "next/navigation";

// Historical session IDs are not interchangeable with current assessment IDs.
// The student's home resumes their own pinned learning journey safely.
export default function OldStudentSessionRedirect() {
  redirect("/student");
}
