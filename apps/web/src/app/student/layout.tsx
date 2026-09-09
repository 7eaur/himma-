import StudentExperienceEffects from "@/components/StudentExperienceEffects";
import StudentRerecordTasks from "@/components/StudentRerecordTasks";

// Student routes render explicit state; this layout only adds shared experience effects and non-blocking tasks.
export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <StudentRerecordTasks />
      <StudentExperienceEffects />
    </>
  );
}
