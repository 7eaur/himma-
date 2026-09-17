"use client";

import { useEffect } from "react";
import { CheckCircle2, X, XCircle } from "lucide-react";
import styles from "./AdminFeedbackToast.module.css";

export type AdminFeedback = { kind: "success" | "error"; text: string };

export default function AdminFeedbackToast({ feedback, onDismiss }: { feedback: AdminFeedback; onDismiss: () => void }) {
  const visible = Boolean(feedback.text);

  useEffect(() => {
    if (!visible) return;
    const timeout = window.setTimeout(onDismiss, feedback.kind === "success" ? 3200 : 5200);
    const dismissOnNextPointer = () => onDismiss();
    const armPointerDismiss = window.setTimeout(() => {
      document.addEventListener("pointerdown", dismissOnNextPointer, { once: true });
    }, 80);
    return () => {
      window.clearTimeout(timeout);
      window.clearTimeout(armPointerDismiss);
      document.removeEventListener("pointerdown", dismissOnNextPointer);
    };
  }, [feedback.kind, feedback.text, onDismiss, visible]);

  if (!visible) return null;

  const Icon = feedback.kind === "success" ? CheckCircle2 : XCircle;
  return (
    <div className={styles.root}>
      <div
        className={`${styles.toast} ${feedback.kind === "success" ? styles.success : styles.error}`}
        role={feedback.kind === "error" ? "alert" : "status"}
        aria-live={feedback.kind === "error" ? "assertive" : "polite"}
        onClick={onDismiss}
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
