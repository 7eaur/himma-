"use client";

import { useEffect, useState } from "react";
import { SkipForward } from "lucide-react";
import styles from "./DevelopmentAudioSkipAction.module.css";

type Props = {
  sessionId: string;
  itemId: number;
  stepId: number;
  isRecording: boolean;
  onSkipped: () => void | Promise<void>;
};

export default function DevelopmentAudioSkipAction({ sessionId, itemId, stepId, isRecording, onSkipped }: Props) {
  const [enabled, setEnabled] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/runtime-flags", { cache: "no-store" })
      .then(async (response) => response.ok ? response.json() : null)
      .then((data) => {
        if (!cancelled) setEnabled(Boolean(data?.temporary_audio_skip));
      })
      .catch(() => {
        if (!cancelled) setEnabled(false);
      });
    return () => { cancelled = true; };
  }, []);

  const skip = async () => {
    if (submitting) return;
    if (isRecording) {
      setMessage("أوقف التسجيل الحالي أولًا، ثم استخدم التخطي المؤقت.");
      return;
    }

    setSubmitting(true);
    setMessage("");
    try {
      const response = await fetch(`/api/temporary-audio/session/${sessionId}/attempt/${itemId}/skip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({ step_id: stepId, elapsed_seconds: 0 }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تخطي مهمة التسجيل");
      await onSkipped();
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "تعذر تخطي مهمة التسجيل");
    } finally {
      setSubmitting(false);
    }
  };

  if (!enabled) return null;

  return (
    <div className={styles.root} data-testid="development-audio-skip">
      <button className={styles.button} type="button" onClick={() => void skip()} disabled={submitting}>
        <SkipForward size={18} aria-hidden="true" />
        {submitting ? "جاري التخطي..." : "تخطي مؤقتًا"}
      </button>
      <p className={styles.help}>هذا الخيار متاح في بيئة التطوير فقط ولا ينشئ درجة أو تسجيلًا أو دليل إتقان.</p>
      {message && <p className={styles.message} role="status" aria-live="polite">{message}</p>}
    </div>
  );
}
