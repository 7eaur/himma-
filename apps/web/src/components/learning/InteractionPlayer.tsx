"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Mic, MicOff, Pause, RotateCcw, Volume2, X } from "lucide-react";
import styles from "./InteractionPlayer.module.css";

export type InteractionKind = "choose_one" | "listen_choose_one" | "choose_image" | "sequence" | "build_word" | "read_aloud" | "write_text";
type MediaKind = "audio" | "image" | "video";
interface MediaRef { media_id: string; kind: MediaKind; }
interface Option { id: string; text: string | null; media: MediaRef[]; }
interface Question {
  question_id: string;
  role: "guided_practice" | "independent_check" | "support_check";
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
  draft: string | null;
}
interface SubmissionResult { correct?: boolean; retry_required: boolean; hint?: string | null; message?: string; status: string; }

interface Props {
  sessionId: number;
  interaction: InteractionPayload;
  onLessonChange: (lesson: unknown) => void;
}

function requestKey(prefix: string) {
  return `${prefix}:${Date.now()}:${crypto.randomUUID()}`;
}

export default function InteractionPlayer({ sessionId, interaction, onLessonChange }: Props) {
  const { question, media } = interaction;
  const [selected, setSelected] = useState<string[]>([]);
  const [text, setText] = useState(interaction.draft ?? "");
  const [saving, setSaving] = useState(false);
  const [draftState, setDraftState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [feedback, setFeedback] = useState<SubmissionResult | null>(null);
  const [error, setError] = useState("");
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioState, setAudioState] = useState<"idle" | "loading" | "playing">("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const answerKeyRef = useRef(requestKey("answer"));
  const uploadKeyRef = useRef(requestKey("upload"));
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => () => {
    audioRef.current?.pause();
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    recorderRef.current?.stream.getTracks().forEach((track) => track.stop());
  }, [audioUrl]);

  useEffect(() => {
    if (question.interaction !== "write_text" || text === (interaction.draft ?? "")) return;
    const timer = window.setTimeout(() => {
      void fetch(`/api/v2/lessons/sessions/${sessionId}/draft`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      }).then((response) => {
        if (!response.ok) throw new Error();
        setDraftState("saved");
      }).catch(() => setDraftState("error"));
    }, 650);
    return () => window.clearTimeout(timer);
  }, [interaction.draft, question.interaction, sessionId, text]);

  const ordered = question.interaction === "sequence" || question.interaction === "build_word";
  const ready = useMemo(() => {
    if (question.interaction === "write_text") return Boolean(text.trim());
    if (question.interaction === "read_aloud") return Boolean(audioBlob);
    if (ordered) return selected.length === question.options.length;
    return selected.length === 1;
  }, [audioBlob, ordered, question.interaction, question.options.length, selected.length, text]);

  const playMedia = async (assetId: string) => {
    const asset = media[assetId];
    if (!asset?.url) { setError("الصوت غير جاهز، ولن يُكشف بديله نصيًا."); return; }
    if (playingId === assetId && audioRef.current) {
      audioRef.current.pause();
      setPlayingId(null);
      setAudioState("idle");
      return;
    }
    audioRef.current?.pause();
    const audio = new Audio(asset.url);
    audioRef.current = audio;
    setPlayingId(assetId);
    setAudioState("loading");
    audio.onwaiting = () => setAudioState("loading");
    audio.onplaying = () => setAudioState("playing");
    audio.onended = () => { setPlayingId(null); setAudioState("idle"); };
    audio.onerror = () => { setPlayingId(null); setAudioState("idle"); setError("تعذر تشغيل الصوت. حاول مرة أخرى."); };
    try { await audio.play(); setAudioState("playing"); } catch { setPlayingId(null); setAudioState("idle"); setError("اضغط زر الصوت مرة أخرى للسماح بالتشغيل."); }
  };

  const choose = (id: string) => {
    setFeedback(null);
    if (ordered) { if (!selected.includes(id)) setSelected((current) => [...current, id]); return; }
    setSelected([id]);
  };

  const startRecording = async () => {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("التسجيل غير مدعوم في هذا المتصفح."); return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const preferred = "audio/webm;codecs=opus";
      const recorder = MediaRecorder.isTypeSupported(preferred) ? new MediaRecorder(stream, { mimeType: preferred }) : new MediaRecorder(stream);
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return URL.createObjectURL(blob); });
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
      setRecordingSeconds(0);
    } catch { setError("لم نتمكن من تشغيل الميكروفون. اسمح باستخدامه ثم حاول مرة أخرى."); }
  };

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [recording]);

  const stopRecording = () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    setRecording(false);
  };

  const resetRecording = () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null); setAudioBlob(null); setRecordingSeconds(0); setFeedback(null);
  };

  const submit = async () => {
    if (!ready || saving) return;
    setSaving(true); setError("");
    try {
      let answer: Record<string, unknown>;
      if (question.interaction === "write_text") answer = { text_response: text };
      else if (question.interaction === "read_aloud") {
        if (!audioBlob) throw new Error("سجل قراءتك أولًا");
        const form = new FormData();
        form.append("file", audioBlob, "v2-reading.webm");
        const upload = await fetch(`/api/v2/lessons/sessions/${sessionId}/recording`, {
          method: "POST", headers: { "Idempotency-Key": uploadKeyRef.current }, body: form,
        });
        const uploaded = await upload.json().catch(() => null);
        if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");
        answer = { ...uploaded, audio_duration_seconds: Math.max(1, recordingSeconds) };
      } else answer = { selected_option_ids: selected };

      const response = await fetch(`/api/v2/lessons/sessions/${sessionId}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ submit_key: answerKeyRef.current, ...answer }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(result?.detail || "تعذر حفظ الإجابة");
      setFeedback(result.submission);
      answerKeyRef.current = requestKey("answer");
      uploadKeyRef.current = requestKey("upload");
      if (!result.submission.retry_required) onLessonChange(result.lesson);
      else setSelected([]);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر حفظ الإجابة"); }
    finally { setSaving(false); }
  };

  const renderMedia = (reference: MediaRef, option = false) => {
    const asset = media[reference.media_id];
    if (reference.kind === "audio") {
      const active = playingId === reference.media_id;
      const label = active ? "إيقاف الصوت" : option ? "تشغيل صوت هذا الخيار" : "تشغيل صوت السؤال";
      return <button type="button" className={styles.audioButton} onClick={(event) => { event.stopPropagation(); void playMedia(reference.media_id); }} aria-label={label}>{active ? <Pause size={25}/> : <Volume2 size={25}/>}<span>{active && audioState === "loading" ? "جاري التحميل" : active ? "إيقاف" : "استمع"}</span></button>;
    }
    if (reference.kind === "image" && asset?.url) return <Image className={styles.educationImage} src={asset.url} width={300} height={220} unoptimized alt={option ? "صورة خيار" : "صورة السؤال"}/>;
    return <div className={styles.mediaMissing} role="alert">الوسيط غير جاهز</div>;
  };

  const stageLabel = interaction.progress.stage === "guided_practice" ? "تدريب موجّه"
    : interaction.progress.stage === "support_practice" ? "مساعدة مركزة"
    : interaction.progress.stage === "additional_check" ? "تحقق قصير"
    : interaction.progress.stage === "support_check" ? "تحقق بعد المساعدة"
    : "اختبار مستقل";

  return <section className={styles.shell} data-testid="v2-interaction-player" data-interaction={question.interaction}>
    <div className={styles.topline}><span>{stageLabel}</span><span>{interaction.progress.index} من {interaction.progress.total}</span></div>
    <h2>{question.prompt}</h2>
    {question.stimulus.text && <div className={styles.stimulusText}>{question.stimulus.text}</div>}
    {question.stimulus.media.length > 0 && <div className={styles.stimulusMedia}>{question.stimulus.media.map((item) => <div key={item.media_id}>{renderMedia(item)}</div>)}</div>}

    {ordered && <div className={styles.orderTray} aria-label="الترتيب المختار">{selected.length ? selected.map((id, index) => <button key={id} type="button" onClick={() => setSelected((current) => current.filter((value) => value !== id))}><b>{index + 1}</b>{question.options.find((option) => option.id === id)?.text}<X size={14}/></button>) : <span>اضغط العناصر بالترتيب الصحيح</span>}</div>}

    {!OPEN_INTERACTIONS.has(question.interaction) && <div className={`${styles.options} ${question.interaction === "choose_image" ? styles.imageOptions : ""}`}>{question.options.map((option, optionIndex) => {
      const chosen = selected.includes(option.id);
      const disabled = ordered && chosen;
      const audioMedia = option.media.filter((item) => item.kind === "audio");
      const visualMedia = option.media.filter((item) => item.kind !== "audio");
      return <div key={option.id} className={`${styles.option} ${chosen ? styles.selected : ""}`}>
        {audioMedia.map((item) => <span key={item.media_id}>{renderMedia(item, true)}</span>)}
        <button type="button" disabled={disabled} className={styles.optionChoice} onClick={() => choose(option.id)} aria-pressed={chosen} aria-label={`اختيار الخيار ${optionIndex + 1}`}>
          {visualMedia.map((item) => <span key={item.media_id}>{renderMedia(item, true)}</span>)}
          {option.text && <strong>{option.text}</strong>}{chosen && !ordered && <Check className={styles.check} size={19}/>}
        </button>
      </div>;
    })}</div>}

    {question.interaction === "write_text" && <div className={styles.writing}><label htmlFor={`write-${question.question_id}`}>اكتب إجابتك هنا</label><textarea id={`write-${question.question_id}`} value={text} onChange={(event) => { setText(event.target.value); setDraftState("saving"); }} maxLength={500} rows={3} inputMode="text" autoComplete="off"/><span className={draftState === "error" ? styles.draftError : ""}>{draftState === "saving" ? "جاري حفظ المسودة..." : draftState === "saved" ? "حُفظت المسودة" : draftState === "error" ? "تعذر حفظ المسودة؛ سنحاول عند التعديل التالي" : "لا تحتاج إلى كتابة الحركات غير المطلوبة"}</span></div>}

    {question.interaction === "read_aloud" && <div className={styles.recorder}>{!audioBlob ? <><button type="button" className={`${styles.recordButton} ${recording ? styles.recording : ""}`} onClick={recording ? stopRecording : () => void startRecording()} aria-label={recording ? "إيقاف التسجيل" : "بدء التسجيل"}>{recording ? <MicOff size={28}/> : <Mic size={28}/>}</button><p>{recording ? `جاري التسجيل… ${recordingSeconds} ث` : "اضغط ثم اقرأ بصوت واضح"}</p></> : <>{audioUrl && <audio controls src={audioUrl}/>}<button type="button" className={styles.secondary} onClick={resetRecording}><RotateCcw size={16}/> إعادة التسجيل</button><p>سيبقى التقييم معلقًا حتى يراجعه المشرف.</p></>}</div>}

    {feedback && <div className={`${styles.feedback} ${feedback.correct === false ? styles.retry : styles.accepted}`} role="status"><strong>{feedback.correct === true ? "أحسنت!" : feedback.correct === false ? "حاول مرة أخرى" : "تم الحفظ"}</strong><span>{feedback.message}</span>{feedback.retry_required && feedback.hint && <span className={styles.hint}>تلميح: {feedback.hint}</span>}</div>}
    {error && <div className={styles.error} role="alert">{error}</div>}
    <button type="button" className={styles.submit} disabled={!ready || saving || recording} onClick={() => void submit()}>{saving ? "جاري الحفظ..." : question.interaction === "read_aloud" ? "إرسال التسجيل للمراجعة" : question.interaction === "write_text" ? "إرسال الكتابة للمراجعة" : "تحقق من الإجابة"}</button>
  </section>;
}

const OPEN_INTERACTIONS = new Set<InteractionKind>(["read_aloud", "write_text"]);
