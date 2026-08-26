import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";

export default function StudentActivityLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      {children}
      <StudentAdaptiveHoldOverlay />
    </>
  );
}
