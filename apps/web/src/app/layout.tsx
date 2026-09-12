import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic, Tajawal } from "next/font/google";
import "./tailwind.css";
import "./globals.css";
import "./fonts.css";
import "./accessibility.css";
import "./reduced-motion.css";
import { ScrollAnimator } from "@/components/ScrollAnimator";

const studentFont = Tajawal({
  subsets: ["arabic"],
  weight: ["400", "500", "700", "800"],
  display: "swap",
  variable: "--font-tajawal",
});

const researcherFont = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-ibm-plex-sans-arabic",
});

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
    <html
      lang="ar"
      dir="rtl"
      className={`${studentFont.variable} ${researcherFont.variable}`}
    >
      <body>
        <ScrollAnimator />
        {children}
      </body>
    </html>
  );
}
