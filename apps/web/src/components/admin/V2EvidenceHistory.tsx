"use client";

import { useState } from "react";

type Kind = "lesson" | "assessment";
interface Entry {
  reviewer_id: number | null; note: string | null; is_correct: boolean | null; at: string | null;
}
interface Retry {
  task_id: number; kind: string; status: string; reason: string;
  requested_at: string | null; submitted_at: string | null;
  text_response: string | null; superseded_recording_count: number;
}
interface Audio {
  id: number; status: string; file_size: number;
  duration_seconds: number | null; submitted_at: string | null; url: string;
}
interface History {
  original: { text_response: string | null; submitted_at: string | null };
  retries: Retry[]; recordings: Audio[]; decisions: Entry[];
}

function dateText(value: string | null) {
  return value ? new Date(value).toLocaleString("ar") : "—";
}

/** Loads sensitive historical evidence only when an authenticated supervisor opens it. */
export default function V2EvidenceHistory({ kind, responseId }: { kind: Kind; responseId: number }) {
  const [open, setOpen] = useState(false);
  const [history, setHistory] = useState<History | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const response = await fetch(`/api/v2/review-history/admin/${kind}/${responseId}`, { cache: "no-store" });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.detail || "تعذر جلب السجل");
      setHistory(payload);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر جلب السجل");
    } finally { setLoading(false); }
  };

  return <section className="rounded-xl border border-slate-200 p-3">
    <button type="button" aria-expanded={open}
      onClick={() => { if (!open && !history) void load(); setOpen((value) => !value); }}
      className="text-sm font-semibold text-blue-800 underline underline-offset-2">
      {open ? "إخفاء تاريخ الإجابة" : "عرض سجل الإجابة والنسخ السابقة"}
    </button>
    {open && <div className="mt-3 space-y-3 text-sm">
      <button type="button" disabled={loading} onClick={() => void load()}
        className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-50">تحديث السجل</button>
      {loading && <p role="status">جاري تحميل السجل المحمي...</p>}
      {error && <p role="alert" className="text-rose-700">{error}</p>}
      {history && <>
        <div className="rounded-lg bg-slate-50 p-3">
          <strong>الدليل الأصلي · {dateText(history.original.submitted_at)}</strong>
          {history.original.text_response !== null &&
            <p className="mt-1 whitespace-pre-wrap break-words">{history.original.text_response}</p>}
        </div>
        {history.retries.map((item) => <div key={item.task_id} className="rounded-lg border border-amber-200 p-3">
          <strong>طلب إعادة #{item.task_id} · {item.kind === "rerecord" ? "تسجيل" : "كتابة"} · {item.status}</strong>
          <p className="mt-1 whitespace-pre-wrap break-words">السبب: {item.reason}</p>
          <p className="mt-1 text-xs text-slate-600">الطلب: {dateText(item.requested_at)} · الإرسال: {dateText(item.submitted_at)}</p>
          {item.text_response !== null &&
            <p className="mt-1 whitespace-pre-wrap break-words">النسخة البديلة: {item.text_response}</p>}
          {item.superseded_recording_count > 0 &&
            <p className="text-xs text-slate-600">تسجيلات مرفوعة استُبدلت قبل الإرسال: {item.superseded_recording_count}</p>}
        </div>)}
        {history.recordings.map((item) => <div key={item.id} className="space-y-2 rounded-lg border border-blue-100 p-3">
          <p className="font-semibold">ملف صوتي #{item.id} · {item.status} · {dateText(item.submitted_at)}</p>
          <audio controls preload="none" src={item.url} className="w-full" aria-label={`تسجيل المراجعة ${item.id}`} />
        </div>)}
        {history.decisions.map((item, index) => <div key={index} className="rounded-lg border border-emerald-200 p-3">
          <p className="font-semibold">قرار المشرف: {item.is_correct ? "مستوفٍ" : "غير مستوفٍ"} · {dateText(item.at)}</p>
          {item.note && <p className="mt-1 whitespace-pre-wrap break-words">{item.note}</p>}
        </div>)}
      </>}
    </div>}
  </section>;
}
