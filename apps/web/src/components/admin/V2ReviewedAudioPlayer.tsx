"use client";

import { useState } from "react";

interface V2ReviewedAudioPlayerProps {
  id: string;
  src: string;
  audioSubmissionId: number;
  completionUrl: string;
  initiallyCompleted: boolean;
  onCompletionChange: (completed: boolean) => void;
}

export default function V2ReviewedAudioPlayer({
  id, src, audioSubmissionId, completionUrl, initiallyCompleted, onCompletionChange,
}: V2ReviewedAudioPlayerProps) {
  const [acknowledgedLocally, setAcknowledgedLocally] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const completed = initiallyCompleted || acknowledgedLocally;

  const acknowledgeCompletion = async () => {
    if (completed || saving) return;
    setSaving(true);
    setError("");
    try {
      const response = await fetch(completionUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_submission_id: audioSubmissionId }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تسجيل اكتمال تشغيل التسجيل");
      setAcknowledgedLocally(true);
      onCompletionChange(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر تسجيل اكتمال تشغيل التسجيل");
      onCompletionChange(false);
    } finally {
      setSaving(false);
    }
  };

  return <div className="space-y-1">
    <p id={`${id}-label`} className="text-sm font-semibold">استمع للتسجيل كاملًا قبل التقييم</p>
    <audio id={id} aria-labelledby={`${id}-label`} controls preload="none" src={src} onEnded={() => void acknowledgeCompletion()} className="w-full" />
    {saving && <p role="status" className="text-sm text-blue-700">جارٍ تسجيل اكتمال التشغيل...</p>}
    {completed && <p role="status" className="text-sm text-emerald-700">اكتمل الاستماع. يمكنك الآن اعتماد القراءة.</p>}
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
  </div>;
}
