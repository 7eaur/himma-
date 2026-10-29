"use client";

import { useEffect, useRef, useState } from "react";

interface V2ReviewedAudioPlayerProps {
  id: string;
  src: string;
  audioSubmissionId: number;
  completionUrl: string;
  initiallyCompleted: boolean;
  onCompletionChange: (completed: boolean) => void;
}

export default function V2ReviewedAudioPlayer(props: V2ReviewedAudioPlayerProps) {
  // Completion belongs to one recording revision, never to its reused row.
  return <RecordingPlayback key={`${props.audioSubmissionId}:${props.src}:${props.completionUrl}`} {...props} />;
}

function RecordingPlayback({
  id, src, audioSubmissionId, completionUrl, initiallyCompleted, onCompletionChange,
}: V2ReviewedAudioPlayerProps) {
  const [acknowledgedLocally, setAcknowledgedLocally] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [playbackEnded, setPlaybackEnded] = useState(false);
  const pending = useRef(false);
  const mounted = useRef(false);
  const completed = initiallyCompleted || acknowledgedLocally;

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const acknowledgeCompletion = async () => {
    if (completed || pending.current) return;
    pending.current = true;
    setSaving(true);
    try {
      const response = await fetch(completionUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_submission_id: audioSubmissionId }),
      });
      const data = await response.json().catch(() => null);
      if (!mounted.current) return;
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "تعذر تسجيل اكتمال تشغيل التسجيل");
      setError("");
      setAcknowledgedLocally(true);
      onCompletionChange(true);
    } catch (reason) {
      if (!mounted.current) return;
      setError(reason instanceof Error ? reason.message : "تعذر تسجيل اكتمال تشغيل التسجيل");
      onCompletionChange(false);
    } finally {
      pending.current = false;
      if (mounted.current) setSaving(false);
    }
  };

  return <div className="space-y-1">
    <p id={`${id}-label`} className="text-sm font-semibold">استمع للتسجيل كاملًا قبل التقييم</p>
    <audio id={id} aria-labelledby={`${id}-label`} controls preload="none" src={src} onEnded={() => {
      setPlaybackEnded(true);
      void acknowledgeCompletion();
    }} className="w-full" />
    {saving && <p role="status" className="text-sm text-blue-700">جارٍ تسجيل اكتمال التشغيل...</p>}
    {completed && <p role="status" className="text-sm text-emerald-700">اكتمل الاستماع. يمكنك الآن اعتماد القراءة.</p>}
    {error && <div role="alert" className="space-y-2 text-sm text-rose-700">
      <p>{error}</p>
      {playbackEnded && !completed && <button type="button" className="btn-secondary min-h-11" disabled={saving}
        aria-busy={saving} onClick={() => void acknowledgeCompletion()}>
        {saving ? "جارٍ تأكيد الاستماع..." : "إعادة تأكيد اكتمال الاستماع"}
      </button>}
    </div>}
  </div>;
}
