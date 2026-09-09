"use client";

import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import styles from "./StudentActivityStateBoundary.module.css";

type LearningNavigationState = {
  navigation_state?: "awaiting_audio_review" | "rerecord_available";
};

export default function StudentActivityStateBoundary({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const sessionId = String(params?.id || "");
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    let active = true;
    const check = async () => {
      try {
        const response = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" });
        if (!response.ok || !active) return;
        const data = await response.json() as LearningNavigationState | null;
        if (data?.navigation_state === "rerecord_available") {
          setRedirecting(true);
          router.replace("/student");
        }
      } catch {
        // The activity page owns recoverable network errors.
      }
    };
    void check();
    return () => { active = false; };
  }, [router, sessionId]);

  if (!redirecting) return children;

  return (
    <main className={styles.page} dir="rtl" data-testid="activity-rerecord-redirect">
      <Image src="/brand/logo-navy.svg" alt="هِمّة" width={126} height={44} priority />
      <h1>مهمة إعادة التسجيل جاهزة في مسارك</h1>
      <p>يمكنك فتحها بنفسك من صفحة مسارك عندما تكون مستعدًا.</p>
    </main>
  );
}
