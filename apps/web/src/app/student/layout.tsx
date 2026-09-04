import StudentExperienceEffects from "@/components/StudentExperienceEffects";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <StudentExperienceEffects />
    </>
  );
}
