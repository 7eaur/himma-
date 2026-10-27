import Link from "next/link";

export interface BlockedV2Review {
  response_id: number; session_id: number; student_id: number; student_name: string;
  reason: string; detail: string; content_release_id: number | null;
  release_version: string | null; release_checksum: string | null;
}

export default function V2BlockedReviewNotice({ items = [] }: { items?: BlockedV2Review[] }) {
  if (items.length === 0) return null;
  return <section role="status" className="rounded-2xl border border-amber-300 bg-amber-50 p-4 space-y-3" data-testid="v2-blocked-reviews">
    <h2 className="font-bold text-navy">سجلات تحتاج استعادة إصدار المحتوى · {items.length}</h2>
    <p className="text-sm">حُفظت الإجابات كما هي. لا يمكن تقييمها ببنك مختلف؛ بقية المراجعات متاحة بصورة مستقلة.</p>
    {items.map(item => <details key={item.response_id} className="text-sm">
      <summary className="cursor-pointer py-2">جلسة #{item.session_id} · إجابة #{item.response_id}</summary>
      <p>{item.detail}</p>
      <p>الإصدار: {item.release_version ?? "غير مسجل"} · المعرّف: {item.content_release_id ?? "—"}</p>
      {item.release_checksum && <p className="break-all font-mono text-xs" dir="ltr">{item.release_checksum}</p>}
      <Link href={`/admin/students/${item.student_id}`} className="inline-block py-3 font-semibold underline">فتح ملف الطالب للمراجعة</Link>
    </details>)}
  </section>;
}
