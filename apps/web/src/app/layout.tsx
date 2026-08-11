import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "هِمّة – منصة تقييم القراءة العربية",
  description: "منصة تعليمية لتقييم مهارات القراءة العربية لدى طلاب المرحلة الابتدائية",
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL ?? "http://localhost:3000"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
