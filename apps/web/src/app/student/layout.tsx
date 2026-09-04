"use client";

import { usePathname } from "next/navigation";
import StudentExperienceEffects from "@/components/StudentExperienceEffects";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const immersive = pathname.startsWith("/student/session/") || pathname.startsWith("/student/activity/");

  return (
    <div className={immersive ? "student-immersive-shell" : undefined}>
      {children}
      <StudentExperienceEffects />
    </div>
  );
}
