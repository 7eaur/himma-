import type { Metadata } from "next";
import { Noto_Kufi_Arabic } from "next/font/google";
import "./globals.css";

const notoKufi = Noto_Kufi_Arabic({
  variable: "--font-noto-kufi",
  subsets: ["arabic"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "هِمّة – منصة تقييم القراءة العربية",
  description: "منصة تعليمية لتقييم مهارات القراءة العربية لدى طلاب المرحلة الابتدائية",
  metadataBase: new URL("http://localhost:3000"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" className={notoKufi.variable}>
      <body>{children}</body>
    </html>
  );
}
