"use client";

type Option = { id: string; text?: string | null };
type PrivateAnswer = {
  correct_option_ids?: string[];
  accepted_option_orders?: string[][];
  target_text?: string;
  rubric?: unknown;
};
const labels: Record<string, string> = {
  expected: "المطلوب", expected_text: "النص المطلوب", target_text: "النص المطلوب",
  target: "المطلوب", text: "النص", word: "الكلمة", words: "الكلمات",
  letter: "الحرف", letters: "الحروف", unit: "وحدة القراءة",
  reading_unit: "وحدة القراءة", pronunciation: "النطق المطلوب",
  expected_pronunciation: "النطق المطلوب", acceptable_variants: "بدائل مقبولة",
  accepted_variants: "بدائل مقبولة", min_accuracy: "الحد الأدنى للدقة",
  accuracy_threshold: "حد الدقة", criteria: "معايير التقييم",
  criterion: "معيار التقييم", instruction: "التوجيه",
  description: "الشرح", notes: "ملاحظات التقييم",
  tolerance: "حد التسامح", review_policy: "سياسة المراجعة",
};
const labelFor = (key: string) => labels[key] ?? "تفصيل من المعيار";
const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) return "";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "نعم" : "لا";
  if (Array.isArray(value)) return value.map(formatValue).filter(Boolean).join("، ");
  if (typeof value === "object") return Object.entries(value).map(([key, nested]) => {
    const formatted = formatValue(nested);
    return formatted ? `${labelFor(key)}: ${formatted}` : "";
  }).filter(Boolean).join(" · ");
  return "";
};

export default function BankAnswerReview({
  answer, options, readingReference, hint,
}: {
  answer: PrivateAnswer; options: Option[]; readingReference: unknown; hint?: string | null;
}) {
  const optionLabel = (id: string) => options.find(option => option.id === id)?.text || `الخيار ${id}`;
  const correct = (answer.correct_option_ids ?? []).map(optionLabel);
  const alternatives = (answer.accepted_option_orders ?? []).map(order => order.map(optionLabel).join(" ← "));
  const rubric = formatValue(answer.rubric);
  const reference = formatValue(readingReference);
  return <details className="rounded-xl bg-bg p-3" data-testid="v2-bank-answer">
    <summary className="cursor-pointer font-semibold">الإجابة ومعيار المراجعة</summary>
    <div className="mt-3 space-y-2 text-sm leading-7">
      {correct.length > 0 && <p><strong>الإجابة الصحيحة:</strong> {correct.join(" ← ")}</p>}
      {alternatives.length > 0 && <div><strong>ترتيبات أخرى مقبولة:</strong>
        <ul className="ms-5 list-disc">{alternatives.map((order, index) => <li key={index}>{order}</li>)}</ul>
      </div>}
      {answer.target_text && <p><strong>النص المطلوب:</strong> {answer.target_text}</p>}
      {rubric && <p className="whitespace-pre-wrap break-words"><strong>معيار التقييم:</strong> {rubric}</p>}
      {reference && <p className="whitespace-pre-wrap break-words"><strong>مرجع القراءة:</strong> {reference}</p>}
      {hint && <p className="whitespace-pre-wrap break-words"><strong>تلميح التدريب:</strong> {hint}</p>}
      {!correct.length && !alternatives.length && !answer.target_text && !rubric && !reference &&
        <p className="text-muted">لا توجد إجابة نصية لهذا السؤال. يمكن مراجعة التفاصيل الكاملة في ملف المحتوى المخصص للمشرف.</p>}
    </div>
  </details>;
}
