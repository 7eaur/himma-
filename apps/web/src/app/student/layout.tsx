import StudentExperienceEffects from "@/components/StudentExperienceEffects";
import "./question-system.css";

// Student routes render explicit state; this layout only adds shared experience effects and non-blocking tasks.
export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="student-page-enter">{children}</div>
      <StudentExperienceEffects />
    </>
  );
}
