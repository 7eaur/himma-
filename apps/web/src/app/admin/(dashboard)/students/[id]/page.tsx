"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, BookOpen, Calendar, Hash, Play, ShieldCheck, Star, User } from "lucide-react";
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
  researcher_manual_override: "قرار يدوي موثق من الباحثة",
};

export default function StudentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [history, setHistory] = useState<AdaptationDecision[]>([]);
  const [rewards, setRewards] = useState<RewardEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingPosttest, setUpdatingPosttest] = useState(false);
  const [savingOverride, setSavingOverride] = useState(false);
  const [overrideLevel, setOverrideLevel] = useState("1");
  const [overrideReason, setOverrideReason] = useState("");
  const [error, setError] = useState("");

  const loadAdaptiveEvidence = async () => {
    const [historyRes, rewardsRes] = await Promise.all([
      fetch(`/api/researcher/students/${id}/adaptation/history`),
      fetch(`/api/researcher/students/${id}/rewards`),
    ]);
    if (historyRes.ok) setHistory(await historyRes.json());
    if (rewardsRes.ok) setRewards(await rewardsRes.json());
  };

  useEffect(() => {
    const fetchStudent = async () => {
      try {
        const res = await fetch(`/api/researcher/students/${id}`);
        if (res.ok) {
          const data: Student = await res.json();
          setStudent(data);
          setOverrideLevel(String(data.current_level));
          await loadAdaptiveEvidence();
        } else if (res.status === 404) {
          setError("لم يتم العثور على الطالب");
        } else {
          setError("تعذر تحميل بيانات الطالب");
        }
      } catch {
        setError("حدث خطأ أثناء تحميل بيانات الطالب");
      } finally {
        setLoading(false);
      }
    };

    if (id) void fetchStudent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const latestDecision = useMemo(() => history.at(-1) ?? null, [history]);
  const totalStars = rewards.reduce((sum, reward) => sum + (reward.stars ?? 0), 0);
  const badges = rewards.filter((reward) => reward.type === "badge");

  const updatePosttestAccess = async () => {
    if (!student) return;
    setUpdatingPosttest(true);
    setError("");
    try {
      const res = await fetch(`/api/researcher/students/${student.id}/posttest-access`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !student.posttest_enabled }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "تعذر تحديث إتاحة الاختبار البعدي");
      setStudent(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تعذر تحديث إتاحة الاختبار البعدي");
    } finally {
      setUpdatingPosttest(false);
    }
  };

  const saveManualOverride = async () => {
    if (!student) return;
    setSavingOverride(true);
    setError("");
    try {
      const res = await fetch(`/api/researcher/students/${student.id}/adaptation/manual-override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_level: Number(overrideLevel), reason: overrideReason.trim() }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.detail?.[0]?.msg || data?.detail || "تعذر حفظ التعديل اليدوي");
      const refreshed = await fetch(`/api/researcher/students/${student.id}`);
      if (refreshed.ok) setStudent(await refreshed.json());
      setOverrideReason("");
      await loadAdaptiveEvidence();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تعذر حفظ التعديل اليدوي");
    } finally {
      setSavingOverride(false);
    }
  };

  if (loading) {
    return <div className="flex-1 flex justify-center py-12"><div className="spinner w-8 h-8" /></div>;
  }

  if (!student) {
    return (
      <div className="flex-1 font-plex max-w-4xl mx-auto w-full">
        <div className="alert-error">{error || "لم يتم العثور على الطالب"}</div>
        <Link href="/admin/students" className="btn-primary mt-4">العودة لقائمة الطلاب</Link>
      </div>
    );
  }

  const progressPercent = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
  const reasonKey = typeof latestDecision?.explanation?.reason === "string" ? latestDecision.explanation.reason : "";

  return (
    <div className="flex-1 font-plex max-w-5xl mx-auto w-full">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/students" className="p-2 text-muted hover:text-navy hover:bg-bg rounded-full transition-colors">
          <ArrowRight size={24} />
        </Link>
        <h1 className="text-2xl font-bold text-navy">ملف الطالب</h1>
      </div>

      {error && <div className="alert-error mb-5">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-6">
          <div className="card text-center">
            <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 text-primary">
              <User size={48} />
            </div>
            <h2 className="text-xl font-bold text-navy mb-1">{student.full_name}</h2>
            <p className="text-muted mb-4">الصف {student.grade_level}</p>
            <div className="bg-bg p-3 rounded-md mb-4">
              <p className="text-xs text-muted mb-1">رمز الدخول</p>
              <p className="text-lg font-mono font-bold text-primary tracking-widest">{student.access_code}</p>
            </div>
            <span className="badge bg-green/10 text-green w-full py-2">{student.status === "active" ? "نشط" : "غير نشط"}</span>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-3 text-navy font-bold"><Star size={19} className="text-yellow-500" /><span>التعزيز</span></div>
            <p className="text-sm text-muted">النجوم المكتسبة من إنجازات فعلية</p>
            <p className="text-2xl font-bold text-navy mt-2">{totalStars}</p>
            {badges.length > 0 && (
              <div className="mt-4 space-y-2">
                {badges.map((badge) => <div key={badge.id} className="rounded-lg bg-green/10 text-green px-3 py-2 text-sm font-bold">{badge.label}</div>)}
              </div>
            )}
          </div>
        </div>

        <div className="md:col-span-2 space-y-6">
          <div className="card">
            <h3 className="text-lg font-bold text-navy mb-4 border-b border-border pb-2">المعلومات الأساسية</h3>
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="flex items-start gap-3"><Hash className="text-muted mt-0.5" size={18} /><div><p className="text-sm text-muted">المعرف</p><p className="text-navy text-sm font-mono">{student.id}</p></div></div>
              <div className="flex items-start gap-3"><Hash className="text-muted mt-0.5" size={18} /><div><p className="text-sm text-muted">المستوى الحالي</p><p className="text-navy">المستوى {student.current_level}</p></div></div>
              <div className="flex items-start gap-3"><Calendar className="text-muted mt-0.5" size={18} /><div><p className="text-sm text-muted">تاريخ الإضافة</p><p className="text-navy">{new Date(student.created_at).toLocaleDateString("ar-SA")}</p></div></div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between gap-4 mb-4 border-b border-border pb-2">
              <h3 className="text-lg font-bold text-navy">المسار التعليمي</h3><BookOpen size={20} className="text-primary" />
            </div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-muted">الأنشطة الأساسية المكتملة</span>
              <strong className="text-navy">{student.core_completed_items} من {student.core_total_items}</strong>
            </div>
            <div className="w-full h-3 rounded-full bg-bg overflow-hidden" aria-label={`تقدم الأنشطة ${progressPercent}%`}>
              <div className="h-full bg-green rounded-full" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>

          <div className="card" data-testid="adaptation-panel">
            <div className="flex items-center justify-between gap-4 mb-4 border-b border-border pb-2">
              <h3 className="text-lg font-bold text-navy">قرار التكيف</h3><Activity size={20} className="text-primary" />
            </div>
            {!latestDecision ? (
              <p className="text-sm text-muted">لا يوجد قرار تكيف محفوظ بعد. يبدأ القرار بعد توفر ثلاث محاولات صالحة.</p>
            ) : (
              <div className="space-y-3">
                <div className="grid sm:grid-cols-3 gap-3">
                  <div className="bg-bg rounded-lg p-3"><p className="text-xs text-muted">القرار</p><p className="font-bold text-navy">{ACTION_LABEL[latestDecision.action] || latestDecision.action}</p></div>
                  <div className="bg-bg rounded-lg p-3"><p className="text-xs text-muted">الإتقان المتحرك</p><p className="font-bold text-navy">{latestDecision.mastery_score == null ? "—" : `${latestDecision.mastery_score.toFixed(1)}%`}</p></div>
                  <div className="bg-bg rounded-lg p-3"><p className="text-xs text-muted">المستوى</p><p className="font-bold text-navy">{latestDecision.previous_level} ← {latestDecision.new_level}</p></div>
                </div>
                <p className="text-sm text-muted">{REASON_LABEL[reasonKey] || reasonKey || "السبب محفوظ ضمن سجل القرار."}</p>
                {latestDecision.recommended_item_id && <p className="text-sm text-primary font-bold">تم ربط نشاط موجه بالمهارة الأضعف دون استبدال المحتوى المعتمد.</p>}
              </div>
            )}

            <div className="mt-5 border-t border-border pt-4">
              <div className="flex items-center gap-2 mb-3"><ShieldCheck size={18} className="text-green" /><h4 className="font-bold text-navy">تعديل الباحثة</h4></div>
              <p className="text-xs text-muted mb-3">التعديل اليدوي لا يحذف القرار الآلي، ويُحفظ كحدث مستقل مع السبب.</p>
              <div className="grid sm:grid-cols-[140px_1fr_auto] gap-3 items-end">
                <label className="text-sm text-navy">المستوى
                  <select className="input mt-1 w-full" value={overrideLevel} onChange={(event) => setOverrideLevel(event.target.value)}>
                    <option value="1">المستوى 1</option><option value="2">المستوى 2</option><option value="3">المستوى 3</option>
                  </select>
                </label>
                <label className="text-sm text-navy">السبب
                  <input className="input mt-1 w-full" value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} placeholder="اكتبي سبب القرار البحثي" maxLength={1000} />
                </label>
                <button className="btn-primary" onClick={saveManualOverride} disabled={savingOverride || overrideReason.trim().length < 5}>{savingOverride ? "جاري الحفظ..." : "حفظ القرار"}</button>
              </div>
            </div>

            {history.length > 0 && (
              <div className="mt-5 border-t border-border pt-4">
                <h4 className="font-bold text-navy mb-3">سجل القرارات</h4>
                <div className="space-y-2 max-h-56 overflow-auto">
                  {[...history].reverse().map((decision) => (
                    <div key={decision.decision_id} className="rounded-lg border border-border px-3 py-2 text-sm flex flex-wrap justify-between gap-2">
                      <span className="font-bold text-navy">{ACTION_LABEL[decision.action] || decision.action}</span>
                      <span className="text-muted">{decision.source === "manual" ? "يدوي" : "آلي"} · {new Date(decision.created_at).toLocaleString("ar-SA")}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-navy mb-4 border-b border-border pb-2">الاختبارات</h3>
            <div className="flex flex-col items-center justify-center py-8 text-center border-2 border-dashed border-border rounded-lg">
              <p className="text-muted mb-4">
                {student.posttest_enabled ? "الاختبار البعدي متاح للطالب الآن." : student.posttest_eligible ? "اكتمل المسار المطلوب ويمكن إتاحة الاختبار البعدي." : "يتاح الاختبار البعدي بعد اكتمال المسار التعليمي المطلوب."}
              </p>
              <button className="btn-primary flex items-center gap-2" onClick={updatePosttestAccess} disabled={updatingPosttest || (!student.posttest_eligible && !student.posttest_enabled)}>
                <Play size={18} /><span>{updatingPosttest ? "جاري الحفظ..." : student.posttest_enabled ? "إيقاف إتاحة الاختبار البعدي" : "إتاحة الاختبار البعدي"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
