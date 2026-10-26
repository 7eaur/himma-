"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
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

// Validate both GET and POST payloads at the UI boundary. A 200 response
// with an incomplete or stale body must not render a wrong question/progress.
function isAssessmentPayload(value: unknown, sessionId: number, expectedKind?: AssessmentPayload["session"]["kind"]): value is AssessmentPayload {
  if (!value || typeof value !== "object") return false;
  const data = value as Partial<AssessmentPayload>;
  const session = data.session;
  const progress = session?.progress;
  const summary = data.summary;
  if (!session || session.session_id !== sessionId ||
      (session.kind !== "pretest" && session.kind !== "posttest") ||
      (expectedKind !== undefined && session.kind !== expectedKind) ||
      !["answering", "waiting_review", "placement_pending_review", "completed"].includes(session.state) ||
      !progress || !Number.isInteger(progress.answered) || !Number.isInteger(progress.total) ||
      progress.total !== 30 || progress.answered < 0 || progress.answered > progress.total ||
      !summary || !Number.isInteger(summary.pending_review) ||
      summary.pending_review < 0 || summary.pending_review > progress.answered) return false;

  if (session.state !== "answering") return data.interaction === null;
  const interaction = data.interaction;
  return !!interaction && typeof interaction === "object" &&
    typeof interaction.question?.question_id === "string" &&
    typeof interaction.question?.interaction === "string" &&
    Array.isArray(interaction.question?.options) &&
    !!interaction.media && typeof interaction.media === "object" && !Array.isArray(interaction.media) &&
    interaction.question.role === session.kind &&
    !!interaction.progress &&
    interaction.progress.stage === session.kind &&
    interaction.progress.total === progress.total &&
    interaction.progress.index === progress.answered + 1 &&
    progress.answered < progress.total;
}

export default function AssessmentV2Page() {
  const params = useParams<{ sessionId: string }>();
  // Next may reuse the page component across dynamic-route transitions.
  // Key the session state to its route to prevent stale learner data flashing.
  return <AssessmentV2Session key={params.sessionId} sessionId={Number(params.sessionId)} />;
}

function AssessmentV2Session({ sessionId }: { sessionId: number }) {
  const router = useRouter();
  const invalid = !Number.isInteger(sessionId) || sessionId < 1;
  const [assessment, setAssessment] = useState<AssessmentPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const loadControllerRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    if (invalid) return;
    // Only the latest mounted assessment may handle GET, including 401/403.
    // A stale unauthorized response must never redirect a newer route.
    loadControllerRef.current?.abort();
    const controller = new AbortController();
    loadControllerRef.current = controller;
    try {
      const response = await fetch(`/api/v2/assessments/sessions/${sessionId}`, {
        cache: "no-store", signal: controller.signal,
      });
      const data = await response.json().catch(() => null);
      if (controller.signal.aborted || loadControllerRef.current !== controller) return;
      if (response.status === 401 || response.status === 403) { router.replace("/student/login"); return; }
      if (!response.ok) throw new Error(response.status === 404
        ? "جلسة التقييم غير متاحة لهذا الحساب."
        : "تعذر استعادة التقييم. تقدّمك محفوظ، حاول مرة أخرى.");
      // Fail closed if a delayed/cached/misrouted response belongs to another
      // assessment. Never render another session's question or progress.
      if (!isAssessmentPayload(data, sessionId)) {
        throw new Error("تعذر استعادة التقييم. تحقق من الرابط وحاول مرة أخرى.");
      }
      // A successful retry supersedes the earlier transport/identity error.
      // Never show a stale failure banner above the recovered question.
      setError("");
      setAssessment(data);
    } catch (reason) {
      if (!controller.signal.aborted) throw reason;
    } finally {
      if (loadControllerRef.current === controller) loadControllerRef.current = null;
    }
  }, [invalid, router, sessionId]);

  useEffect(() => {
    let mounted = true;
    const timer = window.setTimeout(() => {
      void load()
        .catch(reason => { if (mounted) setError(reason instanceof Error ? reason.message : "تعذر استعادة التقييم"); })
        .finally(() => { if (mounted) setLoading(false); });
    }, 0);
    return () => {
      mounted = false;
      window.clearTimeout(timer);
      loadControllerRef.current?.abort();
      loadControllerRef.current = null;
    };
  }, [load]);

  // The POST /answers response is a second source of session state, not a
  // trusted replacement for the GET response. A stale/misrouted acknowledgement
  // must never render another session or switch pretest to posttest.
  const handleAssessmentChange = (value: unknown) => {
    if (!isAssessmentPayload(value, sessionId, assessment?.session.kind) ||
        !assessment ||
        value.session.progress.total !== assessment.session.progress.total ||
        value.session.progress.answered !== assessment.session.progress.answered + 1) {
      // A successful POST must advance exactly one question. A structurally
      // valid stale or skipped counter is not proof of saved progress.
      // The answer may already be committed: do not replay it from this
      // component. Unmount the question and recover authoritative state via GET.
      setAssessment(null);
      setError("تعذر تأكيد حفظ الإجابة. تقدّمك محفوظ، حاول استعادة التقييم.");
      return;
    }
    setError("");
    setAssessment(value);
  };

  if (invalid) return <main className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error}>رابط جلسة التقييم غير صالح</div></div></main>;
  if (loading) return <main className={styles.page} dir="rtl"><div className={styles.loading}><div><div className={styles.spinner}/><p>نستعيد إجاباتك المحفوظة...</p><Link href="/student" className={styles.back}>لوحة الطالب</Link></div></div></main>
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
      {assessment.session.state === "answering" && assessment.interaction && <InteractionPlayer key={assessment.interaction.question.question_id} sessionId={sessionId} interaction={assessment.interaction} endpointBase="/api/v2/assessments" onLessonChange={handleAssessmentChange}/>} 
      {assessment.session.state === "waiting_review" && <section className={styles.practiceBoundary}><Clock3 size={32}/><h2>إجاباتك محفوظة وتنتظر المراجعة</h2><p>لديك {assessment.summary.pending_review} إجابة قراءة أو كتابة. لن تُحسب صحيحة أو خاطئة قبل مراجعة المشرف.</p><StudentRetryTasks kind="assessment" sessionId={sessionId}/></section>}
      {assessment.session.state === "placement_pending_review" && <section className={styles.practiceBoundary}><Clock3 size={32}/><h2>اكتمل الاختبار وينتظر التسكين</h2><p>سيعتمد المشرف المستوى المناسب بسبب موثق. لا تستخدم هِمّة حدودًا رقمية غير معتمدة.</p></section>}
      {assessment.session.state === "completed" && <section className={styles.practiceBoundary}><CheckCircle2 size={32}/><h2>اكتمل {title}</h2><p>{assessment.session.kind === "posttest" ? "أصبحت نتيجتك النهائية محفوظة في التقرير." : "تم اعتماد مستواك وأصبحت رحلتك التعليمية جاهزة."}</p><Link href="/student/learning-v2" className={styles.back}>متابعة الرحلة</Link></section>}
    </section>
  </div></main>;
}
