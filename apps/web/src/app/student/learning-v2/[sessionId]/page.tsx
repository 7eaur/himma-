"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  video: { asset_id: string; url: string | null; test_only: boolean; temporary?: boolean; state: string };
  practice: { count: number; first_question_id: string };
  independent_check: { count: number };
  session: { session_id: number; stage: Stage | "waiting_review"; status: string; video_position_seconds: number; video_duration_seconds: number | null; version: number };
  interaction?: InteractionPayload | null;
  summary?: { submitted: number; pending_review: number };
  adaptation?: { state: string; message: string; support?: { title: string; focus: string; mode: string } | null } | null;
}
const STAGES: Array<{ key: Stage; label: string }> = [{key:"intro",label:"المقدمة"},{key:"teaching_video",label:"الدرس"},{key:"guided_practice",label:"التدريب"},{key:"independent_check",label:"الاختبار"}];
const ACTIVE_LESSON_STAGES = new Set<string>(["intro", "teaching_video", "guided_practice", "independent_check", "additional_check", "support_practice", "support_check", "waiting_review", "supervisor_hold", "outcome"]);

/** POST /answers is not the authority for a different/stale learner session. */
function matchesCurrentLesson(value: unknown, current: LessonPayload, sessionId: number): value is LessonPayload {
  if (!value || typeof value !== "object") return false;
  const update = value as Partial<LessonPayload>;
  return update.lesson_id === current.lesson_id &&
    Number(update.session?.session_id) === sessionId &&
    ACTIVE_LESSON_STAGES.has(String(update.session?.stage)) &&
    Number.isSafeInteger(update.session?.version) &&
    Number(update.session?.version) >= current.session.version &&
    typeof update.title === "string" &&
    Boolean(update.intro) && Boolean(update.video);
}

function learnerLevelLabel(level: string): string {
  return level === "L1" ? "المستوى الأول"
    : level === "L2" ? "المستوى الثاني"
    : level === "L3" ? "المستوى الثالث" : "رحلة القراءة";
}

function eventKey(type: string) { return `${type}:${Date.now()}:${crypto.randomUUID()}`; }

export default function V2LessonPage() {
  const params = useParams<{ sessionId: string }>();
  // A client-side route transition must remount all lesson state, even when
  // both sessions reuse the same media URL. Old network callbacks then belong
  // only to the unmounted session and cannot render in the new one.
  return <V2LessonSessionPage key={params.sessionId} routeSessionId={params.sessionId} />;
}

function V2LessonSessionPage({ routeSessionId }: { routeSessionId: string }) {
  const router = useRouter();
  const [lesson, setLesson] = useState<LessonPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  // Reviewing instructional material never rewinds the academic session.
  const [reviewView, setReviewView] = useState<"intro" | "teaching_video" | null>(null);
  const completionKey = useRef<string | null>(null);
  const completionConfirmed = useRef(false);
  const active = useRef(false);
  const sessionId = Number(routeSessionId);
  const invalidSessionId = !Number.isInteger(sessionId) || sessionId < 1;

  useEffect(() => {
    active.current = true;
    return () => { active.current = false; };
  }, []);

  const loadLesson = useCallback(async () => {
    if (invalidSessionId || !active.current) return;
    return fetch(`/api/v2/lessons/sessions/${sessionId}/interaction`, { cache: "no-store" }).then(async (response) => {
      const data = await response.json().catch(() => null);
      // A response from a route that has already unmounted must not redirect
      // the new lesson to login or overwrite its error/loading state.
      if (!active.current) return;
      if (response.status === 401 || response.status === 403) { router.replace("/student/login"); return; }
      if (!response.ok) throw new Error(data?.detail || "تعذر استعادة الدرس");
      if (Number(data?.session?.session_id) !== sessionId) throw new Error("استجابة جلسة الدرس غير متطابقة");
      setError("");
      setLesson(data as LessonPayload);
    });
  }, [invalidSessionId, router, sessionId]);

  useEffect(() => {
    void loadLesson().catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر استعادة الدرس")).finally(() => setLoading(false));
  }, [loadLesson]);

  const sendEvent = useCallback(async (event_type: "intro_complete" | "video_progress" | "video_ended", position_seconds?: number, duration_seconds?: number, stableEventKey?: string) => {
    const response = await fetch(`/api/v2/lessons/sessions/${sessionId}/events`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ event_key:stableEventKey ?? eventKey(event_type), event_type, position_seconds, duration_seconds }), keepalive:event_type === "video_progress" });
    const data = await response.json().catch(() => null);
    if (!active.current) return;
    if (!response.ok) throw new Error(data?.detail || "تعذر حفظ تقدم الدرس");
    // Checkpoints persist the playback position, but must not replace the
    // rendered lesson. An older checkpoint response can arrive after
    // video_ended and otherwise regress the child from practice to video.
    // Re-rendering on each checkpoint can also seek the player backwards.
    if (event_type === "video_progress") return;
    if (event_type === "intro_complete") setReviewView(null);
    if (Number(data?.session?.session_id) !== sessionId) throw new Error("استجابة حفظ جلسة الدرس غير متطابقة");
    if (event_type === "video_ended") {
      completionConfirmed.current = true;
      setError("");
    }
    if (["guided_practice", "independent_check", "waiting_review", "outcome"].includes(data?.session?.stage)) await loadLesson();
    else setLesson(data);
  }, [loadLesson, sessionId]);

  const completeIntro = async () => { setSaving(true); setError(""); try { await sendEvent("intro_complete"); } catch (reason) { if (active.current) setError(reason instanceof Error ? reason.message : "تعذر فتح الفيديو"); } finally { if (active.current) setSaving(false); } };
  const handleLessonChange = (updated: unknown) => {
    if (!lesson || !matchesCurrentLesson(updated, lesson, sessionId)) {
      // A successful POST may already have committed the answer. Never repeat
      // it or render an answer/lesson from the wrong session; reconcile via GET.
      setLesson(null);
      setError("نتحقق من الإجابة المحفوظة، وسنستعيد موضعك.");
      setLoading(true);
      void loadLesson().catch((reason) => {
        if (active.current) setError(reason instanceof Error ? reason.message : "تعذر استعادة الدرس");
      }).finally(() => { if (active.current) setLoading(false); });
      return;
    }
    setError("");
    setLesson(updated);
  };
  const checkpoint = useCallback((position: number, duration: number) => { void sendEvent("video_progress", position, duration).catch(() => {
    // A delayed failed checkpoint must not put an error on the next stage.
    if (active.current && !completionConfirmed.current) setError("تعذر حفظ موضع الفيديو مؤقتًا. حاول الإيقاف ثم التشغيل.");
  }); }, [sendEvent]);
  const ended = useCallback(async (position: number, duration: number) => {
    if (lesson?.session.stage !== "teaching_video") return;
    // Retain the player after its acknowledgment so replay remains reachable.
    setReviewView("teaching_video");
    // A lost HTTP response after a committed event must be safe to retry.
    const key = completionKey.current ?? (completionKey.current = eventKey("video_ended"));
    await sendEvent("video_ended", position, duration, key);
  }, [lesson?.session.stage, sendEvent]);

  if (invalidSessionId) return <div className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error} role="alert">رابط جلسة الدرس غير صالح</div><Link href="/student/learning-v2" className={styles.back}><ArrowRight size={17}/> العودة إلى الدروس</Link></div></div>;
  if (loading) return <div className={styles.page} dir="rtl"><div className={styles.loading}><div><div className={styles.spinner} /><p>نستعيد موضعك المحفوظ...</p></div></div></div>;
  if (!lesson) return <div className={styles.page} dir="rtl"><div className={styles.container}><div className={styles.error} role="alert">{error || "تعذر فتح الدرس"}</div><Link href="/student/learning-v2" className={styles.back}><ArrowRight size={17}/> العودة إلى الدروس</Link></div></div>;
  const stageIndex = STAGES.findIndex((stage) => stage.key === lesson.session.stage);
  const actualIndex = stageIndex >= 0 ? stageIndex : lesson.session.stage === "waiting_review" ? 3 : STAGES.length;
  const activeIndex = reviewView ? STAGES.findIndex((stage) => stage.key === reviewView) : actualIndex;
  const supportStage = ["additional_check", "support_practice", "support_check"].includes(lesson.session.stage);
  const extraStageLabel = lesson.session.stage === "additional_check" ? "تحقق قصير"
    : lesson.session.stage === "support_practice" ? "تدريب التقوية"
    : lesson.session.stage === "support_check" ? "تحقق بعد التقوية"
    : lesson.session.stage === "waiting_review" ? "مراجعة القراءة"
    : lesson.session.stage === "supervisor_hold" ? "مساعدة المشرف" : "اكتمل الدرس";
  const progressStages = supportStage || lesson.session.stage === "supervisor_hold"
    ? [...STAGES, { key: lesson.session.stage as Stage, label: extraStageLabel }] : STAGES;
  const captions = lesson.video.test_only ? `${lesson.video.url}/captions` : undefined;
  const displayedStage = reviewView ?? lesson.session.stage;
  const reviewingVideo = displayedStage === "teaching_video" && lesson.session.stage !== "teaching_video";

  return <div className={styles.page} dir="rtl"><div className={styles.container}>
    <header className={styles.header}><Image src="/brand/logo-gradient.svg" alt="هِمّة" width={126} height={42} priority /><Link href="/student/learning-v2" className={styles.back}><ArrowRight size={17}/> الدروس</Link></header>
    <main className={styles.lessonCard}><span className={styles.eyebrow}>{learnerLevelLabel(lesson.level)} · درس القراءة</span><h1>{lesson.title}</h1>{lesson.objective && displayedStage !== "intro" && <p>{lesson.objective}</p>}
      <ol className={styles.lessonProgress} aria-label="مراحل الدرس">
        {progressStages.map((stage, index) => {
          const canReview = stage.key === "intro" || (stage.key === "teaching_video" && lesson.session.stage !== "intro");
          const canReturn = index === actualIndex;
          return <li key={stage.key} data-current={index === activeIndex} data-done={index < activeIndex}>
            <button type="button" disabled={!canReview && !canReturn} aria-current={index === activeIndex ? "step" : undefined}
              aria-label={stage.key === "intro" ? "مراجعة المقدمة" : stage.key === "teaching_video" ? "مشاهدة الدرس مرة أخرى" : stage.label}
              onClick={() => canReview ? setReviewView(stage.key as "intro" | "teaching_video") : setReviewView(null)}>
              <span className={styles.progressNode} aria-hidden="true">{index < activeIndex ? "✓" : index + 1}</span><span>{stage.label}</span>
            </button>
          </li>;
        })}
      </ol>
      {reviewView && <div className={styles.reviewActions}><button type="button" onClick={() => setReviewView(null)}>العودة إلى موضعي المحفوظ</button></div>}
      {error && <div className={styles.error} role="alert">{error}</div>}
      {displayedStage === "intro" && <section className={styles.intro} aria-label="تمهيد الدرس" data-testid="v2-lesson-intro">
      <div className={styles.introContent}>
        <span className={styles.eyebrow}>نستعد معًا</span>
        <h2>{lesson.intro.title}</h2>
        <p className={styles.introDescription}>{lesson.intro.text}</p>
        {lesson.objective && <div className={styles.learningGoal}><strong>ماذا سنتعلم؟</strong><p>{lesson.objective}</p></div>}
        <button type="button" className={styles.primary} disabled={saving} onClick={() => lesson.session.stage === "intro" ? void completeIntro() : setReviewView("teaching_video")}>{saving ? "جاري الحفظ..." : lesson.session.stage === "intro" ? lesson.intro.button : "شاهد الدرس"}<ArrowLeft size={18}/></button>
      </div>
      <div className={styles.introCharacter}><Image src="/characters/girl/welcome.png" alt="شخصية هِمّة ترحب بالطالب" width={180} height={215} priority /></div>
    </section>}
      {displayedStage === "teaching_video" && (lesson.video.url ? <><section className={styles.videoGuidance} data-testid="v2-video-guidance" aria-label="تعليمات مشاهدة الدرس">
        <Image src="/characters/girl/explain.png" alt="شخصية هِمّة تشرح التعليمات" width={84} height={100}/>
        <div><h2>شاهد شرح الدرس</h2><p>شاهد الفيديو، ويمكنك إيقافه أو إكماله من موضعك عند الحاجة. بعد المشاهدة ننتقل إلى التدريب.</p></div>
      </section><VideoPlayer key={`${sessionId}:${lesson.lesson_id}:${lesson.video.asset_id}`} src={lesson.video.url} captionsSrc={captions} startAt={reviewingVideo ? 0 : lesson.session.video_position_seconds} testOnly={lesson.video.test_only} temporary={lesson.video.temporary} onCheckpoint={reviewingVideo ? () => {} : checkpoint} onEnded={ended}/>{reviewingVideo && <div className={styles.continueRow}><p>مشاهدتك محفوظة. يمكنك إعادة الشرح أو متابعة رحلتك.</p><button type="button" className={styles.primary} onClick={() => setReviewView(null)}>{lesson.session.stage === "guided_practice" ? "انتقل إلى التدريب" : "متابعة من موضعي المحفوظ"}<ArrowLeft size={18}/></button></div>}</> : <div className={styles.error} role="alert">فيديو الدرس غير جاهز، ولن تتجاوز هِمّة هذه الخطوة تلقائيًا.</div>)}
      <div hidden={Boolean(reviewView)}>
      {supportStage && lesson.adaptation?.support && <section className={styles.supportIntro} data-testid="v2-support-path"><span className={styles.boundaryTag}>مساعدة قصيرة وليست خفضًا للمستوى</span><h2>{lesson.adaptation.support.title}</h2><p>{lesson.adaptation.message}</p><p>{lesson.session.stage === "additional_check" ? "سنبدأ بسؤالين قصيرين دون فيديو جديد؛ إذا احتجت مساعدة نضيف تدريبًا مناسبًا." : lesson.session.stage === "support_practice" ? "تدرّب خطوة خطوة دون فيديو جديد، ثم تحقق مما تعلمته." : "الآن أجب بنفسك لنرى ما تعلمته من المساعدة."}</p></section>}
      {(["guided_practice", "independent_check", "additional_check", "support_practice", "support_check"] as string[]).includes(lesson.session.stage) && lesson.interaction && <InteractionPlayer key={lesson.interaction.question.question_id} sessionId={sessionId} interaction={lesson.interaction} suspended={Boolean(reviewView)} onLessonChange={handleLessonChange}/>}
      {lesson.session.stage === "waiting_review" && <section className={styles.practiceBoundary}><Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع" width={150} height={180}/><span className={styles.boundaryTag}>محفوظ بأمان</span><h2><CheckCircle2 size={25} aria-hidden="true"/> إجاباتك تنتظر مراجعة المشرف</h2><p>أكملت أسئلة الدرس، ولديك {lesson.summary?.pending_review ?? 1} إجابة قراءة مسجلة تنتظر المراجعة. لم تُحتسب صحيحة أو خاطئة، وسيحسمها المشرف.</p><StudentRetryTasks kind="lesson" sessionId={sessionId}/><Link href="/student/learning-v2" className={styles.back}>العودة إلى خريطة الدروس</Link></section>}
      {lesson.session.stage === "supervisor_hold" && <section className={styles.practiceBoundary}><Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع" width={150} height={180}/><span className={styles.boundaryTag}>تقدمك محفوظ</span><h2>سيختار المشرف أفضل مساعدة لك</h2><p>{lesson.adaptation?.message ?? "لن نخفض مستواك ولن نكرر المساعدة بلا نهاية."}</p><Link href="/student/learning-v2" className={styles.back}>العودة إلى خريطة الدروس</Link></section>}
      {lesson.session.stage === "outcome" && <section className={styles.practiceBoundary}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل" width={150} height={180}/><h2><CheckCircle2 size={25} aria-hidden="true"/> أكملت أسئلة الدرس</h2><p>{lesson.adaptation?.message ?? "أصبحت خطوتك التعليمية التالية جاهزة."}</p><Link href="/student/learning-v2" className={styles.back}>العودة إلى خريطة الدروس</Link></section>}
      </div>
    </main>
  </div></div>;
}
