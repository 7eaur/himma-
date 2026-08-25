"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Calendar,
  Check,
  Copy,
  Hash,
  KeyRound,
  PencilLine,
  Play,
  Power,
  RefreshCw,
  Save,
  ShieldCheck,
  Star,
  User,
} from "lucide-react";
import { useParams } from "next/navigation";

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  access_code: string;
  created_at: string;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  core_completed_items: number;
  core_total_items: number;
  core_completed: boolean;
}

interface AdaptationDecision {
  decision_id: number;
  source: "automatic" | "manual";
  action: "promote" | "stay" | "support" | "demote" | "hold" | "override";
  mastery_score: number | null;
  previous_level: number;
  new_level: number;
  weakest_skill_id: number | null;
  recommended_item_id: number | null;
  valid_attempt_count: number;
  consecutive_low_count: number;
  explanation: Record<string, unknown>;
  manual_reason?: string | null;
  created_at: string;
}

interface RewardEvent {
  id: number;
  type: "stars" | "badge";
  stars: number | null;
  label: string;
  details: Record<string, unknown>;
  created_at: string;
}

const ACTION_LABEL: Record<string, string> = {
  promote: "ترقية مستوى",
  stay: "استمرار في المستوى",
  support: "تقوية موجهة",
  demote: "خفض مستوى واحد",
  hold: "انتظار بيانات كافية",
  override: "تعديل يدوي",
};

const REASON_LABEL: Record<string, string> = {
  second_consecutive_low_mastery: "انخفاض الإتقان في قرارين متتاليين",
  low_mastery_support_first: "الإتقان أقل من 50%؛ تبدأ التقوية قبل أي خفض",
  top_level_mastery: "إتقان مرتفع في أعلى مستوى",
  promotion_waiting_for_skill_coverage: "الإتقان مرتفع لكن تغطية المهارات لم تكتمل",
  promotion_blocked_by_skill_floor: "توجد مهارة مطلوبة دون حد 60%",
  mastery_and_skill_gates_passed: "اجتاز الإتقان وتغطية المهارات وحد المهارة المطلوب",
  mastery_in_stability_band: "الإتقان بين 50% وأقل من 80%",
  researcher_manual_override: "قرار يدوي موثق من المشرف",
};

function apiError(data: unknown, fallback: string) {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  }
  return fallback;
}

export default function StudentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [history, setHistory] = useState<AdaptationDecision[]>([]);
  const [rewards, setRewards] = useState<RewardEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [overrideLevel, setOverrideLevel] = useState("1");
  const [overrideReason, setOverrideReason] = useState("");
  const [editName, setEditName] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });

  useEffect(() => {
    let cancelled = false;
    if (!id) return;

    void Promise.all([
      fetch(`/api/researcher/students/${id}`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/adaptation/history`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/rewards`, { cache: "no-store" }),
    ])
      .then(async ([studentResponse, historyResponse, rewardsResponse]) => {
        if (!studentResponse.ok) {
          const body = await studentResponse.json().catch(() => null);
          throw new Error(apiError(body, studentResponse.status === 404 ? "لم يتم العثور على الطالب" : "تعذر تحميل بيانات الطالب"));
        }
        const studentData: Student = await studentResponse.json();
        const historyData: AdaptationDecision[] = historyResponse.ok ? await historyResponse.json() : [];
        const rewardsData: RewardEvent[] = rewardsResponse.ok ? await rewardsResponse.json() : [];
        if (cancelled) return;
        setStudent(studentData);
        setEditName(studentData.full_name);
        setOverrideLevel(String(studentData.current_level));
        setHistory(historyData);
        setRewards(rewardsData);
      })
      .catch((error: unknown) => {
        if (!cancelled) setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحميل بيانات الطالب" });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  const latestDecision = useMemo(() => history.at(-1) ?? null, [history]);
  const totalStars = rewards.reduce((sum, reward) => sum + (reward.stars ?? 0), 0);
  const badges = rewards.filter((reward) => reward.type === "badge");

  const refreshAdaptiveEvidence = async () => {
    if (!student) return;
    const [historyResponse, rewardsResponse] = await Promise.all([
      fetch(`/api/researcher/students/${student.id}/adaptation/history`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${student.id}/rewards`, { cache: "no-store" }),
    ]);
    if (historyResponse.ok) setHistory(await historyResponse.json());
    if (rewardsResponse.ok) setRewards(await rewardsResponse.json());
  };

  const saveStudentName = async () => {
    if (!student || editName.trim() === student.full_name) return;
    setBusy("name");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: editName }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ اسم الطالب"));
      setStudent(data);
      setEditName(data.full_name);
      setMessage({ kind: "success", text: "تم تحديث اسم الطالب." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ اسم الطالب" });
    } finally {
      setBusy("");
    }
  };

  const toggleStudentStatus = async () => {
    if (!student) return;
    setBusy("status");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: student.status !== "active" }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث حالة الطالب"));
      setStudent(data);
      setMessage({ kind: "success", text: data.status === "active" ? "تم تفعيل حساب الطالب." : "تم إيقاف حساب الطالب." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث حالة الطالب" });
    } finally {
      setBusy("");
    }
  };

  const changeAccessCode = async (manual: boolean) => {
    if (!student) return;
    if (manual && !/^\d{6}$/.test(manualCode)) {
      setMessage({ kind: "error", text: "الرمز اليدوي يجب أن يتكون من 6 أرقام." });
      return;
    }
    setBusy("code");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/access-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_code: manual ? manualCode : null }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث رمز الدخول"));
      setStudent(data);
      setManualCode("");
      setMessage({ kind: "success", text: "تم تحديث رمز دخول الطالب." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث رمز الدخول" });
    } finally {
      setBusy("");
    }
  };

  const copyAccessCode = async () => {
    if (!student) return;
    await navigator.clipboard.writeText(student.access_code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  const updatePosttestAccess = async () => {
    if (!student) return;
    setBusy("posttest");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/posttest-access`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !student.posttest_enabled }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث إتاحة الاختبار البعدي"));
      setStudent(data);
      setMessage({ kind: "success", text: data.posttest_enabled ? "تم فتح الاختبار البعدي للطالب." : "تم إيقاف الاختبار البعدي للطالب." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث إتاحة الاختبار البعدي" });
    } finally {
      setBusy("");
    }
  };

  const saveManualOverride = async () => {
    if (!student) return;
    setBusy("override");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/adaptation/manual-override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_level: Number(overrideLevel), reason: overrideReason.trim() }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ التعديل اليدوي"));
      const refreshed = await fetch(`/api/researcher/students/${student.id}`, { cache: "no-store" });
      if (refreshed.ok) {
        const updated: Student = await refreshed.json();
        setStudent(updated);
        setEditName(updated.full_name);
      }
      setOverrideReason("");
      await refreshAdaptiveEvidence();
      setMessage({ kind: "success", text: "تم حفظ قرار المشرف مع سببه في السجل." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ التعديل اليدوي" });
    } finally {
      setBusy("");
    }
  };

  if (loading) {
    return <div className="flex-1 flex flex-col items-center justify-center gap-3 py-16"><div className="spinner w-10 h-10" /><p className="text-muted">جاري تحميل ملف الطالب...</p></div>;
  }

  if (!student) {
    return (
      <div className="flex-1 font-plex max-w-4xl mx-auto w-full">
        <div className="alert-error">{message.text || "لم يتم العثور على الطالب"}</div>
        <Link href="/admin/students" className="btn-primary mt-4">العودة إلى الطلاب</Link>
      </div>
    );
  }

  const progressPercent = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
  const reasonKey = typeof latestDecision?.explanation?.reason === "string" ? latestDecision.explanation.reason : "";

  return (
    <div className="flex-1 font-plex max-w-6xl mx-auto w-full" dir="rtl">
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <Link href="/admin/students" className="p-2 text-muted hover:text-navy hover:bg-bg rounded-full transition-colors" aria-label="العودة إلى الطلاب"><ArrowRight size={24} /></Link>
          <div><p className="text-sm text-primary font-semibold">إدارة الطلاب</p><h1 className="text-2xl font-bold text-navy">ملف الطالب</h1></div>
        </div>
        <button className={student.status === "active" ? "btn-secondary" : "btn-primary"} onClick={() => void toggleStudentStatus()} disabled={busy === "status"}>
          <Power size={17} /> {busy === "status" ? "جاري الحفظ..." : student.status === "active" ? "إيقاف الحساب" : "تفعيل الحساب"}
        </button>
      </div>

      {message.text && <div className={`${message.kind === "success" ? "alert-success" : "alert-error"} mb-5`}>{message.text}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-[310px_1fr] gap-6">
        <div className="space-y-6">
          <section className="card text-center">
            <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 text-primary"><User size={38} /></div>
            <h2 className="text-xl font-bold text-navy mb-1">{student.full_name}</h2>
            <p className="text-muted mb-4">الصف الثالث الابتدائي</p>
            <span className={`badge w-full justify-center py-2 ${student.status === "active" ? "badge-green" : "badge-gray"}`}>{student.status === "active" ? "حساب نشط" : "حساب موقوف"}</span>
          </section>

          <section className="card">
            <div className="flex items-center gap-2 mb-4"><KeyRound size={19} className="text-primary" /><h3 className="font-bold text-navy">رمز الدخول</h3></div>
            <div className="rounded-xl bg-bg border border-border p-4 text-center mb-4">
              <p className="text-xs text-muted mb-2">الرمز الحالي</p>
              <div className="flex items-center justify-center gap-3" dir="ltr">
                <strong className="text-2xl font-mono tracking-widest text-primary">{student.access_code}</strong>
                <button onClick={() => void copyAccessCode()} className="p-2 rounded-md hover:bg-white text-muted" aria-label="نسخ رمز الدخول">{copied ? <Check size={18} className="text-green" /> : <Copy size={18} />}</button>
              </div>
            </div>
            <div className="space-y-3">
              <button className="btn-secondary w-full" onClick={() => void changeAccessCode(false)} disabled={busy === "code"}><RefreshCw size={16} /> توليد رمز جديد</button>
              <div className="border-t border-border pt-3">
                <label htmlFor="manual-code" className="block text-xs text-muted mb-2">أو اكتب رمزًا من 6 أرقام</label>
                <div className="flex gap-2">
                  <input id="manual-code" className="input-field text-center font-mono tracking-widest" inputMode="numeric" maxLength={6} value={manualCode} onChange={(event) => setManualCode(event.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="123456" dir="ltr" />
                  <button className="btn-primary px-4" onClick={() => void changeAccessCode(true)} disabled={busy === "code" || manualCode.length !== 6}>حفظ</button>
                </div>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="flex items-center gap-2 mb-3 text-navy font-bold"><Star size={19} className="text-yellow-500" /><span>التعزيز</span></div>
            <p className="text-sm text-muted">نجوم ناتجة عن إنجازات فعلية</p>
            <p className="text-3xl font-bold text-navy mt-2">{totalStars}</p>
            {badges.length > 0 && <div className="mt-4 space-y-2">{badges.map((badge) => <div key={badge.id} className="rounded-lg bg-green/10 text-green px-3 py-2 text-sm font-bold">{badge.label}</div>)}</div>}
          </section>
        </div>

        <div className="space-y-6">
          <section className="card">
            <div className="flex items-center justify-between gap-3 mb-5 border-b border-border pb-3"><div className="flex items-center gap-2"><PencilLine size={19} className="text-primary" /><h3 className="text-lg font-bold text-navy">بيانات الطالب</h3></div><span className="text-xs text-muted">المعرف #{student.id}</span></div>
            <div className="grid md:grid-cols-[1fr_auto] gap-3 items-end mb-5">
              <label className="text-sm text-navy">اسم الطالب
                <input className="input-field mt-2" value={editName} onChange={(event) => setEditName(event.target.value)} minLength={2} maxLength={80} />
              </label>
              <button className="btn-primary" onClick={() => void saveStudentName()} disabled={busy === "name" || editName.trim() === student.full_name}><Save size={17} /> {busy === "name" ? "جاري الحفظ..." : "حفظ الاسم"}</button>
            </div>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="flex items-start gap-3"><Hash className="text-muted mt-0.5" size={18} /><div><p className="text-sm text-muted">المستوى الحالي</p><p className="text-navy font-semibold">المستوى {student.current_level}</p></div></div>
              <div className="flex items-start gap-3"><BookOpen className="text-muted mt-0.5" size={18} /><div><p className="text-sm text-muted">الصف</p><p className="text-navy font-semibold">الثالث الابتدائي</p></div></div>
              <div className="flex items-start gap-3"><Calendar className="text-muted mt-0.5" size={18} /><div><p className="text-sm text-muted">تاريخ الإضافة</p><p className="text-navy">{new Date(student.created_at).toLocaleDateString("ar-SA")}</p></div></div>
            </div>
          </section>

          <section className="card">
            <div className="flex items-center justify-between gap-4 mb-4 border-b border-border pb-3"><h3 className="text-lg font-bold text-navy">المسار التعليمي</h3><BookOpen size={20} className="text-primary" /></div>
            <div className="flex items-center justify-between text-sm mb-2"><span className="text-muted">الأنشطة الأساسية المكتملة</span><strong className="text-navy">{student.core_completed_items} من {student.core_total_items}</strong></div>
            <div className="w-full h-3 rounded-full bg-bg overflow-hidden" aria-label={`تقدم الأنشطة ${progressPercent}%`}><div className="h-full bg-green rounded-full" style={{ width: `${progressPercent}%` }} /></div>
          </section>

          <section className="card" data-testid="adaptation-panel">
            <div className="flex items-center justify-between gap-4 mb-4 border-b border-border pb-3"><div><h3 className="text-lg font-bold text-navy">قرار التكيف</h3><p className="text-xs text-muted mt-1">آخر قرار محفوظ وسجل التعديلات</p></div><Activity size={20} className="text-primary" /></div>
            {!latestDecision ? (
              <p className="text-sm text-muted">لا يوجد قرار تكيف محفوظ بعد. يبدأ القرار بعد توفر ثلاث محاولات صالحة.</p>
            ) : (
              <div className="space-y-3">
                <div className="grid sm:grid-cols-3 gap-3">
                  <div className="bg-bg rounded-xl p-3"><p className="text-xs text-muted">القرار</p><p className="font-bold text-navy">{ACTION_LABEL[latestDecision.action] || latestDecision.action}</p></div>
                  <div className="bg-bg rounded-xl p-3"><p className="text-xs text-muted">الإتقان المتحرك</p><p className="font-bold text-navy">{latestDecision.mastery_score == null ? "—" : `${latestDecision.mastery_score.toFixed(1)}%`}</p></div>
                  <div className="bg-bg rounded-xl p-3"><p className="text-xs text-muted">المستوى</p><p className="font-bold text-navy">{latestDecision.previous_level} ← {latestDecision.new_level}</p></div>
                </div>
                <p className="text-sm text-muted">{REASON_LABEL[reasonKey] || reasonKey || "السبب محفوظ ضمن سجل القرار."}</p>
                {latestDecision.recommended_item_id && <p className="text-sm text-primary font-bold">تم ربط نشاط تقوية معتمد بالمهارة الأضعف.</p>}
              </div>
            )}

            <div className="mt-6 border-t border-border pt-5">
              <div className="flex items-center gap-2 mb-2"><ShieldCheck size={18} className="text-green" /><h4 className="font-bold text-navy">تعديل المشرف</h4></div>
              <p className="text-xs text-muted mb-4">لا يحذف القرار الآلي؛ يُحفظ التعديل اليدوي كحدث مستقل مع السبب والتاريخ.</p>
              <div className="grid md:grid-cols-[145px_1fr_auto] gap-3 items-end">
                <label className="text-sm text-navy">المستوى
                  <select className="input-field mt-2" value={overrideLevel} onChange={(event) => setOverrideLevel(event.target.value)}>
                    <option value="1">المستوى 1</option><option value="2">المستوى 2</option><option value="3">المستوى 3</option>
                  </select>
                </label>
                <label className="text-sm text-navy">سبب التعديل
                  <input className="input-field mt-2" value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} placeholder="اكتب سبب القرار" maxLength={1000} />
                </label>
                <button className="btn-primary" onClick={() => void saveManualOverride()} disabled={busy === "override" || overrideReason.trim().length < 5}>{busy === "override" ? "جاري الحفظ..." : "حفظ القرار"}</button>
              </div>
            </div>

            {history.length > 0 && (
              <div className="mt-6 border-t border-border pt-5">
                <h4 className="font-bold text-navy mb-3">سجل القرارات</h4>
                <div className="space-y-2 max-h-64 overflow-auto">
                  {[...history].reverse().map((decision) => (
                    <div key={decision.decision_id} className="rounded-xl border border-border px-3 py-3 text-sm flex flex-wrap justify-between gap-2">
                      <span className="font-bold text-navy">{ACTION_LABEL[decision.action] || decision.action}</span>
                      <span className="text-muted">{decision.source === "manual" ? "يدوي" : "آلي"} · {new Date(decision.created_at).toLocaleString("ar-SA")}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="card">
            <div className="flex items-center justify-between gap-4 mb-4 border-b border-border pb-3"><div><h3 className="text-lg font-bold text-navy">الاختبار البعدي</h3><p className="text-xs text-muted mt-1">يُفتح فقط بعد استيفاء المسار المطلوب</p></div><Play size={20} className="text-primary" /></div>
            <div className="rounded-xl bg-bg border border-border p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-muted text-sm leading-7">{student.posttest_enabled ? "الاختبار البعدي متاح للطالب الآن." : student.posttest_eligible ? "اكتمل المسار ويمكن فتح الاختبار البعدي." : "يتاح بعد إكمال الاختبار القبلي والأنشطة التعليمية المطلوبة."}</p>
              <button className="btn-primary whitespace-nowrap" onClick={() => void updatePosttestAccess()} disabled={busy === "posttest" || (!student.posttest_eligible && !student.posttest_enabled)}>{busy === "posttest" ? "جاري الحفظ..." : student.posttest_enabled ? "إيقاف الإتاحة" : "فتح الاختبار"}</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
