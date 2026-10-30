"use client";

import Image from "next/image";
import EducationalImage from "./EducationalImage";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Check, Mic, MicOff, Pause, RotateCcw, Volume2, X } from "lucide-react";
import styles from "./InteractionPlayer.module.css";

export type InteractionKind = "choose_one" | "listen_choose_one" | "choose_image" | "sequence" | "build_word" | "read_aloud";
type MediaKind = "audio" | "image" | "video";
interface MediaRef { media_id: string; kind: MediaKind; }
interface Option { id: string; text: string | null; media: MediaRef[]; }
interface Question {
  question_id: string;
  role: "guided_practice" | "independent_check" | "support_check" | "pretest" | "posttest";
  interaction: InteractionKind;
  prompt: string;
  stimulus: { text: string | null; media: MediaRef[] };
  options: Option[];
  hint?: string | null;
}
interface ResolvedMedia { asset_id: string; kind: MediaKind; state: string; url: string | null; test_only: boolean; }
export interface InteractionPayload {
  question: Question;
  media: Record<string, ResolvedMedia>;
  progress: { index: number; total: number; stage: string };
  attempts: number;
}
interface SubmissionResult { correct?: boolean; retry_required: boolean; hint?: string | null; message?: string; status: string; help_level?: number; model_option_ids?: string[]; assisted_advance?: boolean; }

interface Props {
  sessionId: number;
  interaction: InteractionPayload;
  onLessonChange: (lesson: unknown) => void;
  endpointBase?: string;
  suspended?: boolean;
}

function requestKey(prefix: string) {
  return `${prefix}:${Date.now()}:${crypto.randomUUID()}`;
}

export default function InteractionPlayer({ sessionId, interaction, onLessonChange, endpointBase = "/api/v2/lessons", suspended = false }: Props) {
  const { question, media } = interaction;
  const descriptionIdPrefix = useId();
  const [selected, setSelected] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<SubmissionResult | null>(null);
  // The server has advanced after bounded coaching; let the child review the
  // model before displaying the next question, without another write request.
  const [assistedNext, setAssistedNext] = useState<unknown | null>(null);
  const [error, setError] = useState("");
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioState, setAudioState] = useState<"idle" | "loading" | "playing">("idle");
  // A catalog entry marked "ready" can still fail at the browser (404,
  // expired signed URL, unsupported audio or a broken image). Never grade
  // a response when its required media cannot actually be used.
  const [failedMediaIds, setFailedMediaIds] = useState<string[]>([]);
  const [loadedImageUrls, setLoadedImageUrls] = useState<string[]>([]);
  const markImageLoaded = (url: string) => setLoadedImageUrls((current) => current.includes(url) ? current : [...current, url]);
  const markMediaFailure = (id: string) => {
    setFailedMediaIds((current) => current.includes(id) ? current : [...current, id]);
    if (media[id]?.kind === "image") setLoadedImageUrls((current) => current.filter((url) => url !== media[id].url));
  };
  const clearMediaFailure = (id: string) => setFailedMediaIds((current) => current.filter((item) => item !== id));
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const shellRef = useRef<HTMLElement | null>(null);
  const answerKeyRef = useRef(requestKey("answer"));
  const uploadKeyRef = useRef(requestKey("upload"));
  // A lost HTTP acknowledgment may follow a committed answer. Keep the exact
  // request until the server confirms it; never apply a changed answer to the
  // next question while the browser still shows the previous question.
  const pendingAnswerRef = useRef<{ submit_key: string; answer: Record<string, unknown> } | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mountedRef = useRef(false);
  const micRequestIdRef = useRef(0);
  const micRequestPendingRef = useRef(false);
  const [requestingMic, setRequestingMic] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      micRequestIdRef.current += 1;
      micRequestPendingRef.current = false;
      audioRef.current?.pause();
      const recorder = recorderRef.current;
      if (recorder) {
        // Prevent a late recorder event from writing a child's audio into a new question.
        recorder.ondataavailable = null;
        recorder.onstop = null;
        recorder.onerror = null;
        if (recorder.state !== "inactive") {
          try { recorder.stop(); } catch { /* Tracks are stopped below even if stop() races. */ }
        }
        recorder.stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  useEffect(() => {
    if (!suspended) return;
    // Reviewing the explanation preserves this question's draft, but must
    // never leave a microphone or an old playback running behind the video.
    micRequestIdRef.current += 1;
    micRequestPendingRef.current = false;
    audioRef.current?.pause();
    audioRef.current = null;
    shellRef.current?.querySelectorAll<HTMLMediaElement>("audio, video").forEach((element) => element.pause());
    let cancelled = false;
    // Publish the external-media cancellation together after native handlers
    // settle. Cancel this notification if the component resumes/unmounts.
    queueMicrotask(() => {
      if (cancelled || !mountedRef.current) return;
      setRequestingMic(false);
      setPlayingId(null);
      setAudioState("idle");
    });
    const recorder = recorderRef.current;
    if (recorder?.state === "recording") {
      try { recorder.stop(); }
      catch {
        recorder.stream.getTracks().forEach((track) => track.stop());
        queueMicrotask(() => { if (!cancelled && mountedRef.current) setRecording(false); });
      }
    }
    return () => { cancelled = true; };
  }, [suspended]);

  const ordered = question.interaction === "sequence" || question.interaction === "build_word";
  const missingRequiredOptions = !OPEN_INTERACTIONS.has(question.interaction) && question.options.length === 0;
  // An empty ordered question previously satisfied 0 === 0 and enabled
  // submission of an empty answer. Never grade an incomplete question.
  const invalidQuestion = missingRequiredOptions || !SUPPORTED_INTERACTIONS.has(question.interaction);
  // A missing referenced asset must not turn an audio/image question into a
  // guessable text-only answer. This also covers absent image choices even
  // when a malformed payload forgot to declare their media references.
  const missingRequiredMedia = [
    ...question.stimulus.media,
    ...question.options.flatMap((option) => option.media),
  ].some((reference) => {
    const asset = media[reference.media_id];
    // InteractionPlayer renders only images and audio; a declared video
    // cannot be used as a substitute for a supported question stimulus.
    return reference.kind === "video" || !asset || asset.kind !== reference.kind || asset.state !== "ready" || !asset.url || failedMediaIds.includes(reference.media_id);
  }) || (question.interaction === "choose_image" &&
    question.options.some((option) => !option.media.some((item) => item.kind === "image")));
  const imagesLoading = [...question.stimulus.media, ...question.options.flatMap((option) => option.media)]
    .some((reference) => reference.kind === "image" && Boolean(media[reference.media_id]?.url)
      && !loadedImageUrls.includes(media[reference.media_id].url!));
  const ready = useMemo(() => {
    if (missingRequiredMedia || invalidQuestion || imagesLoading) return false;
    if (question.interaction === "read_aloud") return Boolean(audioBlob);
    if (ordered) return selected.length === question.options.length;
    return selected.length === 1;
  }, [audioBlob, imagesLoading, invalidQuestion, missingRequiredMedia, ordered, question.interaction, question.options.length, selected.length]);

  const playMedia = async (assetId: string) => {
    const asset = media[assetId];
    if (!asset?.url) { setError("الصوت غير جاهز، ولن يُكشف بديله نصيًا."); return; }
    if (playingId === assetId && audioRef.current) {
      audioRef.current.pause();
      // Invalidate this playback before any delayed media event/promise settles.
      audioRef.current = null;
      setPlayingId(null);
      setAudioState("idle");
      return;
    }
    audioRef.current?.pause();
    const audio = new Audio(asset.url);
    audioRef.current = audio;
    setPlayingId(assetId);
    setAudioState("loading");
    // A paused/replaced audio element can still dispatch late events or settle
    // its play() promise. Only the current element may change media readiness.
    audio.onwaiting = () => { if (audioRef.current === audio) setAudioState("loading"); };
    audio.onplaying = () => {
      if (audioRef.current !== audio) return;
      clearMediaFailure(assetId);
      setAudioState("playing");
    };
    audio.onended = () => {
      if (audioRef.current !== audio) return;
      audioRef.current = null;
      setPlayingId(null);
      setAudioState("idle");
    };
    audio.onerror = () => {
      if (audioRef.current !== audio) return;
      audioRef.current = null;
      markMediaFailure(assetId);
      setPlayingId(null);
      setAudioState("idle");
      setError("تعذر تشغيل الصوت. حاول مرة أخرى.");
    };
    try {
      await audio.play();
      if (audioRef.current !== audio) return;
      clearMediaFailure(assetId);
      setError("");
      setAudioState("playing");
    } catch {
      if (audioRef.current !== audio) return;
      audioRef.current = null;
      markMediaFailure(assetId);
      setPlayingId(null);
      setAudioState("idle");
      setError("تعذر تشغيل الصوت. حاول الضغط على زر الصوت مرة أخرى.");
    }
  };

  const choose = (id: string) => {
    if (saving || awaitingConfirmation || missingRequiredMedia || invalidQuestion) return;
    if (ordered) { if (!selected.includes(id)) setSelected((current) => [...current, id]); return; }
    setSelected([id]);
  };

  const startRecording = async () => {
    if (saving || awaitingConfirmation || recording || micRequestPendingRef.current) return;
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("التسجيل غير مدعوم في هذا المتصفح."); return;
    }
    const requestId = ++micRequestIdRef.current;
    micRequestPendingRef.current = true;
    setRequestingMic(true);
    let stream: MediaStream | null = null;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Permission may arrive after the learner leaves the question. Never
      // construct a recorder or retain an open microphone for that old route.
      if (!mountedRef.current || requestId !== micRequestIdRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      chunksRef.current = [];
      // Match the recording browser's supported container instead of assuming
      // WebM (Safari on iPhone commonly produces MP4 audio).
      const formats = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm"];
      const supported = formats.find((type) => MediaRecorder.isTypeSupported?.(type));
      const recorder = supported ? new MediaRecorder(stream, { mimeType: supported }) : new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (mountedRef.current && recorderRef.current === recorder && event.data.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stream?.getTracks().forEach((track) => track.stop());
        if (!mountedRef.current || recorderRef.current !== recorder) return;
        recorderRef.current = null;
        const mimeType = recorder.mimeType || chunksRef.current[0]?.type;
        const blob = new Blob(chunksRef.current, { type: mimeType || "" });
        if (!blob.size || blob.size > 10 * 1024 * 1024) {
          // Fail locally, before S3 receives invalid/oversize child audio.
          setAudioBlob(null);
          setError("التسجيل فارغ أو تجاوز الحجم المسموح (10 ميجابايت). سجّل قراءة أقصر.");
        } else if (!mimeType || !mimeType.startsWith("audio/")) {
          setAudioBlob(null);
          setError("تعذر تحديد صيغة التسجيل. أعد المحاولة من المتصفح.");
        } else {
          setAudioBlob(blob);
          setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return URL.createObjectURL(blob); });
        }
        setRecording(false);
      };
      // A recorder can fail asynchronously after start() (device removal,
      // encoder failure). Never turn partial chunks into a valid answer.
      recorder.onerror = () => {
        stream?.getTracks().forEach((track) => track.stop());
        if (!mountedRef.current || recorderRef.current !== recorder) return;
        recorder.ondataavailable = null;
        recorder.onstop = null;
        recorder.onerror = null;
        if (recorder.state !== "inactive") {
          try { recorder.stop(); } catch { /* Tracks were already stopped. */ }
        }
        recorderRef.current = null;
        chunksRef.current = [];
        setAudioBlob(null);
        setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return null; });
        setRecording(false);
        setError("تعذر تسجيل الصوت. حاول مرة أخرى.");
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
      setRecordingSeconds(0);
    } catch {
      stream?.getTracks().forEach((track) => track.stop());
      if (mountedRef.current && requestId === micRequestIdRef.current) {
        setError("لم نتمكن من تشغيل الميكروفون. اسمح باستخدامه ثم حاول مرة أخرى.");
      }
    } finally {
      if (mountedRef.current && requestId === micRequestIdRef.current) {
        micRequestPendingRef.current = false;
        setRequestingMic(false);
      }
    }
  };

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [recording]);

  const stopRecording = () => {
    const recorder = recorderRef.current;
    if (recorder?.state === "recording") {
      try { recorder.stop(); }
      catch {
        // stop() can throw after data chunks have arrived. A late onstop
        // must not promote that partial capture into a valid submission.
        recorder.ondataavailable = null;
        recorder.onstop = null;
        recorder.onerror = null;
        recorderRef.current = null;
        chunksRef.current = [];
        recorder.stream.getTracks().forEach((track) => track.stop());
        setAudioBlob(null);
        setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return null; });
        setError("تعذر إنهاء التسجيل. حاول مرة أخرى.");
      }
    }
    setRecording(false);
  };

  const resetRecording = () => {
    if (saving || awaitingConfirmation) return;
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    // A fresh recording must not reuse the idempotency key of old audio bytes.
    uploadKeyRef.current = requestKey("upload");
    answerKeyRef.current = requestKey("answer");
    setAudioUrl(null); setAudioBlob(null); setRecordingSeconds(0); setFeedback(null);
  };

  const submit = async () => {
    if (!ready || saving || assistedNext !== null || missingRequiredMedia || invalidQuestion) return;
    setSaving(true); setError("");
    try {
      let pending = pendingAnswerRef.current;
      if (!pending) {
        let answer: Record<string, unknown>;
        if (question.interaction === "read_aloud") {
          if (!audioBlob) throw new Error("سجل قراءتك أولًا");
          const form = new FormData();
          form.append("file", audioBlob, audioBlob.type.includes("mp4") ? "v2-reading.m4a" : "v2-reading.webm");
          const upload = await fetch(`${endpointBase}/sessions/${sessionId}/recording`, {
            method: "POST", headers: { "Idempotency-Key": uploadKeyRef.current }, body: form,
          });
          const uploaded = await upload.json().catch(() => null);
          if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");
          answer = { ...uploaded, audio_duration_seconds: Math.max(1, recordingSeconds) };
        } else answer = { selected_option_ids: [...selected] };
        pending = { submit_key: answerKeyRef.current, answer };
        pendingAnswerRef.current = pending;
      }

      const response = await fetch(`${endpointBase}/sessions/${sessionId}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ submit_key: pending.submit_key, ...pending.answer }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) {
        // Only a definite input-validation rejection is safe to edit in place.
        // A 503, lost response or 409 may mean the server already advanced.
        if (response.status === 400 || response.status === 422) {
          pendingAnswerRef.current = null;
          setAwaitingConfirmation(false);
          answerKeyRef.current = requestKey("answer");
        }
        throw new Error(result?.detail || "تعذر حفظ الإجابة");
      }
      pendingAnswerRef.current = null;
      setAwaitingConfirmation(false);
      setFeedback(result.submission);
      answerKeyRef.current = requestKey("answer");
      uploadKeyRef.current = requestKey("upload");
      if (result.submission.assisted_advance && interaction.progress.stage === "support_practice") {
        setAssistedNext(result.lesson ?? result.assessment);
        setSelected([]);
      } else if (!result.submission.retry_required) onLessonChange(result.lesson ?? result.assessment);
      else setSelected([]);
    } catch (reason) {
      if (pendingAnswerRef.current) setAwaitingConfirmation(true);
      setError(reason instanceof Error ? reason.message : "تعذر حفظ الإجابة");
    } finally { setSaving(false); }
  };

  const renderMedia = (reference: MediaRef, option = false) => {
    const asset = media[reference.media_id];
    if (!asset || asset.kind !== reference.kind || asset.state !== "ready" || !asset.url || (reference.kind === "image" && failedMediaIds.includes(reference.media_id))) {
      return <span className={styles.mediaMissing} role="status">الوسيط غير جاهز</span>;
    }
    if (reference.kind === "audio") {
      const active = playingId === reference.media_id;
      const label = active ? "إيقاف الصوت" : option ? "تشغيل صوت هذا الخيار" : "تشغيل صوت السؤال";
      return <button type="button" className={styles.audioButton} onClick={(event) => { event.stopPropagation(); void playMedia(reference.media_id); }} aria-label={label}>{active ? <Pause size={25}/> : <Volume2 size={25}/>}<span>{active && audioState === "loading" ? "جاري التحميل" : active ? "إيقاف" : "استمع"}</span></button>;
    }
    if (reference.kind === "image") return <EducationalImage key={asset.url} className={styles.educationImage} src={asset.url} width={300} height={220} alt={option ? "صورة خيار" : "صورة السؤال"} onLoad={() => markImageLoaded(asset.url!)} onError={() => markMediaFailure(reference.media_id)}/>;
    return <div className={styles.mediaMissing} role="alert">الوسيط غير جاهز</div>;
  };

  const isAssessment = interaction.progress.stage === "pretest" || interaction.progress.stage === "posttest";
  const stageLabel = interaction.progress.stage === "guided_practice" ? "تدريب موجّه"
    : interaction.progress.stage === "support_practice" ? "مساعدة مركزة"
    : interaction.progress.stage === "additional_check" ? "تحقق قصير"
    : interaction.progress.stage === "support_check" ? "تحقق بعد المساعدة"
    : interaction.progress.stage === "pretest" ? "الاختبار القبلي"
    : interaction.progress.stage === "posttest" ? "الاختبار البعدي"
    : "اختبار مستقل";
  const guidedStage = interaction.progress.stage === "guided_practice" || interaction.progress.stage === "support_practice";
  const retryFeedback = !isAssessment && Boolean(feedback?.retry_required);
  const assistedFeedback = interaction.progress.stage === "support_practice" && Boolean(feedback?.assisted_advance);
  // A single, accessible coach message handles practice retries/assistance.
  // Assessment correctness, teaching models and hidden hints are NEVER shown here.
  const retryHint = guidedStage && retryFeedback && feedback?.hint ? feedback.hint : null;
  const modelIds = interaction.progress.stage === "support_practice" && (feedback?.help_level ?? 0) >= 2
    ? (feedback?.model_option_ids ?? []) : [];
  const coachImage = retryFeedback || assistedFeedback ? "/characters/girl/try-again.png" : "/characters/girl/explain.png";
  const coachMessage = assistedFeedback ? feedback?.message || "راجع المثال ثم نواصل."
    : retryFeedback ? (retryHint ? `حاول مرة أخرى. تلميح: ${retryHint}`
    : feedback?.message?.trim() || "خذ وقتك، ثم جرّب إجابة أخرى.")
    : isAssessment ? "خذ وقتك، واستمع أو اقرأ السؤال ثم اختر إجابتك."
    : interaction.progress.stage === "support_practice" ? "هذه مساعدة قصيرة. جرّب خطوة خطوة."
    : interaction.progress.stage === "additional_check" || interaction.progress.stage === "support_check" ? "تأمل السؤال جيدًا، ثم أجب بنفسك."
    : "اقرأ التعليمات، ثم جرّب بنفسك. يمكنك إعادة الصوت.";

  return <section ref={shellRef} className={styles.shell} dir="rtl" data-testid="v2-interaction-player" data-interaction={question.interaction}>
    <div className={styles.topline}><span>{stageLabel}</span><span>{interaction.progress.index} من {interaction.progress.total}</span></div>
    <aside className={`${styles.coach} ${retryFeedback || assistedFeedback ? styles.coachRetry : ""}`} role={retryFeedback || assistedFeedback ? "status" : undefined} aria-label="رسالة هِمّة" data-testid="v2-question-coach">
      <Image src={coachImage} alt="" width={88} height={108} aria-hidden="true" />
      <p>{coachMessage}</p>
    </aside>
    <h2>{question.prompt}</h2>
    {missingRequiredMedia && <div className={styles.mediaMissing} role="alert">هذا السؤال يحتاج صورة أو صوتًا غير جاهز الآن. لن تُرسل الإجابة حتى يتوفر الوسيط. للصوت أعد تشغيله.
      {failedMediaIds.some((id) => media[id]?.kind === "image") && <button type="button" className={styles.secondary} onClick={() => setFailedMediaIds((current) => current.filter((id) => media[id]?.kind !== "image"))}>إعادة تحميل الصور</button>}
    </div>}
    {missingRequiredOptions && <div className={styles.mediaMissing} role="alert">خيارات هذا السؤال غير مكتملة. لن تُرسل الإجابة حتى تصبح جاهزة.</div>}
    {modelIds.length > 0 && <div className={styles.supportModel} aria-label="مثال محلول للتعلّم">
      <strong>{ordered ? "انظر إلى الترتيب الصحيح" : "هذا مثال للإجابة الصحيحة"}</strong>
      <div className={styles.supportModelOptions}>{modelIds.map((id, index) => {
        const option = question.options.find((item) => item.id === id);
        if (!option) return null;
        return <div key={id} className={styles.supportModelOption}>
          {ordered && <b>{index + 1}</b>}
          {option.text && <span>{option.text}</span>}
          {option.media.map((item) => <span key={item.media_id}>{renderMedia(item, true)}</span>)}
        </div>;
      })}</div>
      <small>هذا المثال للتعلّم فقط، وليس نتيجة اختبارك المستقل.</small>
    </div>}
    {question.stimulus.text && <div className={styles.stimulusText}>{question.stimulus.text}</div>}
    {question.stimulus.media.length > 0 && <div className={styles.stimulusMedia}>{question.stimulus.media.map((item) => <div key={item.media_id}>{renderMedia(item)}</div>)}</div>}

    {ordered && <div className={styles.orderTray} aria-label="الترتيب المختار">{selected.length ? selected.map((id, index) => {
      const option = question.options.find((item) => item.id === id);
      const imageRef = option?.media.find((item) => item.kind === "image");
      const imageAsset = imageRef ? media[imageRef.media_id] : null;
      const imageReady = imageAsset?.kind === "image" && imageAsset.state === "ready" && Boolean(imageAsset.url) && !failedMediaIds.includes(imageRef!.media_id);
      return <button key={id} type="button" disabled={saving || awaitingConfirmation} aria-label={`إزالة العنصر ${index + 1} من الترتيب`} aria-describedby={option?.text ? `${descriptionIdPrefix}-selected-${index}` : undefined} onClick={() => setSelected((current) => current.filter((value) => value !== id))}>
        <b>{index + 1}</b>
        {imageReady && <EducationalImage key={imageAsset.url} className={styles.orderPreview} src={imageAsset.url!} width={68} height={52} alt={`صورة العنصر ${index + 1}`} onError={() => markMediaFailure(imageRef!.media_id)}/>}
        {option?.text && <span id={`${descriptionIdPrefix}-selected-${index}`} className={styles.orderText}>{option.text}</span>}
        {!option?.text && !imageReady && <span className={styles.orderText}>عنصر {index + 1}</span>}
        <X size={14} aria-hidden="true"/>
      </button>;
    }) : <span>اضغط العناصر بالترتيب الصحيح</span>}</div>}

    {!OPEN_INTERACTIONS.has(question.interaction) && <div className={`${styles.options} ${question.interaction === "choose_image" ? styles.imageOptions : ""}`}>{question.options.map((option, optionIndex) => {
      const chosen = selected.includes(option.id);
      const optionDescriptionId = `${descriptionIdPrefix}-option-${optionIndex}`;
      const disabled = saving || awaitingConfirmation || assistedNext !== null || missingRequiredMedia || invalidQuestion || (ordered && chosen);
      const audioMedia = option.media.filter((item) => item.kind === "audio");
      const visualMedia = option.media.filter((item) => item.kind !== "audio");
      return <div key={option.id} className={`${styles.option} ${chosen ? styles.selected : ""}`}>
        {audioMedia.map((item) => <span key={item.media_id}>{renderMedia(item, true)}</span>)}
        <button type="button" disabled={disabled} className={styles.optionChoice} onClick={() => choose(option.id)} aria-pressed={chosen} aria-label={`اختيار الخيار ${optionIndex + 1}`} aria-describedby={option.text ? optionDescriptionId : undefined}>
          {visualMedia.map((item) => <span key={item.media_id}>{renderMedia(item, true)}</span>)}
          {question.interaction === "choose_image" && !visualMedia.some((item) => item.kind === "image") && <span className={styles.mediaMissing}>الصورة غير جاهزة</span>}
          {option.text && <strong id={optionDescriptionId}>{option.text}</strong>}{chosen && !ordered && <Check className={styles.check} size={19}/>}
        </button>
      </div>;
    })}</div>}

    {question.interaction === "read_aloud" && <div className={styles.recorder}>{!audioBlob ? <><button type="button" className={`${styles.recordButton} ${recording ? styles.recording : ""}`} onClick={recording ? stopRecording : () => void startRecording()} disabled={saving || awaitingConfirmation || requestingMic} aria-label={requestingMic ? "جاري تفعيل الميكروفون" : recording ? "إيقاف التسجيل" : "بدء التسجيل"}>{recording ? <MicOff size={28}/> : <Mic size={28}/>}</button><p>{requestingMic ? "جاري طلب إذن الميكروفون..." : recording ? `جاري التسجيل… ${recordingSeconds} ث` : "اضغط ثم اقرأ بصوت واضح"}</p></> : <>{audioUrl && <audio controls src={audioUrl}/>}<button type="button" className={styles.secondary} disabled={saving || awaitingConfirmation} onClick={resetRecording}><RotateCcw size={16}/> إعادة التسجيل</button><p>سيبقى التقييم معلقًا حتى يراجعه المشرف.</p></>}</div>}

    {!isAssessment && feedback && !feedback.retry_required && !assistedFeedback && <div className={`${styles.feedback} ${feedback.correct === false ? styles.retry : styles.accepted}`} role="status"><strong>{feedback.correct === true ? "أحسنت!" : feedback.correct === false ? "لم تكتمل الإجابة" : "تم الحفظ"}</strong><span>{feedback.message}</span></div>}
    {error && <div className={styles.error} role="alert">{error}</div>}
    {assistedNext !== null
      ? <button type="button" className={styles.submit} onClick={() => { const next = assistedNext; setAssistedNext(null); onLessonChange(next); }}>فهمت، نكمل</button>
      : <button type="button" className={styles.submit} disabled={!ready || saving || recording} onClick={() => void submit()}>{saving ? "جاري الحفظ..." : awaitingConfirmation ? "إعادة محاولة حفظ الإجابة" : question.interaction === "read_aloud" ? "إرسال التسجيل للمراجعة" : isAssessment ? "حفظ الإجابة والمتابعة" : "تحقق من الإجابة"}</button>}
  </section>;
}

const SUPPORTED_INTERACTIONS = new Set<InteractionKind>(["choose_one", "listen_choose_one", "choose_image", "sequence", "build_word", "read_aloud"]);
const OPEN_INTERACTIONS = new Set<InteractionKind>(["read_aloud"]);
