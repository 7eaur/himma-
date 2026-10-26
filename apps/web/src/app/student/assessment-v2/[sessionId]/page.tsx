"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Clock3 } from "lucide-react";
import InteractionPlayer, { type InteractionPayload } from "@/components/learning/InteractionPlayer";
import StudentRetryTasks from "@/components/learning/StudentRetryTasks";
import styles from "../../learning-v2/learning-v2.module.css";

interface AssessmentPayload {
  session: { session_id: number; kind: "pretest" | "posttest"; state: "answering" | "waiting_review" | "placement_pending_review" | "completed"; progress: { answered: number; total: number } };
  interaction: InteractionPayload | null;
  summary: { pending_review: number };
  outcome?: { score_percent: number | null; skills: Record<string, unknown> };
}

export default function AssessmentV2Page() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = Number(params.sessionId);
  const invalid = !Number.isInteger(sessionId) || sessionId < 1;
  const [assessment, setAssessment] = useState<AssessmentPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (invalid) return;
    const response = await fetch(`/api/v2/assessments/sessions/${sessionId}`, { cache: "no-store" });
    const data = await response.json().catch(() => null);
    if (response.status === 401 || response.status === 403) { router.replace("/student/login"); return; }
    if (!response.ok) throw new Error(response.status === 404
      ? "جلسة التقييم غير متاحة لهذا الحساب."
      : "تعذر استعادة التقييم. تقدّمك محفوظ، حاول مرة أخرى.");
    setAssessment(data);
  }, [invalid, router, sessionId]);

  useEffect(() => { const timer = window.setTimeout(() => { void load().catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر استعادة التقييم")).finally(() => setLoading(false)); }, 0); return () => window.clearTimeout(timer); }, [load]);

  if (invalid) return <main className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error}>رابط جلسة التقييم غير صالح</div></div></main>;
  if (loading) return <main className={styles.page} dir="rtl"><div className={styles.loading}><div><div className={styles.spinner}/><p>نستعيد إجاباتك المحفوظة...</p></div></div></main>;
  if (!assessment) return <main className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error} role="alert">{error || "تعذر فتح التقييم"}</div><button type="button" className={styles.primary} onClick={() => {
    setError(""); setLoading(true);
    void load().catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر استعادة التقييم")).finally(() => setLoading(false));
  }}>إعادة المحاولة</button><Link href="/student" className={styles.back}>لوحة الطالب</Link></div></main>;
  const title = assessment.session.kind === "pretest" ? "الاختبار القبلي" : "الاختبار البعدي";

  return <main className={styles.page} dir="rtl"><div className={styles.container}>
    <header className={styles.header}><Image src="/brand/logo-gradient.svg" alt="هِمّة" width={126} height={42} priority/><Link href="/student" className={styles.back}>لوحة الطالب</Link></header>
    <section className={styles.lessonCard}><span className={styles.eyebrow}>{title} · 30 سؤالًا</span><h1>{title}</h1>
      <p>تقدمك محفوظ تلقائيًا. لا تظهر تلميحات أو صحة الإجابة أثناء التقييم.</p>
      {error && <div className={styles.error} role="alert">{error}</div>}
      {assessment.session.state === "answering" && assessment.interaction && <InteractionPlayer key={assessment.interaction.question.question_id} sessionId={sessionId} interaction={assessment.interaction} endpointBase="/api/v2/assessments" onLessonChange={(value) => setAssessment(value as AssessmentPayload)}/>} 
      {assessment.session.state === "waiting_review" && <section className={styles.practiceBoundary}><Clock3 size={32}/><h2>إجاباتك محفوظة وتنتظر المراجعة</h2><p>لديك {assessment.summary.pending_review} إجابة قراءة أو كتابة. لن تُحسب صحيحة أو خاطئة قبل مراجعة المشرف.</p><StudentRetryTasks kind="assessment" sessionId={sessionId}/></section>}
      {assessment.session.state === "placement_pending_review" && <section className={styles.practiceBoundary}><Clock3 size={32}/><h2>اكتمل الاختبار وينتظر التسكين</h2><p>سيعتمد المشرف المستوى المناسب بسبب موثق. لا تستخدم هِمّة حدودًا رقمية غير معتمدة.</p></section>}
      {assessment.session.state === "completed" && <section className={styles.practiceBoundary}><CheckCircle2 size={32}/><h2>اكتمل {title}</h2><p>{assessment.session.kind === "posttest" ? "أصبحت نتيجتك النهائية محفوظة في التقرير." : "تم اعتماد مستواك وأصبحت رحلتك التعليمية جاهزة."}</p><Link href="/student/learning-v2" className={styles.back}>متابعة الرحلة</Link></section>}
    </section>
  </div></main>;
}
