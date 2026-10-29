export type FeedbackKind = "success" | "error" | "warning";
export interface FeedbackEvent { kind: FeedbackKind; text: string; id: number }
export const FEEDBACK_EVENT = "himma:feedback";
let nextId = 0;

/** Session-local notification, no persisted user information. */
export function notifyFeedback(kind: FeedbackKind, text: string): void {
  if (typeof window === "undefined" || !text.trim()) return;
  window.dispatchEvent(new CustomEvent<FeedbackEvent>(FEEDBACK_EVENT, {
    detail: { kind, text: text.trim(), id: ++nextId },
  }));
}
