"use client";
import { usePathname } from "next/navigation";
import PlatformState from "@/components/PlatformState";
export default function NotFound() {
  const pathname = usePathname();
  const homeHref = pathname?.startsWith("/admin") ? "/admin" : "/student";
  return <PlatformState mode="empty" title="404 — الصفحة غير موجودة" description="الرابط الذي فتحته غير موجود أو تغيّر مكانه. يمكنك العودة إلى لوحة التحكم." homeHref={homeHref} />;
}
