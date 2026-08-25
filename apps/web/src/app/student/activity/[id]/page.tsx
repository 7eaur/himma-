"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { ArrowRight, Check, CheckCircle2, Headphones, Mic, MicOff, RotateCcw, Volume2 } from "lucide-react";
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
  semantic_text?: string | null;
  url: string;
  option_id?: number | null;
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
    kind?: string;
    assets?: ActivityAsset[];
  };
  step: {
    id: number;
    order_index: number;
    prompt_text: string;
    instruction_text?: string | null;
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
const LISTEN_INTERACTIONS = new Set<Interaction>([
  "listen_choose_one",
  "listen_choose_image",
  "listen_choose_many",
]);

function stableOptionOrder(values: ActivityOption[]) {
  return [...values].sort((a, b) => ((a.id * 19) % 101) - ((b.id * 19) % 101));
}

function shortActivityTitle(title: string) {
  return title.includes(":") ? title.split(":").slice(1).join(":").trim() : title;
}

function cleanPrompt(value: string, interaction: Interaction) {
  if (LISTEN_INTERACTIONS.has(interaction) || AUDIO_INTERACTIONS.has(interaction) || ORDER_INTERACTIONS.has(interaction)) return "";
  let prompt = value.replace(/^التعليمات:\s*/u, "");
  prompt = prompt.split(/الخيارات:|الصور:/u)[0].trim();
  return prompt;
}

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
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const startedAtRef = useRef(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playbackRef = useRef<HTMLAudioElement | null>(null);

  const interaction = activity?.item.interaction_type;
  const options = useMemo(() => stableOptionOrder(activity?.step.options ?? []), [activity]);
  const audioAssets = useMemo(() => activity?.step.assets.filter((asset) => asset.asset_type === "audio") ?? [], [activity]);
  const imageAssets = useMemo(() => activity?.step.assets.filter((asset) => asset.asset_type === "image") ?? [], [activity]);
  const contextAssets = useMemo(() => activity?.item.assets?.filter((asset) => asset.asset_type === "image") ?? [], [activity]);
  const percent = progress
    ? Math.min(100, Math.round((progress.completed_items / Math.max(1, progress.total_items)) * 100))
    : 0;

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/activities/session/${sessionId}/progress`, { cache: "no-store" });
    if (response.ok) setProgress(await response.json());
  }, [sessionId]);

  const resetQuestionState = () => {
    setSelected([]);
    setAudioBlob(null);
    setAudioUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
    setRecordingSeconds(0);
    setFeedback(null);
  };

  const fetchNext = useCallback(async () => {
    setError("");
    try {
      const response = await fetch(`/api/activities/session/${sessionId}/next`, { cache: "no-store" });
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
      setAudioUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
      setFeedback(null);
      setRecordingSeconds(0);
      startedAtRef.current = Date.now();
      await fetchProgress();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل النشاط");
    }
  }, [fetchProgress, sessionId]);

  useEffect(() => {
    const kickoff = window.setTimeout(() => void fetchNext(), 0);
    return () => {
      window.clearTimeout(kickoff);
      if (timerRef.current) clearInterval(timerRef.current);
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      playbackRef.current?.pause();
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

  const playPrompt = async () => {
    if (!audioAssets.length || isListening) return;
    setIsListening(true);
    setError("");
    try {
      for (const asset of audioAssets) {
        await new Promise<void>((resolve, reject) => {
          const audio = new Audio(asset.url);
          playbackRef.current = audio;
          audio.onended = () => resolve();
          audio.onerror = () => reject(new Error("تعذر تشغيل الصوت"));
          void audio.play().catch(reject);
        });
      }
    } catch {
      setError("تعذر تشغيل الصوت. تحقق من مستوى الصوت في الجهاز ثم حاول مرة أخرى.");
    } finally {
      setIsListening(false);
      playbackRef.current = null;
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
          text: result.is_correct ? "أحسنت! إجابة صحيحة." : "أكملت المحاولة، ننتقل للخطوة التالية.",
        });
        window.setTimeout(() => void fetchNext(), 620);
      } else {
        setFeedback({ ok: false, text: "قريب جدًا. جرّب مرة أخرى بهدوء." });
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
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl((current) => {
          if (current) URL.revokeObjectURL(current);
          return URL.createObjectURL(blob);
        });
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      recorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    } catch {
      setError("لم نتمكن من تشغيل الميكروفون. اسمح للمتصفح باستخدامه ثم حاول مرة أخرى.");
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
      if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");

      const elapsedSeconds = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const submit = await fetch(`/api/assessment/session/${sessionId}/attempt/${activity.item.id}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": makeIdempotencyKey("answer"),
        },
        body: JSON.stringify({
          step_id: activity.step.id,
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
      setFeedback({ ok: true, text: "تم حفظ قراءتك. أحسنت!" });
      window.setTimeout(() => void fetchNext(), 620);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ القراءة");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleOption = (optionId: number) => {
    if (!interaction || submitting) return;
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
      (SINGLE_INTERACTIONS.has(interaction) && selected.length === 1)
      || (MULTI_INTERACTIONS.has(interaction) && selected.length >= 2)
      || (ORDER_INTERACTIONS.has(interaction) && selected.length === options.length)
    ),
  );

  if (done) {
    return (
      <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="done">
        <main className={styles.main}>
          <section className={`${styles.card} ${styles.done}`}>
            <CheckCircle2 size={50} color="#51B985" aria-hidden="true" />
            <h1>أحسنت، أكملت أنشطة مستواك</h1>
            <p>أنجزت تقدمًا جميلًا. سيظهر الاختبار البعدي عندما يفتحه المشرف.</p>
            <Image className={styles.character} src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل بالإنجاز" width={180} height={220} />
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
            <Image src="/brand/logo-navy.svg" alt="هِمّة" width={112} height={38} />
            <div className="spinner w-12 h-12 border-4" />
            <p>جاري تجهيز النشاط...</p>
          </section>
        </main>
      </div>
    );
  }

  const hasMediaGap = activity.step.media_gaps.length > 0;
  const imageChoice = interaction === "choose_image" || interaction === "listen_choose_image";
  const multiImageChoice = interaction === "choose_many" || interaction === "listen_choose_many";
  const sequenceWithImages = ORDER_INTERACTIONS.has(interaction) && imageAssets.some((asset) => asset.option_id);
  const displayPrompt = cleanPrompt(activity.step.prompt_text, interaction);
  const imageOptions = imageAssets.filter((asset) => asset.option_id);

  return (
    <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="active">
      <header className={styles.header}>
        <button className={styles.back} onClick={() => router.push("/student")} aria-label="العودة إلى مسار الطالب">
          <ArrowRight size={18} aria-hidden="true" /><span>رجوع</span>
        </button>
        <div className={styles.progress} aria-label={`أكملت ${progress?.completed_items ?? 0} من ${progress?.total_items ?? 10} أنشطة`}>
          <span style={{ width: `${percent}%` }} />
        </div>
        <span className={styles.counter} data-testid="activity-progress">
          {progress?.completed_items ?? 0} من {progress?.total_items ?? 10}
        </span>
      </header>

      <main className={styles.main}>
        <section className={styles.card}>
          <div className={styles.activityMeta}>
            <span className={styles.levelPill}>{LEVEL_NAMES[activity.item.level_id]}</span>
            <span className={styles.roundPill}>النشاط {activity.item.order_index} · الجولة {activity.step.order_index}</span>
          </div>

          <span className={styles.taskBadge}>
            {LISTEN_INTERACTIONS.has(interaction) ? <Headphones size={15} /> : AUDIO_INTERACTIONS.has(interaction) ? <Mic size={15} /> : <Check size={15} />}
            مهمة واحدة في كل مرة
          </span>
          <h1 className={styles.title}>{activity.step.instruction_text || shortActivityTitle(activity.item.title)}</h1>
          <p className={styles.method}>{shortActivityTitle(activity.item.title)}</p>
          {displayPrompt && <div className={styles.prompt}>{displayPrompt}</div>}

          {contextAssets[0] && (
            <div className={styles.contextImage}>
              <Image src={contextAssets[0].url} alt={contextAssets[0].semantic_text || "صورة توضيحية للنشاط"} width={460} height={260} unoptimized />
            </div>
          )}

          {LISTEN_INTERACTIONS.has(interaction) && (
            <button className={`${styles.listenButton} ${isListening ? styles.listening : ""}`} onClick={() => void playPrompt()} disabled={isListening || !audioAssets.length} data-testid="activity-listen">
              <Volume2 size={27} /><span>استمع</span>
            </button>
          )}

          {hasMediaGap && (
            <div className={styles.gapNotice}>
              <p>هذا الملف الصوتي غير متوفر ضمن الملفات المعتمدة حاليًا، لذلك لن تُحسب هذه الجولة عليك.</p>
              <button className={styles.secondary} disabled={submitting} onClick={() => void submitStructured(true)}>متابعة دون احتساب الجولة</button>
            </div>
          )}

          {!hasMediaGap && (imageChoice || (multiImageChoice && imageOptions.length > 0)) && (
            <div className={styles.imageOptions} data-testid="activity-image-options">
              {imageOptions.map((asset) => {
                const optionId = Number(asset.option_id);
                const isSelected = selected.includes(optionId);
                return (
                  <button key={`${asset.asset_id}-${optionId}`} className={`${styles.imageOption} ${isSelected ? styles.imageOptionSelected : ""}`} onClick={() => toggleOption(optionId)} aria-pressed={isSelected}>
                    {isSelected && <span className={styles.selectedMark}><Check size={16} /></span>}
                    <Image src={asset.url} alt={asset.semantic_text || "خيار مصور"} width={220} height={150} unoptimized />
                    <span>{asset.semantic_text || activity.step.options.find((option) => option.id === optionId)?.text}</span>
                  </button>
                );
              })}
            </div>
          )}

          {!hasMediaGap && ORDER_INTERACTIONS.has(interaction) && (
            <>
              <div className={styles.sequenceChosen} aria-label="ترتيبك الحالي">
                {selected.length === 0 && <span className={styles.sequenceHint}>{interaction === "build_word" ? "اضغط الحروف بالترتيب لتكوين الكلمة" : "اضغط العناصر بالترتيب الصحيح"}</span>}
                {selected.map((id, index) => {
                  const option = activity.step.options.find((candidate) => candidate.id === id);
                  return <span className={styles.sequenceChip} key={`${id}-${index}`}><b>{index + 1}</b>{option?.text}</span>;
                })}
              </div>

              {interaction === "build_word" && imageAssets[0] && (
                <div className={styles.contextImage}>
                  <Image src={imageAssets[0].url} alt={imageAssets[0].semantic_text || "صورة الكلمة"} width={360} height={220} unoptimized />
                </div>
              )}

              {sequenceWithImages && interaction !== "build_word" ? (
                <div className={styles.imageOptions}>
                  {imageOptions.filter((asset) => !selected.includes(Number(asset.option_id))).map((asset) => (
                    <button key={asset.asset_id} className={styles.imageOption} onClick={() => toggleOption(Number(asset.option_id))}>
                      <Image src={asset.url} alt={asset.semantic_text || "عنصر ترتيب"} width={220} height={150} unoptimized />
                      <span>{asset.semantic_text}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <div className={styles.options}>
                  {options.filter((option) => !selected.includes(option.id)).map((option) => (
                    <button key={option.id} className={styles.option} onClick={() => toggleOption(option.id)}>{option.text}</button>
                  ))}
                </div>
              )}
            </>
          )}

          {!hasMediaGap && !AUDIO_INTERACTIONS.has(interaction) && !ORDER_INTERACTIONS.has(interaction) && !(imageChoice || (multiImageChoice && imageOptions.length > 0)) && (
            <div className={styles.options}>
              {options.map((option) => {
                const isSelected = selected.includes(option.id);
                return (
                  <button key={option.id} className={`${styles.option} ${isSelected ? styles.optionSelected : ""}`} onClick={() => toggleOption(option.id)} aria-pressed={isSelected}>
                    {option.text}
                  </button>
                );
              })}
            </div>
          )}

          {!hasMediaGap && AUDIO_INTERACTIONS.has(interaction) && (
            <>
              <div className={`${styles.readingText} ${(activity.step.expected_reading_text?.length || 0) > 55 ? styles.readingTextLong : ""}`} data-testid="activity-reading-text">
                {activity.step.expected_reading_text || "اقرأ النص الظاهر بصوت واضح"}
              </div>
              <div className={styles.recordPanel}>
                {!audioBlob ? (
                  <>
                    <button className={`${styles.recordCircle} ${isRecording ? styles.recording : ""}`} onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"}>
                      {isRecording ? <MicOff size={30} /> : <Mic size={30} />}
                    </button>
                    <strong>{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</strong>
                    {isRecording && <span className={styles.timer}>{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</span>}
                  </>
                ) : (
                  <>
                    {audioUrl && <audio className={styles.audioPreview} src={audioUrl} controls />}
                    <p>استمع إلى تسجيلك، ثم أرسله أو أعد المحاولة.</p>
                    <div className={styles.actions}>
                      <button className={styles.secondary} onClick={() => { resetQuestionState(); startedAtRef.current = Date.now(); }}><RotateCcw size={17} /> إعادة التسجيل</button>
                      <button className={styles.primary} disabled={submitting} onClick={() => void uploadReading()}>{submitting ? "جاري الحفظ..." : "إرسال التسجيل"}</button>
                    </div>
                  </>
                )}
              </div>
            </>
          )}

          {feedback && <p className={`${styles.feedback} ${feedback.ok ? styles.success : styles.retry}`}>{feedback.text}</p>}
          {error && <p className={`${styles.feedback} ${styles.errorMessage}`}>{error}</p>}
          {activity.retry && !feedback && !error && <p className={`${styles.feedback} ${styles.retry}`}>حاول مرة أخرى. لديك محاولة ثانية، ويمكنك الاستفادة من التعليمة.</p>}

          {!hasMediaGap && !AUDIO_INTERACTIONS.has(interaction) && (
            <div className={styles.actions}>
              {ORDER_INTERACTIONS.has(interaction) && selected.length > 0 && <button className={styles.secondary} disabled={submitting} onClick={() => setSelected([])}><RotateCcw size={17} /> إعادة الترتيب</button>}
              <button className={styles.primary} disabled={submitting || !readyToSubmit} onClick={() => void submitStructured(false)}>{submitting ? "جاري الحفظ..." : "تأكيد والمتابعة"}</button>
            </div>
          )}

          <div className={styles.helperRow}>
            <Image src={activity.retry ? "/characters/girl/encourage.png" : "/characters/girl/explain.png"} alt="شخصية هِمّة المساعدة" width={95} height={120} />
            <p>{activity.retry ? "لا بأس، ركّز في الصوت أو الصورة وجرب مرة ثانية." : "خذ وقتك. يمكنك الاستماع مرة أخرى قبل الإجابة عندما يظهر زر الصوت."}</p>
          </div>
        </section>
      </main>
    </div>
  );
}
