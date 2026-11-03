import PlatformState from "@/components/PlatformState";
export default function NotFound() {
  return <PlatformState mode="empty" compact title="404 — الصفحة غير موجودة" description="لم نتمكن من العثور على هذه الصفحة." homeHref="/admin" />;
}
