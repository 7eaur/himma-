"use client";

import { useEffect } from "react";
import { CheckCircle2, X, XCircle } from "lucide-react";
import styles from "./AdminFeedbackToast.module.css";

export type AdminFeedback = { kind: "success" | "error"; text: string };

export default function AdminFeedbackToast({ feedback, onDismiss }: { feedback: AdminFeedback; onDismiss: () => void }) {
  const visible = Boolean(feedback.text);

  useEffect(() => {
    if (!visible) return;
    // Errors need to remain readable and actionable, including for keyboard
    // and screen-reader users. Successful acknowledgements can time out.
    if (feedback.kind !== "success") return;
    const timeout = window.setTimeout(onDismiss, 3200);
    return () => window.clearTimeout(timeout);
  }, [feedback.kind, feedback.text, onDismiss, visible]);

  if (!visible) return null;

  const Icon = feedback.kind === "success" ? CheckCircle2 : XCircle;
  return (
    <div className={styles.root}>
      <div
        className={`${styles.toast} ${feedback.kind === "success" ? styles.success : styles.error}`}
        role={feedback.kind === "error" ? "alert" : "status"}
        aria-live={feedback.kind === "error" ? "assertive" : "polite"}
        data-testid="admin-feedback-toast"
      >
        <Icon className={styles.icon} size={19} aria-hidden="true" />
        <span className={styles.text}>{feedback.text}</span>
        <button type="button" className={styles.close} aria-label="إغلاق الإشعار" onClick={(event) => { event.stopPropagation(); onDismiss(); }}>
          <X size={17} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
