"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { Check, Info, LogOut, Mic, MicOff, Pause, Play, RotateCcw, Target, Volume2 } from "lucide-react";
import { useAudioQueue } from "@/hooks/useAudioQueue";
import styles from "../../session/[id]/session.module.css";

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

type Asset = {
  asset_id: string;
  asset_type: string;
  usage?: string | null;
  semantic_text?: string | null;
  url: string;
  option_id?: number | null;
};
type Option = { id: number; text: string; order_index: number };
type ContextIntro = {
  kind?: string;
  title?: string;
  instruction?: string;
  text?: string;
  audio_asset_id?: string;
  image_asset_id?: string;
  asset?: Asset;
};
type ViewPayload = {
  version?: string;
  session_id: number;
  navigation_state?: "awaiting_audio_review";
  pending_audio_reviews?: number;
  level_id?: number;
  item_id?: number;
  stable_key?: string;
  kind?: string;
  interaction_type?: Interaction;
  round?: {
    round_number: number;
    round_total: number;
    skill: string;
    encouragement: string;
    hint: string;
    question_text: string;
    instruction_text: string;
    stimulus_text?: string;
  };
  retry?: boolean;
  attempts_used?: number;
  audio_review_status?: string | null;
  awaiting_audio_review?: boolean;
  context_intro?: ContextIntro | null;
  layout_hint?: string | null;
  step?: {
    id: number;
    expected_reading_text?: string | null;
    required_selection_count: number;
    options: Option[];
    assets: Asset[];
    media_gaps: Array<{ status?: string; semantic_text?: string }>;
  };
  assets?: Asset[];
};
type AdvancePayload = { navigation_state?: string; pending_audio_reviews?: number; detail?: string } | null;
type Progress = {
  completed_items: number;
  total_items: number;
  level_id: number;
  status: string;
  pending_audio_reviews?: number;
};
type SubmitResult = {
  is_correct: boolean | null;
  step_complete: boolean;
  activity_complete: boolean;
  learning_complete: boolean;
  awaiting_review?: boolean;
  navigation_complete?: boolean;
  detail?: string;
};

const SINGLE = new Set<Interaction>(["choose_one", "listen_choose_one", "choose_image", "listen_choose_image"]);
const MULTI = new Set<Interaction>(["choose_many", "listen_choose_many"]);
const ORDER = new Set<Interaction>(["sequence", "memory_sequence", "path_sequence", "build_word"]);
const LISTEN = new Set<Interaction>(["listen_choose_one", "listen_choose_image", "listen_choose_many"]);
const READ = new Set<Interaction>(["read_aloud", "timed_read_aloud"]);
const LEVEL_NAMES: Record<number, string> = { 1: "الاستعداد للقراءة", 2: "بناء الكلمة", 3: "الطلاقة والفهم" };

function completionCopy(levelId: number) {
  if (levelId === 1) return { title: "أحسنت، أكملت الاستعداد للقراءة", text: "خطوتك التالية هي بناء الكلمة. استمر بنفس التركيز.", cta: "الانتقال إلى خطوتي التالية" };
  if (levelId === 2) return { title: "أحسنت، أكملت بناء الكلمة", text: "خطوتك التالية هي الطلاقة والفهم. استمر، أنت تتقدم بشكل ممتاز.", cta: "الانتقال إلى خطوتي التالية" };
  return { title: "أحسنت، أكملت المستوى الثالث", text: "أكملت أنشطة الطلاقة والفهم. أصبح مسارك جاهزًا للاختبار البعدي عندما يفتحه المشرف.", cta: "العودة إلى مساري" };
}

export default function StudentActivityPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = String(params.id);
  const [view, setView] = useState<ViewPayload | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [waitingReview, setWaitingReview] = useState(false);
  const [showContextIntro, setShowContextIntro] = useState(false);
  const [introPlaybackComplete, setIntroPlaybackComplete] = useState(false);
  const [error, setError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [memoryPreview, setMemoryPreview] = useState(true);
  const startedAtRef = useRef(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playback = useAudioQueue(setError, () => {
    if (showContextIntro && view?.context_intro?.kind === "audio_story") {
      setIntroPlaybackComplete(true);
    }
  });
  const stopPlayback = playback.stop;

  const interaction = view?.interaction_type;
  const step = view?.step;
  const round = view?.round;
  const itemId = view?.item_id;
  const levelId = view?.level_id ?? progress?.level_id ?? 1;
  const options = step?.options ?? [];
  const targetCount = step?.required_selection_count ?? 0;
  const audioAssets = useMemo(() => step?.assets?.filter((asset) => asset.asset_type === "audio") ?? [], [step]);
  const imageAssets = useMemo(() => step?.assets?.filter((asset) => asset.asset_type === "image") ?? [], [step]);
  const contextImages = useMemo(() => view?.assets?.filter((asset) => asset.asset_type === "image") ?? [], [view]);
  const stepContextImages = useMemo(() => imageAssets.filter((asset) => !asset.option_id), [imageAssets]);
  const imageOptions = imageAssets.filter((asset) => asset.option_id);
  const imageOptionIds = new Set(imageOptions.map((asset) => Number(asset.option_id)));
  const sequenceImagesComplete = options.length > 0 && options.every((option) => imageOptionIds.has(option.id));
  const percent = progress ? Math.min(100, Math.round((progress.completed_items / Math.max(1, progress.total_items)) * 100)) : 0;

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/activities/session/${sessionId}/progress`, { cache: "no-store" });
    if (response.ok) setProgress(await response.json());
  }, [sessionId]);

  const resetRoundState = useCallback(() => {
    setSelected([]);
    setAudioBlob(null);
    setRecordingSeconds(0);
    setMemoryPreview(true);
    startedAtRef.current = Date.now();
    stopPlayback();
    setAudioUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
  }, [stopPlayback]);

  const prepareContextIntro = useCallback((data: ViewPayload) => {
    if (!data.context_intro || !data.item_id) {
      setShowContextIntro(false);
      setIntroPlaybackComplete(false);
      return;
    }
    const key = `himma:context-intro:${sessionId}:${data.item_id}`;
    const seen = window.sessionStorage.getItem(key) === "seen";
    setShowContextIntro(!seen);
    setIntroPlaybackComplete(seen || data.context_intro.kind !== "audio_story");
  }, [sessionId]);

  const loadCurrent = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const advance = await fetch(`/api/activities/session/${sessionId}/next`, { cache: "no-store" });
      const advanceData = await advance.json().catch(() => null) as AdvancePayload;
      if (!advance.ok) throw new Error(advanceData?.detail || "تعذر تجهيز النشاط");
      if (!advanceData) {
        setDone(true);
        setWaitingReview(false);
        setShowContextIntro(false);
        setIntroPlaybackComplete(false);
        setView(null);
        await fetchProgress();
        return;
      }
      if (advanceData.navigation_state === "awaiting_audio_review") {
        setDone(false);
        setWaitingReview(true);
        setShowContextIntro(false);
        setIntroPlaybackComplete(false);
        setView(null);
        await fetchProgress();
        return;
      }

      const response = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" });
      const data = await response.json().catch(() => null) as ViewPayload | null;
      if (!response.ok) throw new Error((data as { detail?: string } | null)?.detail || "تعذر تحميل بيانات النشاط");
      if (data?.navigation_state === "awaiting_audio_review") {
        setDone(false);
        setWaitingReview(true);
        setShowContextIntro(false);
        setIntroPlaybackComplete(false);
        setView(null);
        await fetchProgress();
        return;
      }
      if (!data?.step || !data.item_id || !data.interaction_type || !data.round) {
        setDone(true);
        setWaitingReview(false);
        setShowContextIntro(false);
        setIntroPlaybackComplete(false);
        setView(null);
        await fetchProgress();
        return;
      }

      setDone(false);
      setWaitingReview(false);
      setView(data);
      resetRoundState();
      prepareContextIntro(data);
      await fetchProgress();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل النشاط");
    } finally {
      setLoading(false);
    }
  }, [fetchProgress, prepareContextIntro, resetRoundState, sessionId]);

  useEffect(() => {
    const kickoff = window.setTimeout(() => void loadCurrent(), 0);
    return () => {
      window.clearTimeout(kickoff);
      if (timerRef.current) clearInterval(timerRef.current);
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      stopPlayback();
    };
  }, [loadCurrent, stopPlayback]);

  const operationKey = (kind: "answer" | "upload") => `himma:activity:${sessionId}:${step?.id ?? 0}:${(view?.attempts_used ?? 0) + 1}:${kind}`;
  const idempotencyKey = (kind: "answer" | "upload") => {
    const key = operationKey(kind);
    const existing = window.sessionStorage.getItem(key);
    if (existing) return existing;
    const created = crypto.randomUUID();
    window.sessionStorage.setItem(key, created);
    return created;
  };
  const clearKeys = () => {
    for (const kind of ["answer", "upload"] as const) window.sessionStorage.removeItem(operationKey(kind));
  };

  const promptUrls = audioAssets.map((asset) => asset.url);
  const playPrompt = () => {
    if (!promptUrls.length || step?.media_gaps.length) return;
    setError("");
    playback.toggle(promptUrls);
  };

  const playContext = () => {
    const asset = view?.context_intro?.asset;
    if (!asset || asset.asset_type !== "audio") {
      setError("الصوت المعتمد لهذه القصة غير متوفر.");
      return;
    }
    setError("");
    playback.toggle([asset.url]);
  };

  const finishContextIntro = () => {
    if (!view?.item_id) return;
    if (view.context_intro?.kind === "audio_story" && !introPlaybackComplete) return;
    window.sessionStorage.setItem(`himma:context-intro:${sessionId}:${view.item_id}`, "seen");
    stopPlayback();
    setShowContextIntro(false);
    startedAtRef.current = Date.now();
  };

  const toggleOption = (id: number) => {
    if (!interaction || submitting) return;
    if (SINGLE.has(interaction)) return setSelected([id]);
    if (MULTI.has(interaction)) {
      return setSelected((current) => current.includes(id)
        ? current.filter((value) => value !== id)
        : targetCount > 0 && current.length >= targetCount
          ? current
          : [...current, id]);
    }
    if (ORDER.has(interaction)) {
      setSelected((current) => current.includes(id) || (targetCount > 0 && current.length >= targetCount) ? current : [...current, id]);
    }
  };

  const canSubmit = Boolean(interaction && (
    (SINGLE.has(interaction) && selected.length === 1)
    || (MULTI.has(interaction) && targetCount > 0 && selected.length === targetCount)
    || (ORDER.has(interaction) && targetCount > 0 && selected.length === targetCount)
  ));

  const submitStructured = async () => {
    if (!view || !step || !interaction || !itemId || step.media_gaps.length) return;
    setSubmitting(true);
    setError("");
    try {
      const elapsed = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const response = await fetch(`/api/activities/session/${sessionId}/attempt/${itemId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey("answer") },
        body: JSON.stringify({ step_id: step.id, selected_option_ids: selected, hint_used: view.retry, elapsed_seconds: elapsed }),
      });
      const result = await response.json().catch(() => ({})) as SubmitResult;
      if (!response.ok) throw new Error(result.detail || "تعذر حفظ الإجابة");
      clearKeys();
      if (result.learning_complete) {
        setDone(true);
        await fetchProgress();
        return;
      }
      if (result.is_correct === false && !result.step_complete) {
        const refreshed = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" });
        if (refreshed.ok) setView(await refreshed.json());
        setSelected([]);
        startedAtRef.current = Date.now();
        return;
      }
      await loadCurrent();
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
        if (event.data.size) chunksRef.current.push(event.data);
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
    if (!view || !step || !audioBlob || !itemId || step.media_gaps.length) return;
    setSubmitting(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", audioBlob, "activity-reading.webm");
      const upload = await fetch(`/api/assessment/session/${sessionId}/upload-audio`, {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey("upload") },
        body: form,
      });
      const uploaded = await upload.json().catch(() => null);
      if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");
      const elapsed = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const submit = await fetch(`/api/activities/session/${sessionId}/attempt/${itemId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey("answer") },
        body: JSON.stringify({
          step_id: step.id,
          audio_storage_key: uploaded.audio_storage_key,
          audio_file_size: uploaded.audio_file_size,
          audio_mime_type: uploaded.audio_mime_type,
          audio_duration_seconds: recordingSeconds,
          elapsed_seconds: elapsed,
        }),
      });
      const result = await submit.json().catch(() => ({})) as SubmitResult;
      if (!submit.ok) throw new Error(result.detail || "تعذر حفظ القراءة");
      clearKeys();
      await loadCurrent();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ القراءة");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="loading"><div className={styles.loadingState}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={128} height={46}/><div className={styles.spinner}/><p>جاري تجهيز النشاط...</p></div></div>;
  }

  if (waitingReview) {
    return <div className={styles.resultPage} dir="rtl" data-testid="activity-session" data-phase="awaiting-audio-review"><div className={styles.resultCard}><div className={styles.resultContent}><h1 className={styles.resultTitle}>أحسنت، أنجزت الأنشطة المتاحة الآن</h1><p className={styles.resultText}>لديك {progress?.pending_audio_reviews ?? 1} تسجيل ينتظر مراجعة المشرف. لن يُحتسب التسجيل صحيحًا أو خاطئًا قبل المراجعة.</p><button className={styles.primary} onClick={() => router.push("/student")}>العودة إلى مساري</button></div><div className={styles.resultVisual}><Image src="/characters/girl/encourage.png" alt="شخصية هِمّة" width={300} height={370}/></div></div></div>;
  }

  if (done) {
    const copy = completionCopy(progress?.level_id ?? 1);
    return <div className={styles.resultPage} dir="rtl" data-testid="activity-session" data-phase="done"><div className={styles.resultCard}><div className={styles.resultContent}><h1 className={styles.resultTitle}>{copy.title}</h1><p className={styles.resultText}>{copy.text}</p><button className={styles.primary} onClick={() => router.push("/student")}>{copy.cta}</button></div><div className={styles.resultVisual}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل" width={320} height={390}/></div></div></div>;
  }

  if (!view || !step || !interaction || !round || !itemId) {
    return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="error"><div className={styles.loadingState}><h1>تعذر فتح النشاط</h1><p>{error || "بيانات النشاط غير متاحة."}</p><button className={styles.primary} onClick={() => void loadCurrent()}>حاول مرة أخرى</button></div></div>;
  }

  const explicitImageChoice = interaction === "choose_image" || interaction === "listen_choose_image";
  const partialOrderedImageMapping = ORDER.has(interaction) && imageOptions.length > 0 && !sequenceImagesComplete;
  const hasImageMappingGap = (explicitImageChoice && !sequenceImagesComplete)
    || (interaction === "memory_sequence" && !sequenceImagesComplete)
    || partialOrderedImageMapping;
  const hasMediaGap = step.media_gaps.length > 0 || hasImageMappingGap;
  const message = view.retry ? round.hint : round.encouragement;
  const isImageChoice = explicitImageChoice
    || ((interaction === "choose_many" || interaction === "listen_choose_many") && sequenceImagesComplete);
  const stimulus = String(round.stimulus_text || "").trim();
  const visualAsset = contextImages[0] || stepContextImages[0];
  const isReinforcement = view.kind === "reinforcement_activity";
  const label = isReinforcement ? "تدريب تقوية" : `المستوى ${levelId} — ${LEVEL_NAMES[levelId] || "التعلم"}`;
  const selectionLimitReached = targetCount > 0 && selected.length >= targetCount;
  const stackedOptions = view.layout_hint === "stacked_long_options";
  const stimulusFirst = view.layout_hint === "stimulus_then_question";
  const imageStimulusFirst = view.layout_hint === "image_stimulus";

  const optionButtons = (image: boolean) => image
    ? <div className={styles.imageOptions} data-testid="activity-image-options">{imageOptions.map((asset) => {
        const id = Number(asset.option_id);
        const chosen = selected.includes(id);
        return <button key={`${asset.asset_id}-${id}`} className={`${styles.imageOption} ${chosen ? styles.optionSelected : ""}`} type="button" onClick={() => toggleOption(id)} disabled={MULTI.has(interaction) && selectionLimitReached && !chosen} aria-pressed={chosen} aria-label={asset.semantic_text || options.find((option) => option.id === id)?.text || "خيار مصور"} data-testid="activity-option">{chosen && <span className={styles.selectedMark}><Check size={18}/></span>}<Image src={asset.url} alt="" aria-hidden="true" width={220} height={150} unoptimized/></button>;
      })}</div>
    : <div className={styles.options} data-layout={stackedOptions ? "stacked" : "default"} style={stackedOptions ? { gridTemplateColumns: "1fr" } : undefined} data-testid="activity-text-options">{options.map((option) => {
        const chosen = selected.includes(option.id);
        return <button key={option.id} className={`${styles.option} ${chosen ? styles.optionSelected : ""}`} type="button" onClick={() => toggleOption(option.id)} disabled={MULTI.has(interaction) && selectionLimitReached && !chosen} aria-pressed={chosen} data-testid="activity-option">{chosen && <span className={styles.selectedMark}><Check size={18}/></span>}{option.text}</button>;
      })}</div>;

  if (showContextIntro && view.context_intro) {
    const intro = view.context_intro;
    const introAsset = intro.asset;
    const requiresAudioCompletion = intro.kind === "audio_story";
    const audioIntro = introAsset?.asset_type === "audio";
    return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="context-intro" data-context-kind={intro.kind || "context"}>
      <header className={styles.header}><div className={styles.headerInner}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={124} height={44} priority/><button className={styles.exit} type="button" onClick={() => { stopPlayback(); router.push("/student"); }}><LogOut size={21}/><span>رجوع</span></button></div></header>
      <main className={styles.shell}><section className={styles.card}><div className={styles.contentColumn}>
        <h1 className={styles.questionTitle}>{intro.title || "استعد للنشاط"}</h1>
        {intro.text && <div className={`${styles.readingBox} ${intro.text.length > 120 ? styles.readingBoxLong : ""}`}>{intro.text}</div>}
        {introAsset?.asset_type === "image" && <div className={styles.contextImage}><Image src={introAsset.url} alt={introAsset.semantic_text || "صورة تمهيدية"} width={420} height={260} unoptimized/></div>}
        {audioIntro && <button type="button" className={styles.listenButton} onClick={playContext} data-testid="context-audio-control">{playback.isPlaying ? <Pause size={34}/> : playback.isPaused ? <Play size={34}/> : <Volume2 size={34}/>}<span>{playback.isPlaying ? "إيقاف مؤقت" : playback.isPaused ? "متابعة الاستماع" : introPlaybackComplete ? "استمع إلى القصة مرة أخرى" : "استمع إلى القصة"}</span></button>}
        {requiresAudioCompletion && !audioIntro && <div className={styles.notice} role="alert">هذه القصة متوقفة لأن الصوت المعتمد غير متوفر. لا يمكن تجاوز شاشة الاستماع.</div>}
        <div className={styles.instructionRow}><Info size={21}/><p>{intro.instruction || "ركّز جيدًا قبل بدء الأسئلة."}</p></div>
        {error && <div className={styles.error} role="alert">{error}</div>}
        <div className={styles.bottomActions}><button className={styles.primaryWide} type="button" onClick={finishContextIntro} disabled={requiresAudioCompletion && !introPlaybackComplete}>{requiresAudioCompletion && !introPlaybackComplete ? "استمع إلى القصة أولًا" : "ابدأ الأسئلة"}</button></div>
      </div></section></main>
    </div>;
  }

  return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase={submitting ? "submitting" : "active"} data-activity-kind={isReinforcement ? "reinforcement" : "core"} data-item-id={itemId} data-step-id={step.id} data-interaction-type={interaction} data-media-gap-count={hasMediaGap ? Math.max(1, step.media_gaps.length) : 0} data-layout-hint={view.layout_hint || ""}>
    <header className={styles.header}><div className={styles.headerInner}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={124} height={44} priority/><button className={styles.exit} type="button" onClick={() => router.push("/student")}><LogOut size={21}/><span>رجوع</span></button></div></header>
    <div className={styles.progressPanel}><div className={styles.progressTop}><span className={styles.assessmentBadge}>{label}</span><span className={styles.progressCount}>{progress?.completed_items ?? 0} من {progress?.total_items ?? 10}</span></div><div className={styles.progressTrack} aria-label={`التقدم ${percent}%`}><div className={styles.progressFill} style={{ width: `${Math.max(percent, 2)}%` }}/></div></div>
    <main className={styles.shell}><section className={styles.card}>
      <div className={styles.taskMeta}><div className={styles.skillChip}><Target size={19}/>{round.skill}</div><span className={styles.assessmentBadge}>الجولة {round.round_number} من {round.round_total}</span></div>
      <div className={styles.contentColumn}>
        {isReinforcement && <div className={styles.notice} data-testid="reinforcement-intro">هذا تدريب قصير يساعدك على إتقان المهارة، وبعد إتقانها تعود إلى نشاطك الأساسي.</div>}
        {imageStimulusFirst && visualAsset && <div className={styles.contextImage}><Image src={visualAsset.url} alt={visualAsset.semantic_text || "صورة النشاط"} width={420} height={260} unoptimized/></div>}
        {stimulusFirst && stimulus && <div className={`${styles.stimulusBox} ${stimulus.length <= 3 ? styles.letterStimulus : ""}`}>{stimulus}</div>}
        <h1 className={styles.questionTitle}>{round.question_text}</h1>
        {!stimulusFirst && stimulus && !LISTEN.has(interaction) && !READ.has(interaction) && <div className={`${styles.stimulusBox} ${stimulus.length <= 3 ? styles.letterStimulus : ""}`}>{stimulus}</div>}
        {!imageStimulusFirst && visualAsset && interaction !== "memory_sequence" && <div className={styles.contextImage}><Image src={visualAsset.url} alt={visualAsset.semantic_text || "صورة النشاط"} width={420} height={260} unoptimized/></div>}
        {LISTEN.has(interaction) && <button type="button" className={styles.listenButton} onClick={playPrompt} disabled={!audioAssets.length || hasMediaGap} data-testid="activity-listen-prompt">{playback.isPlaying ? <Pause size={34}/> : playback.isPaused ? <Play size={34}/> : <Volume2 size={34}/>}<span>{playback.isPlaying ? "إيقاف مؤقت" : playback.isPaused ? "متابعة الاستماع" : "استمع"}</span></button>}
        {READ.has(interaction) && <div className={`${styles.readingBox} ${(step.expected_reading_text?.length || stimulus.length) > 55 ? styles.readingBoxLong : ""}`} data-testid="activity-reading-text">{step.expected_reading_text || stimulus || "اقرأ النص الظاهر"}</div>}
        <div className={styles.instructionRow} data-testid="student-task-instruction"><Info size={21}/><p>{round.instruction_text}</p></div>
        {hasMediaGap && <div className={styles.notice} role="alert" data-testid="declared-media-gap">هذا النشاط متوقف لأن أصلًا تعليميًا معتمدًا غير متوفر أو غير مرتبط بكل الخيارات. لا يمكن تجاوز الجولة أو احتسابها. تواصل مع المشرف.</div>}

        {!hasMediaGap && interaction === "memory_sequence" && (memoryPreview
          ? <><div className={styles.imageOptions} data-testid="activity-memory-preview">{imageOptions.map((asset, index) => <div key={`${asset.asset_id}-${index}`} className={styles.imageOption}><span className={styles.selectedMark}>{index + 1}</span><Image src={asset.url} alt={asset.semantic_text || `الصورة ${index + 1}`} width={220} height={150} unoptimized/></div>)}</div><div className={styles.inlineActions}><button className={styles.primary} type="button" onClick={() => setMemoryPreview(false)}>التالي</button></div></>
          : <><div className={styles.sequenceBoard}>{selected.length === 0 ? <span className={styles.sequenceHint}>رتّب الصور كما ظهرت.</span> : selected.map((id, index) => { const asset = imageOptions.find((candidate) => Number(candidate.option_id) === id); return <span className={styles.sequenceChip} key={`${id}-${index}`}><span className={styles.number}>{index + 1}</span>{asset && <Image src={asset.url} alt={asset.semantic_text || `العنصر ${index + 1}`} width={70} height={50} unoptimized/>}</span>; })}</div><div className={styles.imageOptions} data-testid="activity-sequence-image-options">{imageOptions.filter((asset) => !selected.includes(Number(asset.option_id))).map((asset) => <button key={`${asset.asset_id}-${asset.option_id}`} className={styles.imageOption} type="button" onClick={() => toggleOption(Number(asset.option_id))} disabled={selectionLimitReached} aria-label={asset.semantic_text || "عنصر ترتيب"}><Image src={asset.url} alt="" aria-hidden="true" width={220} height={150} unoptimized/></button>)}</div></>)}

        {!hasMediaGap && interaction !== "memory_sequence" && (interaction === "sequence" || interaction === "path_sequence" || interaction === "build_word") && <><div className={styles.sequenceBoard}>{selected.length === 0 ? <span className={styles.sequenceHint}>ابدأ بالعنصر الأول ثم أكمل بالترتيب.</span> : selected.map((id, index) => { const option = options.find((candidate) => candidate.id === id); const asset = imageOptions.find((candidate) => Number(candidate.option_id) === id); return <span className={styles.sequenceChip} key={`${id}-${index}`}><span className={styles.number}>{index + 1}</span>{sequenceImagesComplete && interaction !== "build_word" && asset ? <Image src={asset.url} alt={asset.semantic_text || option?.text || `العنصر ${index + 1}`} width={70} height={50} unoptimized/> : option?.text}</span>; })}</div>{sequenceImagesComplete && interaction !== "build_word" ? <div className={styles.imageOptions} data-testid="activity-sequence-image-options">{imageOptions.filter((asset) => !selected.includes(Number(asset.option_id))).map((asset) => <button key={`${asset.asset_id}-${asset.option_id}`} className={styles.imageOption} type="button" onClick={() => toggleOption(Number(asset.option_id))} disabled={selectionLimitReached} aria-label={asset.semantic_text || "عنصر ترتيب"}><Image src={asset.url} alt="" aria-hidden="true" width={220} height={150} unoptimized/></button>)}</div> : <div className={styles.options} data-testid="activity-sequence-options">{options.filter((option) => !selected.includes(option.id)).map((option) => <button key={option.id} className={styles.option} type="button" onClick={() => toggleOption(option.id)} disabled={selectionLimitReached}>{option.text}</button>)}</div>}</>}

        {!hasMediaGap && interaction !== "memory_sequence" && !ORDER.has(interaction) && !READ.has(interaction) && optionButtons(isImageChoice)}

        {!hasMediaGap && READ.has(interaction) && <div className={styles.recordPanel}>{!audioBlob ? <><button className={`${styles.recordButton} ${isRecording ? styles.recordButtonRecording : ""}`} type="button" onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"} data-testid="record-reading">{isRecording ? <MicOff size={30}/> : <Mic size={30}/>}</button><p className={styles.recordLabel}>{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</p>{isRecording && interaction !== "timed_read_aloud" && <p className={styles.timer}>{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</p>}</> : <>{audioUrl && <audio className={styles.audioPreview} src={audioUrl} controls/>}<div className={styles.inlineActions}><button className={styles.secondary} type="button" onClick={resetRoundState}><RotateCcw size={17}/> إعادة التسجيل</button><button className={styles.primary} type="button" onClick={() => void uploadReading()} disabled={submitting}>{submitting ? "جاري الحفظ..." : "إرسال التسجيل للمراجعة"}</button></div><p className={styles.recordLabel}>يراجع المشرف التسجيل ويعتمده أو يطلب إعادة التسجيل.</p></>}</div>}
      </div>

      <aside className={styles.coach} aria-label="نصيحة هِمّة"><div className={styles.tip}><span>{message}</span></div><Image className={styles.character} src={view.retry ? "/characters/girl/encourage.png" : "/characters/girl/explain.png"} alt="شخصية هِمّة" width={150} height={205}/></aside>
      {error && <div className={styles.error} role="alert">{error}</div>}
      {!hasMediaGap && !READ.has(interaction) && !(interaction === "memory_sequence" && memoryPreview) && <div className={styles.bottomActions}>{ORDER.has(interaction) && selected.length > 0 && <button className={styles.secondary} type="button" onClick={() => setSelected([])} disabled={submitting}><RotateCcw size={17}/> إعادة الترتيب</button>}<button className={styles.primaryWide} type="button" onClick={() => void submitStructured()} disabled={submitting || !canSubmit}>{submitting ? "جاري الحفظ..." : "تأكيد والمتابعة"}</button></div>}
    </section></main>
  </div>;
}
