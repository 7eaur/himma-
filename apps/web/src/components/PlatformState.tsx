"use client";

import Image from "next/image";
import styles from "./PlatformState.module.css";

type Props = {
  mode?: "loading" | "error" | "empty";
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  compact?: boolean;
};

export default function PlatformState({
  mode = "loading",
  title,
  description,
  actionLabel,
  onAction,
  compact = false,
}: Props) {
  const isLoading = mode === "loading";
  const heading = title ?? (isLoading ? "لحظات ونجهز لك الصفحة" : mode === "error" ? "تعذر تحميل الصفحة" : "لا توجد بيانات للعرض");
  const detail = description ?? (isLoading ? "جارٍ تجهيز المحتوى، انتظر قليلًا." : mode === "error" ? "تحقق من اتصالك بالإنترنت، ثم حاول مرة أخرى." : "ستظهر البيانات هنا عند توفرها.");
  return (
    <section className={`${styles.shell} ${compact ? styles.compact : ""}`} dir="rtl" aria-busy={isLoading} aria-live="polite">
      <div className={styles.card} role={isLoading ? "status" : mode === "error" ? "alert" : "status"}>
        <Image src="/brand/logo-navy.svg" alt="هِمّة" width={112} height={42} className={styles.logo} priority />
        <div className={styles.symbol} aria-hidden="true">
          {isLoading ? <span className={styles.spinner} /> : mode === "error" ? "!" : "✓"}
        </div>
        <h2 className={styles.title}>{heading}</h2>
        <p className={styles.description}>{detail}</p>
        {!isLoading && onAction && <button type="button" className={styles.button} onClick={onAction}>{actionLabel ?? "إعادة المحاولة"}</button>}
      </div>
    </section>
  );
}
