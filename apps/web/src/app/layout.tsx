import type { Metadata } from "next";
import "@fontsource/tajawal/400.css";
import "@fontsource/tajawal/500.css";
import "@fontsource/tajawal/700.css";
import "@fontsource/tajawal/800.css";
import "@fontsource/ibm-plex-sans-arabic/400.css";
import "@fontsource/ibm-plex-sans-arabic/500.css";
import "@fontsource/ibm-plex-sans-arabic/600.css";
import "@fontsource/ibm-plex-sans-arabic/700.css";
import "./tailwind.css";
import "./globals.css";
import "./fonts.css";
import "./accessibility.css";
import "./reduced-motion.css";
import "./ux-corrections.css";
import "./ux-student-surfaces.css";
import "./student-dashboard-corrections.css";
import { ScrollAnimator } from "@/components/ScrollAnimator";
import GlobalFeedback from "@/components/GlobalFeedback";

export const metadata: Metadata = {
  title: "منصة همة التعليمية",
  description: "أتعلم، أتطور، أصل إلى القمة",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <ScrollAnimator />
        <GlobalFeedback />
        {children}
      </body>
    </html>
  );
}
