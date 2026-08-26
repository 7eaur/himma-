"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Route, ShieldCheck } from "lucide-react";
import { usePathname } from "next/navigation";

interface ReinforcementOption {
  item_id: number;
  canonical_id?: string | null;
  title: string;
  skill_id: number;
  skill_name?: string | null;
  interaction_type: string;
  already_used: boolean;
  attempt_status?: string | null;
}

interface ReviewPayload {
  student_id: number;
  level_id: number;
  weakest_skill_id?: number | null;
  decision_id: number;
  options: ReinforcementOption[];
}

interface PanelMessage {
  kind: "success" | "error";
  text: string;
  studentId: string;
}

function apiError(data: unknown, fallback: string) {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export default function ReinforcementReviewPanel() {
  const pathname = usePathname();
  const studentId = useMemo(() => pathname.match(/^\/admin\/students\/(\d+)$/)?.[1] ?? null, [pathname]);
  const [review, setReview] = useState<ReviewPayload | null>(null);
  const [selectedItem, setSelectedItem] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<PanelMessage | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!studentId) return;

    void fetch(`/api/researcher/students/${studentId}/adaptation/reinforcement-options`, { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json().catch(() => null);
        if (cancelled) return;
        if (response.status === 409) {
          setReview(null);
          setMessage(null);
          return;
        }
        if (!response.ok) throw new Error(apiError(data, "تعذر فحص حالة التقوية"));
        const payload = data as ReviewPayload;
        setReview(payload);
        setMessage(null);
        const firstAvailable = payload.options.find((option) => !option.already_used);
        setSelectedItem(firstAvailable ? String(firstAvailable.item_id) : "");
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setReview(null);
          setMessage({
            kind: "error",
            text: error instanceof Error ? error.message : "تعذر فحص حالة التقوية",
            studentId,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [studentId]);

  if (!studentId) return null;

  const visibleMessage = message?.studentId === studentId ? message : null;
  const activeReview: ReviewPayload | null = review && String(review.student_id) === studentId ? review : null;

  if (!activeReview) {
    if (!visibleMessage) return null;
    return (
      <section className="mx-auto mb-6 w-full max-w-6xl" dir="rtl" aria-live="polite">
        <div className={visibleMessage.kind === "success" ? "alert-success" : "alert-error"}>
          {visibleMessage.kind === "success" && <CheckCircle2 size={18} className="inline ml-2" />}
          {visibleMessage.text}
        </div>
      </section>
    );
  }

  const available = activeReview.options.filter((option) => !option.already_used);

  const assign = async () => {
    if (!selectedItem) {
      setMessage({ kind: "error", text: "اختر نشاط تقوية معتمدًا.", studentId });
      return;
    }
    if (reason.trim().length < 5) {
      setMessage({ kind: "error", text: "اكتب سبب الاختيار بوضوح ليُحفظ في سجل القرارات.", studentId });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch(`/api/researcher/students/${studentId}/adaptation/assign-reinforcement`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: Number(selectedItem), reason: reason.trim() }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر إسناد نشاط التقوية"));
      setReview(null);
      setMessage({ kind: "success", text: "تم إسناد نشاط التقوية. يستطيع الطالب الآن متابعة مساره.", studentId });
      window.setTimeout(() => window.location.reload(), 1200);
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر إسناد نشاط التقوية", studentId });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mx-auto mb-6 w-full max-w-6xl rounded-3xl border border-amber-200 bg-amber-50/80 p-5 shadow-sm" dir="rtl" data-testid="reinforcement-review-panel">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex max-w-xl gap-3">
          <div className="mt-1 grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-white text-amber-700 shadow-sm"><Route size={22} /></div>
          <div>
            <div className="mb-1 flex items-center gap-2 text-sm font-bold text-amber-800"><AlertCircle size={16} /> يحتاج قرار تقوية من المشرف</div>
            <h2 className="text-xl font-extrabold text-navy">اختر نشاطًا معتمدًا قبل متابعة المسار</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">لم يجد المحرك تطابقًا آليًا آمنًا بين المهارة الأضعف وأحد أنشطة التقوية الخمسة المعتمدة. لن تختار المنصة نشاطًا عشوائيًا؛ اختر من الأنشطة المعتمدة في المستوى {activeReview.level_id} واكتب سبب القرار.</p>
          </div>
        </div>

        <div className="w-full rounded-2xl border border-white bg-white/90 p-4 lg:max-w-xl">
          {available.length > 0 ? (
            <div className="space-y-3">
              <label className="block text-sm font-bold text-navy" htmlFor="reinforcement-option">نشاط التقوية</label>
              <select id="reinforcement-option" className="input-field w-full" value={selectedItem} onChange={(event) => setSelectedItem(event.target.value)}>
                {available.map((option) => (
                  <option key={option.item_id} value={option.item_id}>{option.title}{option.skill_name ? ` — ${option.skill_name}` : ""}</option>
                ))}
              </select>
              <label className="block text-sm font-bold text-navy" htmlFor="reinforcement-reason">سبب الإسناد</label>
              <textarea id="reinforcement-reason" className="input-field min-h-24 w-full resize-y" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="مثال: راجعت أداء الطالب واخترت هذا النشاط لأنه الأنسب للضعف الظاهر." />
              <button className="btn-primary w-full justify-center" disabled={busy} onClick={() => void assign()}>
                <ShieldCheck size={18} /> {busy ? "جاري الحفظ..." : "إسناد النشاط وتوثيق القرار"}
              </button>
            </div>
          ) : (
            <div className="alert-error">استُخدمت جميع أنشطة التقوية المعتمدة في هذا المستوى. يلزم قرار أكاديمي موثق قبل إضافة محتوى جديد.</div>
          )}
        </div>
      </div>
      {visibleMessage && <div className={`mt-4 ${visibleMessage.kind === "success" ? "alert-success" : "alert-error"}`}>{visibleMessage.kind === "success" && <CheckCircle2 size={18} className="inline ml-2" />}{visibleMessage.text}</div>}
    </section>
  );
}
