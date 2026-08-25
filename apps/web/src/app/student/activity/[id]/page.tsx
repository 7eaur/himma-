"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, Mic, RotateCcw, Square } from "lucide-react";
import styles from "../activity.module.css";

type Interaction =
  | "choose_one"
  | "listen_choose_one"
  | "choose_image"
  | "listen_choose_image"
  | "choose_many"
  | "listen_choose_many"
  | "sequence"
  | "memory_sequence"
  | "path_sequence"
  | "build_word"
  | "read_aloud"
  | "timed_read_aloud";

interface ActivityOption {
  id: number;
  text: string;
  order_index: number;
}

interface ActivityAsset {
  asset_id: string;
  asset_type: "audio" | "image" | string;
  usage?: string | null;
  url: string;
}

interface MediaGap {
  asset_type: string;
  usage: string;
  semantic_text: string;
  status: string;
  reason?: string;
}

interface ActivityPayload {
  session_id: number;
  item: {
    id: number;
    stable_key: string;
    canonical_id: string;
    title: string;
    level_id: number;
    order_index: number;
    interaction_type: Interaction;
    source_method?: string | null;
  };
  step: {
    id: number;
    order_index: number;
    prompt_text: string;
    expected_reading_text?: string | null;
    options: ActivityOption[];
    assets: ActivityAsset[];
    media_gaps: MediaGap[];
  };
  attempts_used: number;
  max_attempts: number;
  retry: boolean;
  hint_available: boolean;
}

interface LearningProgress {
  session_id: number;
  status: "in_progress" | "completed";
  level_id: number;
  completed_items: number;
  total_items: number;
  elapsed_seconds: number;
}

interface SubmitResult {
  is_correct: boolean;
  attempts_used: number;
  step_complete: boolean;
  show_hint: boolean;
  activity_complete: boolean;
  learning_complete: boolean;
}

const LEVEL_NAMES: Record<number, string> = {
  1: "الاستعداد للقراءة",
  2: "بناء الكلمة",
  3: "الطلاقة والفهم",
};

const SINGLE_INTERACTIONS = new Set<Interaction>([
  "choose_one",
  "listen_choose_one",
  "choose_image",
  "listen_choose_image",
]);
const MULTI_INTERACTIONS = new Set<Interaction>(["choose_many", "listen_choose_many"]);
const ORDER_INTERACTIONS = new Set<Interaction>([
  "sequence",
  "memory_sequence",
  "path_sequence",
  "build_word",
]);
const AUDIO_INTERACTIONS = new Set<Interaction>(["read_aloud", "timed_read_aloud"]);

export default function StudentActivityPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = String(params.id);
  const [activity, setActivity] = useState<ActivityPayload | null>(null);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const startedAtRef = useRef(Date.now());
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const options = useMemo(
    () => [...(activity?.step.options ?? [])].sort((a, b) => a.order_index - b.order_index),
    [activity],
  );
  const audioAssets = activity?.step.assets.filter((asset) => asset.asset_type === "audio") ?? [];
  const imageAssets = activity?.step.assets.filter((asset) => asset.asset_type === "image") ?? [];
  const interaction = activity?.item.interaction_type;
  const percent = progress
    ? Math.min(100, Math.round((progress.completed_items / Math.max(1, progress.total_items)) * 100))
    : 0;

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/activities/session/${sessionId}/progress`);
    if (!response.ok) return;
    setProgress(await response.json());
  }, [sessionId]);

  const fetchNext = useCallback(async () => {
    setError("");
    try {
      const response = await fetch(`/api/activities/session/${sessionId}/next`);
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تحميل النشاط");
      if (!data) {
        setDone(true);
        setActivity(null);
        await fetchProgress();
        return;
      }
      setActivity(data);
      setSelected([]);
      setAudioBlob(null);
      setFeedback(null);
      setRecordingSeconds(0);
      startedAtRef.current = Date.now();
      await fetchProgress();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل النشاط");
    }
  }, [fetchProgress, sessionId]);

  useEffect(() => {
    void fetchNext();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    };
  }, [fetchNext]);

  const makeIdempotencyKey = (kind: "answer" | "upload") => {
    const stepId = activity?.step.id ?? 0;
    const attempt = (activity?.attempts_used ?? 0) + 1;
    const storageKey = `himma:activity:${sessionId}:${stepId}:${attempt}:${kind}`;
    const existing = window.sessionStorage.getItem(storageKey);
    if (existing) return existing;
    const created = crypto.randomUUID();
    window.sessionStorage.setItem(storageKey, created);
    return created;
  };

  const clearIdempotency = () => {
    if (!activity) return;
    const attempt = activity.attempts_used + 1;
    for (const kind of ["answer", "upload"] as const) {
      window.sessionStorage.removeItem(`himma:activity:${sessionId}:${activity.step.id}:${attempt}:${kind}`);
    }
  };

  const submitStructured = async (mediaGapSkip = false) => {
    if (!activity || !interaction) return;
    setSubmitting(true);
    setError("");
    const elapsedSeconds = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
    try {
      const response = await fetch(
        `/api/activities/session/${sessionId}/attempt/${activity.item.id}/submit`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": makeIdempotencyKey("answer"),
          },
          body: JSON.stringify({
            step_id: activity.step.id,
            selected_option_ids: selected,
            hint_used: activity.retry,
            elapsed_seconds: elapsedSeconds,
            declared_media_gap_skip: mediaGapSkip,
          }),
        },
      );
      const result: SubmitResult & { detail?: string } = await response.json().catch(() => ({} as SubmitResult));
      if (!response.ok) throw new Error(result.detail || "تعذر حفظ الإجابة");
      clearIdempotency();
      if (result.learning_complete) {
        setDone(true);
        setFeedback({ ok: true, text: "أحسنت، أكملت أنشطة مستواك." });
        await fetchProgress();
        return;
      }
      if (result.is_correct || result.step_complete) {
        setFeedback({
          ok: result.is_correct,
          text: result.is_correct ? "أحسنت، تقدمت خطوة." : "أكملت المحاولة. ننتقل إلى الخطوة التالية.",
        });
        window.setTimeout(() => void fetchNext(), 520);
      } else {
        setFeedback({ ok: false, text: "حاول مرة أخرى. اقرأ أو استمع بهدوء." });
        await fetchNext();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ الإجابة");
    } finally {
      setSubmitting(false);
    }
  };

  const startRecording = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const preferred = "audio/webm;codecs=opus";
      const recorder = MediaRecorder.isTypeSupported(preferred)
        ? new MediaRecorder(stream, { mimeType: preferred })
        : new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        setAudioBlob(new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" }));
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      recorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    } catch {
      setError("لم نتمكن من تشغيل الميكروفون. اسمح بالوصول ثم حاول مرة أخرى.");
    }
  };

  const stopRecording = () => {
    if (!recorderRef.current || recorderRef.current.state !== "recording") return;
    recorderRef.current.stop();
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const uploadReading = async () => {
    if (!activity || !audioBlob) return;
    setSubmitting(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", audioBlob, "activity-reading.webm");
      const upload = await fetch(`/api/assessment/session/${sessionId}/upload-audio`, {
        method: "POST",
        headers: { "Idempotency-Key": makeIdempotencyKey("upload") },
        body: form,
      });
      const uploaded = await upload.json().catch(() => null);
      if (!upload.ok) throw new Error(uploaded?.detail || "فشل رفع التسجيل");

      const elapsedSeconds = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const submit = await fetch(`/api/assessment/session/${sessionId}/attempt/${activity.item.id}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": makeIdempotencyKey("answer"),
        },
        body: JSON.stringify({
          step_id: activity.step.id,
          selected_option_id: null,
          audio_storage_key: uploaded.audio_storage_key,
          audio_file_size: uploaded.audio_file_size,
          audio_mime_type: uploaded.audio_mime_type,
          audio_duration_seconds: recordingSeconds,
          elapsed_seconds: elapsedSeconds,
        }),
      });
      const result = await submit.json().catch(() => null);
      if (!submit.ok) throw new Error(result?.detail || "تعذر حفظ القراءة");
      clearIdempotency();
      setFeedback({ ok: true, text: "تم حفظ قراءتك. أحسنت المتابعة." });
      window.setTimeout(() => void fetchNext(), 520);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ القراءة");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleOption = (optionId: number) => {
    if (!interaction) return;
    setFeedback(null);
    if (SINGLE_INTERACTIONS.has(interaction)) {
      setSelected([optionId]);
      return;
    }
    if (MULTI_INTERACTIONS.has(interaction)) {
      setSelected((current) => current.includes(optionId)
        ? current.filter((id) => id !== optionId)
        : [...current, optionId]);
      return;
    }
    if (ORDER_INTERACTIONS.has(interaction)) {
      setSelected((current) => current.includes(optionId) ? current : [...current, optionId]);
    }
  };

  const readyToSubmit = Boolean(
    interaction && (
      (SINGLE_INTERACTIONS.has(interaction) && selected.length === 1) ||
      (MULTI_INTERACTIONS.has(interaction) && selected.length >= 2) ||
      (ORDER_INTERACTIONS.has(interaction) && selected.length === options.length)
    ),
  );

  if (done) {
    return (
      <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="done">
        <main className={styles.main}>
          <section className={`${styles.card} ${styles.done}`}>
            <CheckCircle2 size={50} color="#51B985" aria-hidden="true" />
            <h1>أحسنت، أكملت أنشطة مستواك</h1>
            <p>أنجزت اليوم تقدمًا جميلًا. سيظهر الاختبار البعدي عندما تفتحه الباحثة.</p>
            <Image className={styles.character} src="/characters/boy/success.png" alt="شخصية هِمّة سعيدة" width={150} height={190} />
            <button className={styles.primary} onClick={() => router.push("/student")}>العودة إلى مساري</button>
          </section>
        </main>
      </div>
    );
  }

  if (error && !activity) {
    return (
      <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="error">
        <main className={styles.main}>
          <section className={`${styles.card} ${styles.error}`}>
            <h1>تعذر فتح النشاط</h1>
            <p className={styles.errorMessage}>{error}</p>
            <button className={styles.primary} onClick={() => void fetchNext()}>حاول مرة أخرى</button>
          </section>
        </main>
      </div>
    );
  }

  if (!activity || !interaction) {
    return (
      <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="loading">
        <main className={styles.main}>
          <section className={`${styles.card} ${styles.loading}`}>
            <div className="spinner w-12 h-12 border-4" />
            <p>جاري تجهيز النشاط...</p>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="active">
      <header className={styles.header}>
        <button className={styles.back} onClick={() => router.push("/student")} aria-label="العودة إلى مسار الطالب">
          <ArrowRight size={18} aria-hidden="true" />
          <span>رجوع</span>
        </button>
        <div className={styles.progress} aria-label={`أكملت ${progress?.completed_items ?? 0} من ${progress?.total_items ?? 10} أنشطة`}>
          <span style={{ width: `${percent}%` }} />
        </div>
        <span className={styles.counter} data-testid="activity-progress">
          {progress?.completed_items ?? 0}/{progress?.total_items ?? 10}
        </span>
      </header>

      <main className={styles.main}>
        <section className={styles.card}>
          <div className={styles.activityMeta}>
            <span className={styles.levelPill}>المستوى: {LEVEL_NAMES[activity.item.level_id]}</span>
            <span className={styles.roundPill}>النشاط {activity.item.order_index} · الجولة {activity.step.order_index}</span>
          </div>

          <h1 className={styles.title}>{activity.item.title}</h1>
          {activity.item.source_method && <p className={styles.method}>{activity.item.source_method}</p>}

          <div className={styles.prompt}>{activity.step.prompt_text}</div>
          {activity.step.expected_reading_text && (
            <div className={styles.readingText}>{activity.step.expected_reading_text}</div>
          )}

          {audioAssets.map((asset) => (
            <div className={styles.audioBox} key={asset.asset_id}>
              <audio controls preload="metadata" src={asset.url}>المتصفح لا يدعم تشغيل الصوت.</audio>
            </div>
          ))}

          {imageAssets.length > 0 && (
            <div className={styles.mediaGrid}>
              {imageAssets.map((asset) => (
                <div className={styles.imageBox} key={asset.asset_id}>
                  <Image src={asset.url} alt="صورة تعليمية" width={240} height={180} unoptimized />
                </div>
              ))}
            </div>
          )}

          {activity.step.media_gaps.length > 0 && (
            <div className={styles.gapNotice}>
              <p>هذا الجزء يحتاج ملفًا صوتيًا معتمدًا غير متوفر حاليًا. لن يُحسب ذلك عليك.</p>
              <button className={styles.secondary} disabled={submitting} onClick={() => void submitStructured(true)}>
                متابعة دون احتساب هذه الجولة
              </button>
            </div>
          )}

          {!AUDIO_INTERACTIONS.has(interaction) && activity.step.media_gaps.length === 0 && (
            <>
              {ORDER_INTERACTIONS.has(interaction) && (
                <div className={styles.sequenceArea}>
                  <div className={styles.sequenceChosen} aria-label="ترتيبك الحالي">
                    {selected.length === 0 && <span>اضغط على العناصر بالترتيب</span>}
                    {selected.map((id, index) => {
                      const option = options.find((candidate) => candidate.id === id);
                      return <span className={styles.sequenceChip} key={id}>{index + 1}. {option?.text}</span>;
                    })}
                  </div>
                </div>
              )}

              <div className={styles.options}>
                {options.map((option) => {
                  const isSelected = selected.includes(option.id);
                  return (
                    <button
                      key={option.id}
                      className={`${styles.option} ${isSelected ? styles.optionSelected : ""}`}
                      onClick={() => toggleOption(option.id)}
                      disabled={submitting || (ORDER_INTERACTIONS.has(interaction) && isSelected)}
                      aria-pressed={isSelected}
                    >
                      {option.text}
                    </button>
                  );
                })}
              </div>

              <div className={styles.actions}>
                {ORDER_INTERACTIONS.has(interaction) && selected.length > 0 && (
                  <button className={styles.secondary} disabled={submitting} onClick={() => setSelected([])}>
                    <RotateCcw size={17} aria-hidden="true" /> إعادة الترتيب
                  </button>
                )}
                <button className={styles.primary} disabled={submitting || !readyToSubmit} onClick={() => void submitStructured(false)}>
                  {submitting ? "جاري الحفظ..." : "تحقق وتابع"}
                </button>
              </div>
            </>
          )}

          {AUDIO_INTERACTIONS.has(interaction) && activity.step.media_gaps.length === 0 && (
            <div className={styles.actions}>
              {!isRecording && !audioBlob && (
                <button className={styles.recordButton} onClick={() => void startRecording()}>
                  <Mic size={19} aria-hidden="true" /> ابدأ القراءة
                </button>
              )}
              {isRecording && (
                <button className={`${styles.recordButton} ${styles.recording}`} onClick={stopRecording}>
                  <Square size={17} aria-hidden="true" /> إيقاف التسجيل · {recordingSeconds}ث
                </button>
              )}
              {!isRecording && audioBlob && (
                <>
                  <button className={styles.secondary} onClick={() => setAudioBlob(null)}>إعادة التسجيل</button>
                  <button className={styles.primary} disabled={submitting} onClick={() => void uploadReading()}>
                    {submitting ? "جاري الحفظ..." : "حفظ القراءة والمتابعة"}
                  </button>
                </>
              )}
            </div>
          )}

          {feedback && (
            <p className={`${styles.feedback} ${feedback.ok ? styles.success : styles.retry}`}>{feedback.text}</p>
          )}
          {error && <p className={`${styles.feedback} ${styles.retry}`}>{error}</p>}
          {activity.retry && !feedback && (
            <p className={`${styles.feedback} ${styles.retry}`}>حاول مرة أخرى. لديك محاولة ثانية، ويمكنك الاستفادة من التعليمة.</p>
          )}
        </section>
      </main>
    </div>
  );
}
