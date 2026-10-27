"use client";

import Link from "next/link";
import { useRef, useState } from "react";

export interface BlockedV2Review {
  response_id: number; session_id: number; student_id: number; student_name: string;
  reason: string; detail: string; content_release_id: number | null;
  release_version: string | null; release_checksum: string | null;
  recoverable?: boolean;
}

export default function V2BlockedReviewNotice({ items = [], onRestored }: {
  items?: BlockedV2Review[]; onRestored?: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const restore = async (releaseId: number) => {
    if (inFlight.current || !Number.isSafeInteger(releaseId) || releaseId <= 0) return;
    inFlight.current = true; setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v2/content/admin/releases/${releaseId}/restore-original-snapshot`, { method: "POST" });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(typeof result?.detail === "string" ? result.detail : "تعذر استعادة النسخة الأصلية");
      await onRestored?.();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "تعذر استعادة النسخة الأصلية"); }
    finally { inFlight.current = false; setBusy(false); }
  };
  if (items.length === 0) return null;
  return <section role="status" className="rounded-2xl border border-amber-300 bg-amber-50 p-4 space-y-3" data-testid="v2-blocked-reviews">
    <h2 className="font-bold text-navy">سجلات تحتاج استعادة إصدار المحتوى · {items.length}</h2>
    <p className="text-sm">حُفظت الإجابات كما هي. لا يمكن تقييمها ببنك مختلف؛ بقية المراجعات متاحة بصورة مستقلة.</p>
    {error && <p role="alert">{error}</p>}
    {items.map(item => <details key={item.response_id} className="text-sm">
      <summary className="cursor-pointer py-2">جلسة #{item.session_id} · إجابة #{item.response_id}</summary>
      <p>{item.detail}</p>
      <p>الإصدار: {item.release_version ?? "غير مسجل"} · المعرّف: {item.content_release_id ?? "—"}</p>
      {item.release_checksum && <p className="break-all font-mono text-xs" dir="ltr">{item.release_checksum}</p>}
      {item.recoverable && item.content_release_id != null && onRestored && <button type="button" disabled={busy}
        onClick={() => void restore(item.content_release_id!)} className="my-2 block rounded-xl border border-amber-400 bg-white px-4 py-3 font-semibold">
        استعادة النسخة الأصلية المطابقة
      </button>}
      <Link href={`/admin/students/${item.student_id}`} className="inline-block py-3 font-semibold underline">فتح ملف الطالب للمراجعة</Link>
    </details>)}
  </section>;
}
