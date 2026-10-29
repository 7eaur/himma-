"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, MicOff, RefreshCw, RotateCcw } from "lucide-react";

interface RetryItem {
  task_id: number; kind: "lesson" | "assessment"; session_id: number;
  question_id: string; status: "requested" | "submitted";
  request_kind: "rerecord"; reason: string; prompt: string;
  stimulus: { text: string };
  staged_audio?: {
    audio_storage_key: string; audio_file_size: number;
    audio_mime_type: string; audio_duration_seconds: number | null;
  } | null;
}

function newKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `p08-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function RetryCard({ task, onSaved }: { task: RetryItem; onSaved: () => void }) {
  const [recording, setRecording] = useState(false);
  const [requestingMic, setRequestingMic] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  // Derive recovery state from the server's latest response, avoiding effect-
  // driven React state updates and retaining a successful local upload until
  // the next refresh. Never persist the student's raw recording in storage.
  const [uploadedAudio, setUploadedAudio] = useState<RetryItem["staged_audio"]>(null);
  const stagedAudio = uploadedAudio ?? task.staged_audio ?? null;
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submitPendingRef = useRef(false);
  const [error, setError] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const mountedRef = useRef(false);
  const micRequestIdRef = useRef(0);
  const micPendingRef = useRef(false);
  const chunksRef = useRef<Blob[]>([]);
  const startedAt = useRef(0);
  const uploadKey = useRef(newKey());
  const submitKey = useRef(newKey());

  // Microphone lifetime belongs to this card, never to the playback URL.
  // A late getUserMedia permission after navigation must close its stream.
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      micRequestIdRef.current += 1;
      micPendingRef.current = false;
      const recorder = recorderRef.current;
      if (recorder) {
        recorder.ondataavailable = null;
        recorder.onstop = null;
        recorder.onerror = null;
        if (recorder.state !== "inactive") {
          try { recorder.stop(); } catch { /* Tracks still close below. */ }
        }
        recorder.stream.getTracks().forEach((track) => track.stop());
        recorderRef.current = null;
      }
    };
  }, []);
  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  const startRecording = async () => {
    if (busy || recording || micPendingRef.current) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("متصفحك لا يدعم التسجيل؛ افتح الموقع في متصفح يدعم الميكروفون."); return;
    }
    const requestId = ++micRequestIdRef.current;
    micPendingRef.current = true;
    setRequestingMic(true);
    setError("");
    let openedStream: MediaStream | null = null;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      openedStream = stream;
      if (!mountedRef.current || requestId !== micRequestIdRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      const supported = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm"].find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = supported ? new MediaRecorder(stream, { mimeType: supported }) : new MediaRecorder(stream);
      // New audio is a new submission: never reuse the old audio idempotency key.
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
      setAudioBlob(null);
      setUploadedAudio(null);
      uploadKey.current = newKey();
      submitKey.current = newKey();
      chunksRef.current = [];
      let recorderFailed = false;
      recorder.ondataavailable = (event) => {
        if (mountedRef.current && recorderRef.current === recorder && event.data.size) chunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        recorderFailed = true;
        stream.getTracks().forEach((track) => track.stop());
        if (!mountedRef.current || recorderRef.current !== recorder) return;
        recorderRef.current = null;
        recorder.onstop = null;
        chunksRef.current = [];
        setRecording(false);
        setError("حدث خطأ أثناء التسجيل. حاول مرة أخرى بعد التحقق من إذن الميكروفون.");
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        if (!mountedRef.current || recorderRef.current !== recorder || recorderFailed) return;
        recorderRef.current = null;
        const mimeType = recorder.mimeType || chunksRef.current[0]?.type || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (!blob.size || blob.size > 10 * 1024 * 1024) {
          // Recording may fail after permission succeeds: never leave the
          // child's microphone stream running on an empty/oversize file.
          stream.getTracks().forEach((track) => track.stop());
          setError("التسجيل فارغ أو تجاوز الحجم المسموح (10 ميجابايت). سجّل قراءة أقصر.");
          return;
        }
        setAudioBlob(blob);
        setAudioUrl((previous) => { if (previous) URL.revokeObjectURL(previous); return URL.createObjectURL(blob); });
        stream.getTracks().forEach((track) => track.stop());
        setSeconds(Math.max(1, Math.ceil((Date.now() - startedAt.current) / 1000)));
      };
      recorder.start();
      recorderRef.current = recorder;
      startedAt.current = Date.now();
      setRecording(true);
    } catch {
      // Some browsers grant a MediaStream but reject MediaRecorder.start().
      // Release the microphone even when setup fails after permission.
      openedStream?.getTracks().forEach((track) => track.stop());
      if (mountedRef.current && requestId === micRequestIdRef.current) {
        setRecording(false);
        setError("تعذر تشغيل الميكروفون. تحقق من إذنه ثم حاول مجددًا.");
      }
    } finally {
      if (mountedRef.current && requestId === micRequestIdRef.current) {
        micPendingRef.current = false;
        setRequestingMic(false);
      }
    }
  };

  const stopRecording = () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    setRecording(false);
  };

  const submit = async () => {
    if (submitPendingRef.current || busy || recording) return;
    submitPendingRef.current = true;
    setBusy(true); setError("");
    try {
      let answer: Record<string, unknown>;
      if (!audioBlob && !stagedAudio) throw new Error("سجل قراءتك أولًا");
      // If S3 already accepted this exact recording, a failed submit should
      // retry only the academic POST, never re-upload the child’s voice.
      if (audioBlob && !uploadedAudio) {
        const form = new FormData();
        form.append("file", audioBlob, audioBlob.type.includes("mp4") ? "v2-retry.m4a" : "v2-retry.webm");
        form.append("duration_seconds", String(Math.max(1, seconds)));
        const response = await fetch(`/api/v2/retries/student/tasks/${task.task_id}/recording`, {
          method: "POST", headers: { "Idempotency-Key": uploadKey.current }, body: form,
        });
        const payload = await response.json().catch(() => null);
        if (!response.ok) throw new Error(payload?.detail || "تعذر رفع التسجيل");
        answer = payload;
        setUploadedAudio(payload);
      } else {
        if (!stagedAudio?.audio_duration_seconds) throw new Error("مدة التسجيل غير محفوظة. يُرجى إعادة التسجيل.");
        answer = stagedAudio;
      }
      const response = await fetch(`/api/v2/retries/student/tasks/${task.task_id}/submit`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ submit_key: submitKey.current, ...answer }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.detail || "تعذر إرسال النسخة الجديدة");
      onSaved();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر إكمال الإعادة"); }
    finally { submitPendingRef.current = false; setBusy(false); }
  };

  return <section className="space-y-3 rounded-2xl border border-amber-300 bg-amber-50/70 p-4" aria-label="إعادة الدليل">
    <div><strong className="text-slate-900">طلب من المشرف: إعادة القراءة</strong>
      <p className="mt-1 text-sm text-slate-700">{task.prompt}</p>
      <p data-testid="retry-original-stimulus" className="mt-3 rounded-xl bg-white p-3 text-center text-xl font-bold leading-loose text-slate-950" dir="rtl">{task.stimulus.text}</p>
      <p className="mt-2 text-sm text-amber-900">ملاحظة المشرف: {task.reason}</p></div>
    <div className="space-y-2">
        {!audioBlob
          ? <button type="button" disabled={busy || requestingMic} onClick={recording ? stopRecording : () => void startRecording()}
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-blue-800 px-4 py-2 font-semibold text-white disabled:opacity-50">
              {recording ? <MicOff size={19}/> : <Mic size={19}/>}
              {requestingMic ? "جارٍ تشغيل الميكروفون..." : recording ? "إيقاف التسجيل" : "تسجيل القراءة من جديد"}</button>
          : <><audio controls src={audioUrl || undefined} className="w-full"/>
            <button type="button" disabled={busy || requestingMic || recording} onClick={() => {
               setAudioBlob(null);
              setUploadedAudio(null);
              if (audioUrl) URL.revokeObjectURL(audioUrl);
              setAudioUrl(null);
              uploadKey.current = newKey();
              submitKey.current = newKey();
            }}
              className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-slate-400 px-3 py-2 text-sm disabled:opacity-50"><RotateCcw size={16}/> إعادة المحاولة</button></>}
        {stagedAudio && !audioBlob && <p role="status" className="text-sm text-emerald-700">
          التسجيل السابق محفوظ في الخدمة. يمكنك إرسال النسخة دون رفعها مرة أخرى، أو إعادة التسجيل.
        </p>}
        <p className="text-sm text-slate-700">القراءة الجديدة ستظل بانتظار مراجعة المشرف، ولن تُحتسب نتيجة تلقائية.</p>
      </div>
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
    <button type="button" disabled={busy || requestingMic || recording || (!audioBlob && !stagedAudio)}
      onClick={() => void submit()} aria-busy={busy} className="min-h-11 rounded-xl bg-emerald-700 px-5 py-2 font-semibold text-white disabled:opacity-40">
      {busy ? "جاري حفظ الدليل..." : "إرسال الإجابة الجديدة للمراجعة"}</button>
  </section>;
}

export default function StudentRetryTasks({ kind, sessionId, taskId, dashboard = false }: { kind?: "lesson" | "assessment"; sessionId?: number; taskId?: number; dashboard?: boolean }) {
  const [tasks, setTasks] = useState<RetryItem[]>([]);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(true);
  const requestSequence = useRef(0);
  const load = useCallback(async () => {
    const sequence = ++requestSequence.current;
    try {
      const allTasks: RetryItem[] = [];
      let nextOffset: number | null = 0;
      // A student may have open review evidence from multiple finished lessons.
      // Never silently truncate the queue to the first 50 most recent tasks.
      for (let page = 0; nextOffset !== null && page < 30; page += 1) {
        const offset: number = nextOffset;
        const response = await fetch(`/api/v2/retries/student/tasks?limit=100&offset=${offset}`, { cache: "no-store" });
        const payload = await response.json().catch(() => null);
        if (!response.ok) throw new Error(payload?.detail || "تعذر تحميل طلبات الإعادة");
        if (sequence !== requestSequence.current) return;
        if (!Array.isArray(payload?.items)) throw new Error("قائمة الإعادات غير صالحة");
        if (payload.items.some((item: RetryItem) => item.request_kind !== "rerecord")) {
          throw new Error("توجد مهمة غير متوافقة مع مراجعة القراءة؛ تواصل مع المشرف.");
        }
        // Deployments may temporarily serve different Web/API revisions.
        // A missing source text must fail closed with guidance, never crash or
        // let a child record from a substitute question.
        if (payload.items.some((item: RetryItem) => typeof item.stimulus?.text !== "string" || !item.stimulus.text.trim())) {
          throw new Error("تعذر عرض النص الأصلي لطلب الإعادة. حدّث الصفحة، وإذا استمرت المشكلة تواصل مع المشرف.");
        }
        allTasks.push(...(payload.items as RetryItem[]));
        const following: unknown = payload.next_offset ?? null;
        if (following !== null && (!Number.isSafeInteger(following) || (following as number) <= offset)) {
          throw new Error("تعذر استكمال قائمة الإعادات");
        }
        nextOffset = following as number | null;
      }
      if (nextOffset !== null) throw new Error("قائمة الإعادات كبيرة جدًا، أعد تحميل الصفحة");
      if (sequence !== requestSequence.current) return;
      setTasks(allTasks.filter((item) =>
        (kind === undefined || item.kind === kind) &&
        (sessionId === undefined || item.session_id === sessionId) &&
        (taskId === undefined || item.task_id === taskId)
      ));
      setError("");
    } catch (reason) {
      if (sequence === requestSequence.current) {
        setError(reason instanceof Error ? reason.message : "تعذر تحميل الإعادات");
      }
    } finally {
      if (sequence === requestSequence.current) setLoading(false);
    }
  }, [kind, sessionId, taskId]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    const onOnline = () => { void load(); };
    const onVisibility = () => {
      if (document.visibilityState === "visible") void load();
    };
    window.addEventListener("online", onOnline);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("online", onOnline);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [load]);

  const requested = tasks.filter((task) => task.status === "requested");
  const submitted = tasks.filter((task) => task.status === "submitted");
  // The student dashboard must not show an empty review card: it pushes the
  // learning journey below the viewport despite no actionable review request.
  if (taskId !== undefined && loading && !error) {
    return <p role="status" className="rounded-xl border border-blue-100 bg-white p-5 text-center text-slate-700">جارٍ فتح طلب إعادة القراءة…</p>;
  }
  if (taskId !== undefined && !loading && !error && tasks.length === 0 && !sent) {
    return <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
      <p role="status" className="font-semibold text-slate-800">طلب القراءة لم يعد متاحًا للإعادة. قد يكون المشرف راجعه أو تغيرت حالته.</p>
      <button type="button" onClick={() => { setLoading(true); void load(); }} className="min-h-11 rounded-xl border border-blue-300 px-4 py-2 font-bold text-blue-800">تحديث الطلب</button>
    </section>;
  }
  if (dashboard && tasks.length === 0 && !sent) {
    if (!error) return null;
    // On a failed request the inbox is unknown, not confirmed empty.
    // Keep retry available without falsely claiming the student has no tasks.
    return <div role="alert" className="mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      <span>تعذر تحديث طلبات المشرف: {error}</span>
      <button type="button" onClick={() => void load()} className="rounded-lg border border-amber-400 px-3 py-1.5 font-semibold">
        إعادة المحاولة
      </button>
    </div>;
  }
  return <section className={dashboard
    ? "mt-3 space-y-3 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5"
    : "mt-4 space-y-3"} dir="rtl" data-testid={dashboard ? "v2-active-retry-tasks" : undefined}>
    {dashboard && <>
      <h2 className="text-lg font-bold text-slate-900">طلبات إعادة القراءة</h2>
      <p className="text-sm text-slate-600">إذا طلب المشرف إعادة تسجيل قراءة سابقة، يظهر الطلب هنا ولو أكملت الدرس. لا تُحسب نتيجة القراءة قبل مراجعة التسجيل.</p>
    </>}
    <button type="button" className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm"
      onClick={() => void load()}><RefreshCw size={15}/> تحديث طلبات المشرف</button>
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
    {sent && <p role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">وصلت إجابتك الجديدة؛ بانتظار قرار المشرف.</p>}
    {submitted.length > 0 && <p role="status" className="rounded-lg border border-blue-200 p-3 text-sm">لديك {submitted.length} إجابة جديدة وصلت وتنتظر المراجعة.</p>}
    {requested.map((task) => <RetryCard key={task.task_id} task={task} onSaved={() => { setSent(true); void load(); }}/>)}
  </section>;
}
