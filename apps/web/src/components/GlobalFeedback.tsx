"use client";

import { useEffect, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { FEEDBACK_EVENT, type FeedbackEvent } from "@/lib/feedback";
import styles from "./GlobalFeedback.module.css";

/** One accessible feedback layer across supervisor and student routes. */
export default function GlobalFeedback() {
  const [feedback, setFeedback] = useState<FeedbackEvent | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handle = (event: Event) => setFeedback((event as CustomEvent<FeedbackEvent>).detail);
    window.addEventListener(FEEDBACK_EVENT, handle);
    return () => window.removeEventListener(FEEDBACK_EVENT, handle);
  }, []);

  useEffect(() => {
    if (!feedback || feedback.kind === "error") return;
    const timer = window.setTimeout(() => setFeedback(current =>
      current?.id === feedback.id ? null : current
    ), feedback.kind === "success" ? 4200 : 5500);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  // Native dialogs occupy the browser top layer. Show notifications there too
  // so a review prerequisite warning is not hidden behind the modal on Safari.
  useEffect(() => {
    const node = popoverRef.current;
    if (!node || !feedback || typeof node.showPopover !== "function") return;
    try { node.showPopover(); } catch { /* CSS fixed-position fallback. */ }
    return () => { try { node.hidePopover(); } catch { /* Already closed. */ } };
  }, [feedback]);

  if (!feedback) return null;
  const Icon = feedback.kind === "success" ? CheckCircle2 :
    feedback.kind === "error" ? AlertCircle : Info;
  return <div ref={popoverRef} popover="manual" className={styles.host} dir="rtl" data-testid="himma-feedback-host">
    <div className={`${styles.toast} ${styles[feedback.kind]}`}
      role={feedback.kind === "error" ? "alert" : "status"}
      aria-live={feedback.kind === "error" ? "assertive" : "polite"}>
      <Icon size={23} aria-hidden="true" className={styles.icon} />
      <span className={styles.message}>{feedback.text}</span>
      <button type="button" className={styles.dismiss} aria-label="إغلاق الإشعار"
        onClick={() => setFeedback(null)}><X size={19} aria-hidden="true" /></button>
    </div>
  </div>;
}
