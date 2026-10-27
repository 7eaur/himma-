"use client";

import Link from "next/link";

export interface ReviewQueueEntry {
  response_id: number;
  student_id: number;
  student_name: string;
  question_id: string;
  lesson_id?: string;
  kind?: string;
  retry_state?: "requested" | "submitted" | null;
}

/**
 * One-review-at-a-time picker shared by lesson and assessment queues.
 * The authenticated server still owns review eligibility, locking and scoring;
 * changing this selection never grades or bypasses audio playback acknowledgement.
 */
export default function V2ReviewQueuePicker<T extends ReviewQueueEntry>({
  items,
  selectedResponseId,
  onSelect,
  busy,
  label,
}: {
  items: T[];
  selectedResponseId: number | null;
  onSelect: (id: number) => void;
  busy: boolean;
  label: string;
}) {
  if (!items.length) return null;
  const current = items.find(item => item.response_id === selectedResponseId) ?? items[0];
  const index = items.findIndex(item => item.response_id === current.response_id);
  return <section className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:p-4"
    aria-label="اختيار تسجيل للمراجعة" data-testid="v2-review-queue-picker">
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
      <div><strong className="text-sm text-slate-900">اختر تسجيلًا واحدًا</strong>
        <p className="text-xs text-slate-600">{label} · {index + 1} من {items.length} في الصفحة الحالية</p></div>
      <Link href={`/admin/students/${current.student_id}?tab=recordings`}
        className="inline-flex min-h-11 items-center rounded-xl border border-slate-300 bg-white px-3 text-sm font-semibold text-blue-800">
        ملف الطالب
      </Link>
    </div>
    <label className="grid gap-1 text-sm font-semibold text-slate-800" htmlFor="v2-review-select">
      الطالب والتسجيل
      <select id="v2-review-select" className="min-h-11 w-full min-w-0 rounded-xl border border-slate-300 bg-white p-3"
        disabled={busy} value={current.response_id}
        onChange={event => onSelect(Number(event.target.value))}>
        {items.map(item => <option key={item.response_id} value={item.response_id}>
          {item.student_name} — {item.lesson_id ?? (item.kind === "pretest" ? "القبلي" : "البعدي")} — {item.question_id}
          {item.retry_state === "submitted" ? " (وصلت إعادة)" : ""}
        </option>)}
      </select>
    </label>
    <div className="mt-3 grid grid-cols-2 gap-2">
      <button className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 font-semibold disabled:opacity-40"
        type="button" disabled={busy || index === 0}
        onClick={() => onSelect(items[index - 1].response_id)}>السابق</button>
      <button className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 font-semibold disabled:opacity-40"
        type="button" disabled={busy || index === items.length - 1}
        onClick={() => onSelect(items[index + 1].response_id)}>التالي</button>
    </div>
  </section>;
}
