"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, MicOff, RefreshCw, RotateCcw } from "lucide-react";

interface RetryItem {
  task_id: number; kind: "lesson" | "assessment"; session_id: number;
  question_id: string; status: "requested" | "submitted";
  request_kind: "rerecord" | "rewrite"; reason: string; prompt: string;
}

function newKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `p08-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function RetryCard({ task, onSaved }: { task: RetryItem; onSaved: () => void }) {
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAt = useRef(0);
  const uploadKey = useRef(newKey());
  const submitKey = useRef(newKey());

  useEffect(() => () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    recorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("متصفحك لا يدعم التسجيل؛ افتح الموقع في متصفح يدعم الميكروفون."); return;
    }
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const supported = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm"].find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = supported ? new MediaRecorder(stream, { mimeType: supported }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl((previous) => { if (previous) URL.revokeObjectURL(previous); return URL.createObjectURL(blob); });
        stream.getTracks().forEach((track) => track.stop());
        setSeconds(Math.max(1, Math.ceil((Date.now() - startedAt.current) / 1000)));
      };
      recorder.start();
      recorderRef.current = recorder;
      startedAt.current = Date.now();
      setRecording(true);
    } catch { setError("تعذر الوصول إلى الميكروفون. اسمح بالتسجيل ثم حاول مجددًا."); }
  };

  const stopRecording = () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    setRecording(false);
  };

  const submit = async () => {
    if (busy || recording) return;
    setBusy(true); setError("");
    try {
      let answer: Record<string, unknown>;
      if (task.request_kind === "rewrite") {
        const value = text.trim();
        if (!value) throw new Error("اكتب إجابتك قبل الإرسال");
        answer = { text_response: value };
      } else {
        if (!audioBlob) throw new Error("سجل قراءتك أولًا");
        const form = new FormData();
        form.append("file", audioBlob, audioBlob.type.includes("mp4") ? "v2-retry.m4a" : "v2-retry.webm");
        const response = await fetch(`/api/v2/retries/student/tasks/${task.task_id}/recording`, {
          method: "POST", headers: { "Idempotency-Key": uploadKey.current }, body: form,
        });
        const payload = await response.json().catch(() => null);
        if (!response.ok) throw new Error(payload?.detail || "تعذر رفع التسجيل");
        answer = { ...payload, audio_duration_seconds: Math.max(1, seconds) };
      }
      const response = await fetch(`/api/v2/retries/student/tasks/${task.task_id}/submit`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ submit_key: submitKey.current, ...answer }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.detail || "تعذر إرسال النسخة الجديدة");
      onSaved();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر إكمال الإعادة"); }
    finally { setBusy(false); }
  };

  return <section className="space-y-3 rounded-2xl border border-amber-300 bg-amber-50/70 p-4" aria-label="إعادة الدليل">
    <div><strong className="text-slate-900">طلب جديد من المشرف: {task.request_kind === "rerecord" ? "إعادة القراءة" : "إعادة الكتابة"}</strong>
      <p className="mt-1 text-sm text-slate-700">{task.prompt}</p>
      <p className="mt-2 text-sm text-amber-900">ملاحظة المشرف: {task.reason}</p></div>
    {task.request_kind === "rewrite"
      ? <div><label className="block text-sm font-semibold" htmlFor={`retry-write-${task.task_id}`}>إجابتك الجديدة</label>
        <textarea id={`retry-write-${task.task_id}`} value={text} maxLength={500} rows={3}
          onChange={(event) => setText(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-3" /></div>
      : <div className="space-y-2">
        {!audioBlob
          ? <button type="button" disabled={busy} onClick={recording ? stopRecording : () => void startRecording()}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-800 px-4 py-2 font-semibold text-white disabled:opacity-50">
              {recording ? <MicOff size={19}/> : <Mic size={19}/>}
              {recording ? "إيقاف التسجيل" : "تسجيل القراءة من جديد"}</button>
          : <><audio controls src={audioUrl || undefined} className="w-full"/>
            <button type="button" onClick={() => { setAudioBlob(null); if (audioUrl) URL.revokeObjectURL(audioUrl); setAudioUrl(null); uploadKey.current = newKey(); }}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-400 px-3 py-2 text-sm"><RotateCcw size={16}/> إعادة المحاولة</button></>}
        <p className="text-sm text-slate-700">القراءة الجديدة ستظل بانتظار مراجعة المشرف، ولن تُحتسب نتيجة تلقائية.</p>
      </div>}
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
    <button type="button" disabled={busy || recording || (task.request_kind === "rewrite" ? !text.trim() : !audioBlob)}
      onClick={() => void submit()} className="rounded-xl bg-emerald-700 px-5 py-2 font-semibold text-white disabled:opacity-40">
      {busy ? "جاري حفظ الدليل..." : "إرسال الإجابة الجديدة للمراجعة"}</button>
  </section>;
}

export default function StudentRetryTasks({ kind, sessionId }: { kind?: "lesson" | "assessment"; sessionId?: number }) {
  const [tasks, setTasks] = useState<RetryItem[]>([]);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/v2/retries/student/tasks", { cache: "no-store" });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.detail || "تعذر تحميل طلبات الإعادة");
      setTasks((payload.items as RetryItem[]).filter((item) =>
        (kind === undefined || item.kind === kind) &&
        (sessionId === undefined || item.session_id === sessionId)
      ));
      setError("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر تحميل الإعادات"); }
  }, [kind, sessionId]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const requested = tasks.filter((task) => task.status === "requested");
  const submitted = tasks.filter((task) => task.status === "submitted");
  return <div className="mt-4 space-y-3" dir="rtl">
    <button type="button" className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm"
      onClick={() => void load()}><RefreshCw size={15}/> تحديث طلبات المشرف</button>
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
    {sent && <p role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">وصلت إجابتك الجديدة؛ بانتظار قرار المشرف.</p>}
    {submitted.length > 0 && <p role="status" className="rounded-lg border border-blue-200 p-3 text-sm">لديك {submitted.length} إجابة جديدة وصلت وتنتظر المراجعة.</p>}
    {requested.map((task) => <RetryCard key={task.task_id} task={task} onSaved={() => { setSent(true); void load(); }}/>)}
  </div>;
}
