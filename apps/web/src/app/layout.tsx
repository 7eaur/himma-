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

const description = "هِمّة منصة تعليمية لتنمية مهارات القراءة العربية، تبدأ بتحديد مستوى الطالب وتقدم دروسًا تفاعلية وتدريبات صوتية وتقوية تناسب احتياجه، مع متابعة تقدمه خطوة بخطوة.";

export const metadata: Metadata = {
  metadataBase: new URL("https://himma-om.com"),
  title: "هِمّة | تعلّم القراءة بثقة",
  description,
  openGraph: {
    type: "website",
    locale: "ar_OM",
    siteName: "منصة هِمّة التعليمية",
    title: "هِمّة | تعلّم القراءة بثقة",
    description,
    url: "https://himma-om.com",
    images: [{ url: "/brand/social-preview.png", width: 1200, height: 630, alt: "شعار منصة هِمّة التعليمية" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "هِمّة | تعلّم القراءة بثقة",
    description,
    images: ["/brand/social-preview.png"],
  },
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
