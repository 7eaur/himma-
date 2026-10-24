"use client";

import { useState } from "react";
import { LockKeyhole, LockKeyholeOpen } from "lucide-react";

type ReviewKind = "lesson" | "assessment";

/** Optional short human-review lease: locking stays authoritative on the API. */
export default function SupervisorClaimActions({ kind, responseId }: {
  kind: ReviewKind; responseId: number;
}) {
  const [claimed, setClaimed] = useState(false);
  const [expires, setExpires] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const change = async () => {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v2/review-claims/admin/${kind}/${responseId}/claim`, {
        method: claimed ? "DELETE" : "POST",
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.detail || "تعذر تحديث حجز المراجعة");
      setClaimed(!claimed);
      setExpires(payload.expires_at || "");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر تحديث حجز المراجعة");
    } finally {
      setBusy(false);
    }
  };

  return <div className="flex flex-wrap items-center gap-2">
    <button type="button" disabled={busy} onClick={() => void change()}
      className="inline-flex items-center gap-2 rounded-lg border border-slate-400 px-3 py-2 text-sm font-semibold disabled:opacity-40">
      {claimed ? <LockKeyholeOpen size={16} aria-hidden="true"/> : <LockKeyhole size={16} aria-hidden="true"/>}
      {claimed ? "تحرير الحجز" : "حجز المراجعة 10 دقائق"}
    </button>
    {claimed && <span role="status" className="text-xs text-slate-600">الحجز لك حتى {expires ? new Date(expires).toLocaleTimeString("ar") : "نهاية المدة المحددة"}</span>}
    {error && <span role="alert" className="text-xs text-rose-700">{error}</span>}
  </div>;
}
