"use client";

export interface ReadingRubricDraft {
  target_units: number | "";
  deletions: number;
  substitutions: number;
  insertions: number;
  pronunciation_notes: string;
  fluency_notes: string;
}

export const emptyReadingRubric = (): ReadingRubricDraft => ({
  target_units: "",
  deletions: 0,
  substitutions: 0,
  insertions: 0,
  pronunciation_notes: "",
  fluency_notes: "",
});

export function rubricValid(value: ReadingRubricDraft): boolean {
  return typeof value.target_units === "number" && Number.isInteger(value.target_units) && value.target_units > 0 &&
    value.target_units <= 1000 &&
    [value.deletions, value.substitutions, value.insertions].every(
      number => Number.isInteger(number) && number >= 0 && number <= 1000
    ) &&
    value.deletions + value.substitutions <= value.target_units &&
    value.pronunciation_notes.length <= 2000 && value.fluency_notes.length <= 2000;
}

export function readingObservation(value: ReadingRubricDraft): number | null {
  if (!rubricValid(value)) return null;
  const errors = value.deletions + value.substitutions + value.insertions;
  return Math.max(0, Math.round((1 - errors / Number(value.target_units)) * 100));
}

export default function V2ReadingRubricEditor({
  value, onChange, disabled,
}: {
  value: ReadingRubricDraft;
  onChange: (next: ReadingRubricDraft) => void;
  disabled: boolean;
}) {
  const fields: Array<{key: "target_units" | "deletions" | "substitutions" | "insertions"; label: string}> = [
    {key: "target_units", label: "عدد الوحدات المطلوبة"},
    {key: "deletions", label: "أخطاء الحذف"},
    {key: "substitutions", label: "أخطاء الاستبدال"},
    {key: "insertions", label: "أخطاء الإضافة"},
  ];
  const observation = readingObservation(value);
  return <fieldset className="min-w-0 rounded-xl border border-teal-200 bg-teal-50/30 p-3 sm:p-4"
    disabled={disabled} data-testid="v2-reading-rubric">
    <legend className="px-2 font-bold text-slate-900">تقدير القراءة بالأرقام</legend>
    <p className="mb-3 text-sm text-slate-700">عدّ الوحدات وأخطاء القراءة بعد سماع التسجيل كاملًا. الرقم وصفي للبحث؛ لا يحسم وحده استيفاء المهارة.</p>
    <div className="grid grid-cols-2 gap-3">
      {fields.map(field => <label key={field.key} className="grid min-w-0 gap-1 text-sm font-semibold">
        <span>{field.label}</span>
        <input type="number" min={field.key === "target_units" ? 1 : 0} max={1000} step={1}
          inputMode="numeric" className="min-h-11 w-full min-w-0 rounded-xl border border-slate-300 bg-white px-3"
          value={value[field.key]}
          onChange={event => {
            const input = event.target.value;
            const next = input === "" ? (field.key === "target_units" ? "" : 0)
              : Number(input);
            onChange({...value, [field.key]: next});
          }} />
      </label>)}
    </div>
    <div className="mt-3 grid gap-3 sm:grid-cols-2">
      <label className="grid gap-1 text-sm font-semibold">ملاحظات النطق
        <textarea rows={2} maxLength={2000} className="min-h-20 w-full rounded-xl border border-slate-300 p-3"
          value={value.pronunciation_notes}
          onChange={event => onChange({...value, pronunciation_notes: event.target.value})}
          placeholder="الحروف والأصوات التي لاحظت صعوبتها" />
      </label>
      <label className="grid gap-1 text-sm font-semibold">ملاحظات الطلاقة
        <textarea rows={2} maxLength={2000} className="min-h-20 w-full rounded-xl border border-slate-300 p-3"
          value={value.fluency_notes}
          onChange={event => onChange({...value, fluency_notes: event.target.value})}
          placeholder="الوقف والسرعة ووضوح القراءة" />
      </label>
    </div>
    {observation === null
      ? <p className="mt-3 text-sm text-amber-800" role="status">أدخل عدد وحدات موجبًا، ولا تتجاوز أخطاء الحذف والاستبدال عدد الوحدات، لتفعيل قرار التقييم.</p>
      : <p className="mt-3 text-sm font-semibold text-teal-900" role="status">
          التقدير الرقمي الوصفي: {observation}% — القرار النهائي يحدده المشرف بعد مراجعة الصوت.
        </p>}
  </fieldset>;
}
