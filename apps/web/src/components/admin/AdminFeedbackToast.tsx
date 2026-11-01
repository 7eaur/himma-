"use client";

import { useEffect } from "react";
import { AlertCircle, CheckCircle2, X } from "lucide-react";
// Use the exact visual and accessibility treatment of the existing global
// feedback layer. Settings and learner profiles keep local dismiss controls,
// but must not display a second visual notification system.
import styles from "@/components/GlobalFeedback.module.css";

export type AdminFeedback = { kind: "success" | "error"; text: string };

export default function AdminFeedbackToast({ feedback, onDismiss }: { feedback: AdminFeedback; onDismiss: () => void }) {
  const visible = Boolean(feedback.text);
  useEffect(() => {
    if (!visible || feedback.kind !== "success") return;
    const timeout = window.setTimeout(onDismiss, 4200);
    return () => window.clearTimeout(timeout);
  }, [feedback.kind, feedback.text, onDismiss, visible]);
  if (!visible) return null;
  const Icon = feedback.kind === "success" ? CheckCircle2 : AlertCircle;
  return <div className={styles.host} dir="rtl" data-testid="admin-feedback-toast">
    <div className={`${styles.toast} ${styles[feedback.kind]}`}
      role={feedback.kind === "error" ? "alert" : "status"}
      aria-live={feedback.kind === "error" ? "assertive" : "polite"}>
      <Icon size={23} aria-hidden="true" className={styles.icon} />
      <span className={styles.message}>{feedback.text}</span>
      <button type="button" className={styles.dismiss} aria-label="إغلاق الإشعار"
        onClick={event => { event.stopPropagation(); onDismiss(); }}>
        <X size={19} aria-hidden="true" />
      </button>
    </div>
  </div>;
}
