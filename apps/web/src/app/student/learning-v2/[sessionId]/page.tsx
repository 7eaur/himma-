"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import VideoPlayer from "@/components/learning/VideoPlayer";
import InteractionPlayer, { type InteractionPayload } from "@/components/learning/InteractionPlayer";
import StudentRetryTasks from "@/components/learning/StudentRetryTasks";
import styles from "../learning-v2.module.css";

type Stage = "intro" | "teaching_video" | "guided_practice" | "independent_check" | "additional_check" | "support_practice" | "support_check" | "supervisor_hold" | "outcome";
interface LessonPayload {
  lesson_id: string; title: string; level: string; objective?: string | null;
  intro: { title: string; text: string; button: string };
  video: { asset_id: string; url: string | null; test_only: boolean; state: string };
  practice: { count: number; first_question_id: string };
  independent_check: { count: number };
  session: { session_id: number; stage: Stage | "waiting_review"; status: string; video_position_seconds: number; video_duration_seconds: number | null; version: number };
  interaction?: InteractionPayload | null;
  summary?: { submitted: number; pending_review: number };
  adaptation?: { state: string; message: string; support?: { title: string; focus: string; mode: string } | null } | null;
}
const STAGES: Array<{ key: Stage; label: string }> = [{key:"intro",label:"المقدمة"},{key:"teaching_video",label:"الشرح"},{key:"guided_practice",label:"التدريب"},{key:"independent_check",label:"الاختبار"}];

function eventKey(type: string) { return `${type}:${Date.now()}:${crypto.randomUUID()}`; }

export default function V2LessonPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [lesson, setLesson] = useState<LessonPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const sessionId = Number(params.sessionId);
  const invalidSessionId = !Number.isInteger(sessionId) || sessionId < 1;

  const loadLesson = useCallback(async () => {
    if (invalidSessionId) return;
    return fetch(`/api/v2/lessons/sessions/${sessionId}/interaction`, { cache: "no-store" }).then(async (response) => {
      const data = await response.json().catch(() => null);
      if (response.status === 401 || response.status === 403) { router.replace("/student/login"); return; }
      if (!response.ok) throw new Error(data?.detail || "تعذر استعادة الدرس");
      setLesson(data);
    });
  }, [invalidSessionId, router, sessionId]);

  useEffect(() => {
    void loadLesson().catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر استعادة الدرس")).finally(() => setLoading(false));
  }, [loadLesson]);

  const sendEvent = useCallback(async (event_type: "intro_complete" | "video_progress" | "video_ended", position_seconds?: number, duration_seconds?: number) => {
    const response = await fetch(`/api/v2/lessons/sessions/${sessionId}/events`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ event_key:eventKey(event_type), event_type, position_seconds, duration_seconds }), keepalive:event_type === "video_progress" });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "تعذر حفظ تقدم الدرس");
    if (["guided_practice", "independent_check", "waiting_review", "outcome"].includes(data?.session?.stage)) await loadLesson();
    else setLesson(data);
  }, [loadLesson, sessionId]);

  const completeIntro = async () => { setSaving(true); setError(""); try { await sendEvent("intro_complete"); } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر فتح الفيديو"); } finally { setSaving(false); } };
  const checkpoint = useCallback((position: number, duration: number) => { void sendEvent("video_progress", position, duration).catch(() => setError("تعذر حفظ موضع الفيديو مؤقتًا. حاول الإيقاف ثم التشغيل.")); }, [sendEvent]);
  const ended = useCallback((position: number, duration: number) => { void sendEvent("video_ended", position, duration).catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر حفظ اكتمال الفيديو")); }, [sendEvent]);

  if (invalidSessionId) return <div className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error} role="alert">رابط جلسة الدرس غير صالح</div><Link href="/student/learning-v2" className={styles.back}><ArrowRight size={17}/> العودة إلى الدروس</Link></div></div>;
  if (loading) return <div className={styles.page} dir="rtl"><div className={styles.loading}><div><div className={styles.spinner} /><p>نستعيد موضعك المحفوظ...</p></div></div></div>;
  if (!lesson) return <div className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error} role="alert">{error || "تعذر فتح الدرس"}</div><Link href="/student/learning-v2" className={styles.back}><ArrowRight size={17}/> العودة إلى الدروس</Link></div></div>;
  const stageIndex = STAGES.findIndex((stage) => stage.key === lesson.session.stage);
  const activeIndex = stageIndex >= 0 ? stageIndex : STAGES.length - 1;
  const captions = lesson.video.test_only ? `${lesson.video.url}/captions` : undefined;

  return <div className={styles.page} dir="rtl"><div className={styles.container}>
    <header className={styles.header}><Image src="/brand/logo-gradient.svg" alt="هِمّة" width={126} height={42} priority /><Link href="/student/learning-v2" className={styles.back}><ArrowRight size={17}/> الدروس</Link></header>
    <main className={styles.lessonCard}><span className={styles.eyebrow}>{lesson.level} · {lesson.lesson_id}</span><h1>{lesson.title}</h1>{lesson.objective && <p>{lesson.objective}</p>}
      <div className={styles.progress} aria-label="مراحل الدرس">{STAGES.map((stage,index) => <span key={stage.key} className={index === activeIndex ? styles.active : ""} aria-current={index === activeIndex ? "step" : undefined}>{index < activeIndex ? "✓ " : ""}{stage.label}</span>)}</div>
      {error && <div className={styles.error} role="alert">{error}</div>}
      {lesson.session.stage === "intro" && <section className={styles.intro}><div><span className={styles.eyebrow}>هيا نبدأ</span><h2>{lesson.intro.title}</h2><p>{lesson.intro.text}</p><button type="button" className={styles.primary} disabled={saving} onClick={() => void completeIntro()}>{saving ? "جاري الحفظ..." : lesson.intro.button}<ArrowLeft size={18}/></button></div><Image src="/characters/girl/welcome.png" alt="شخصية هِمّة ترحب" width={180} height={215}/></section>}
      {lesson.session.stage === "teaching_video" && (lesson.video.url ? <VideoPlayer src={lesson.video.url} captionsSrc={captions} startAt={lesson.session.video_position_seconds} testOnly={lesson.video.test_only} onCheckpoint={checkpoint} onEnded={ended}/> : <div className={styles.error} role="alert">فيديو الدرس غير جاهز، ولن تتجاوز هِمّة هذه الخطوة تلقائيًا.</div>)}
      {(["additional_check", "support_practice", "support_check"] as string[]).includes(lesson.session.stage) && lesson.adaptation?.support && <section className={styles.supportIntro}><span className={styles.boundaryTag}>مساعدة قصيرة وليست خفضًا للمستوى</span><h2>{lesson.adaptation.support.title}</h2><p>{lesson.adaptation.message}</p></section>}
      {(["guided_practice", "independent_check", "additional_check", "support_practice", "support_check"] as string[]).includes(lesson.session.stage) && lesson.interaction && <InteractionPlayer key={lesson.interaction.question.question_id} sessionId={sessionId} interaction={lesson.interaction} onLessonChange={(updated) => setLesson(updated as LessonPayload)}/>}
      {lesson.session.stage === "waiting_review" && <section className={styles.practiceBoundary}><Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع" width={150} height={180}/><span className={styles.boundaryTag}>محفوظ بأمان</span><h2><CheckCircle2 size={25} aria-hidden="true"/> إجاباتك تنتظر مراجعة المشرف</h2><p>أكملت أسئلة الدرس، ولديك {lesson.summary?.pending_review ?? 1} إجابة كتابة أو قراءة معلّقة. لم تُحتسب صحيحة أو خاطئة، وسيحسمها المشرف.</p><StudentRetryTasks kind="lesson" sessionId={sessionId}/><Link href="/student/learning-v2" className={styles.back}>العودة إلى خريطة الدروس</Link></section>}
      {lesson.session.stage === "supervisor_hold" && <section className={styles.practiceBoundary}><Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع" width={150} height={180}/><span className={styles.boundaryTag}>تقدمك محفوظ</span><h2>سيختار المشرف أفضل مساعدة لك</h2><p>{lesson.adaptation?.message ?? "لن نخفض مستواك ولن نكرر المساعدة بلا نهاية."}</p><Link href="/student/learning-v2" className={styles.back}>العودة إلى خريطة الدروس</Link></section>}
      {lesson.session.stage === "outcome" && <section className={styles.practiceBoundary}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل" width={150} height={180}/><h2><CheckCircle2 size={25} aria-hidden="true"/> أكملت أسئلة الدرس</h2><p>{lesson.adaptation?.message ?? "أصبحت خطوتك التعليمية التالية جاهزة."}</p><Link href="/student/learning-v2" className={styles.back}>العودة إلى خريطة الدروس</Link></section>}
    </main>
  </div></div>;
}
