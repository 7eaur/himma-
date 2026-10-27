import StudentActivityStateBoundary from "@/components/StudentActivityStateBoundary";
import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentAdaptiveHoldOverlay />
      <StudentActivityStateBoundary>{children}</StudentActivityStateBoundary>
    </>
  );
}
