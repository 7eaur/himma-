"use client";

import { Bell } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./AdminNotifications.module.css";

interface NotificationItem { id: number | string; type: string; title: string; message: string; href: string; entity_type?: string | null; entity_id?: string | null; is_read: boolean; created_at: string; }
interface NotificationPayload { source?: string; unread_count: number; items: NotificationItem[]; }
const EMPTY: NotificationPayload = { unread_count: 0, items: [] };
const endpoint = "/api/v2/notifications";
function relativeTime(value: string) { const stamp = Date.parse(value); if (!Number.isFinite(stamp)) return ""; const minutes = Math.max(0, Math.floor((Date.now() - stamp) / 60000)); if (minutes < 1) return "الآن"; if (minutes < 60) return `منذ ${minutes} د`; const hours = Math.floor(minutes / 60); if (hours < 24) return `منذ ${hours} س`; return `منذ ${Math.floor(hours / 24)} ي`; }
function safeDestination(value: unknown): value is string {
  return typeof value === "string" && /^\/admin\/(?:v2-assessments|v2-lesson-review|v2-reviewed-recordings|students\/\d+)(?:\?[a-zA-Z0-9_=&%-]*)?$/.test(value);
}

export default function AdminNotifications() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<NotificationPayload>(EMPTY);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(true);
  const requestId = useRef(0);
  const mutation = useRef(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const refresh = useCallback(async () => {
    const id = ++requestId.current;
    if (mounted.current) setLoading(true);
    try {
      const response = await fetch(`${endpoint}?limit=24`, { cache: "no-store" });
      const payload = await response.json().catch(() => null);
      if (!response.ok || !payload || !Array.isArray(payload.items) || payload.source !== "himma_v2_attention") throw new Error("تعذر تحميل الإشعارات. أعد المحاولة.");
      if (mounted.current && id === requestId.current) { setData(payload); setError(""); }
    } catch (caught) {
      if (mounted.current && id === requestId.current) { setData(EMPTY); setError(caught instanceof Error ? caught.message : "تعذر تحميل الإشعارات"); }
    } finally { if (mounted.current && id === requestId.current) setLoading(false); }
  }, []);
  useEffect(() => {
    mounted.current = true;
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), 30000);
    return () => { mounted.current = false; requestId.current += 1; window.clearTimeout(initial); window.clearInterval(timer); };
  }, [refresh]);
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => { if (event.key === "Escape") { setOpen(false); trigger.current?.focus(); } };
    const outside = (event: PointerEvent) => { if (event.target instanceof Node && !root.current?.contains(event.target)) setOpen(false); };
    document.addEventListener("keydown", dismiss); document.addEventListener("pointerdown", outside);
    return () => { document.removeEventListener("keydown", dismiss); document.removeEventListener("pointerdown", outside); };
  }, [open]);
  const saveRead = async (item?: NotificationItem) => {
    if (mutation.current) return;
    const destination = item?.href;
    if (item && !safeDestination(destination)) { setError("رابط الإشعار غير صالح."); return; }
    mutation.current = true; setBusy(true); setError("");
    // Invalidate any older poll before updating the durable read marker.
    requestId.current += 1;
    try {
      if (!item || !item.is_read) {
        const response = await fetch(item ? `${endpoint}/${encodeURIComponent(item.id)}/read` : `${endpoint}/read-all`, { method: "POST" });
        if (!response.ok) throw new Error("تعذر حفظ حالة القراءة. أعد المحاولة أو حدّث القائمة.");
      }
      await refresh();
      if (item && safeDestination(destination)) { setOpen(false); router.push(destination); }
    } catch (caught) { if (mounted.current) setError(caught instanceof Error ? caught.message : "تعذر حفظ القراءة"); }
    finally { mutation.current = false; if (mounted.current) setBusy(false); }
  };
  return <div className={styles.root} ref={root}>
    {open && <button className={styles.scrim} aria-label="إغلاق الإشعارات" onClick={() => setOpen(false)} />}
    <button ref={trigger} className={styles.trigger} aria-label="الإشعارات" aria-expanded={open} onClick={() => { setOpen(value => !value); void refresh(); }}><Bell size={20} aria-hidden="true" />{data.unread_count > 0 && <span className={styles.badge}>{data.unread_count > 99 ? "99+" : data.unread_count}</span>}</button>
    {open && <div className={styles.popover} role="dialog" aria-label="إشعارات المشرف" aria-busy={busy || loading}>
      <div className={styles.header}><strong>إشعارات V2</strong>{data.unread_count > 0 && <button className={styles.markAll} disabled={busy || loading} onClick={() => void saveRead()}>تحديد الكل كمقروء</button>}</div>
      <div className={styles.header}><button className={styles.markAll} disabled={busy || loading} onClick={() => void refresh()}>تحديث</button></div>
      {error && <div role="alert" className={styles.error}>{error}</div>}
      <div className={styles.list}>{loading ? <div role="status" className={styles.empty}>جاري تحميل الإشعارات...</div> : error && data.items.length === 0 ? null : data.items.length === 0 ? <div className={styles.empty}>لا توجد إشعارات تحتاج انتباهك الآن.</div> : data.items.map(item => <button key={item.id} disabled={busy} className={`${styles.item} ${item.is_read ? "" : styles.unread}`} onClick={() => void saveRead(item)}><span className={styles.itemTop}><span className={styles.itemTitle}>{item.title}</span>{!item.is_read && <span className={styles.dot} />}</span><span className={styles.message}>{item.message}</span><span className={styles.time}>{relativeTime(item.created_at)}</span></button>)}</div>
    </div>}
  </div>;
}
