"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import V2StudentDashboard, { type StudentV2Home } from "./V2StudentDashboard";

/**
 * A learner has ONE visible product: Himma V2.
 * Historical V1 evidence remains in the database and staff-only routes,
 * but no V1 student endpoints, rewards or components are reachable here.
 */
export default function StudentHomePage() {
  const { replace } = useRouter();
  const [home, setHome] = useState<StudentV2Home | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await fetch("/api/v2/student/home", { cache: "no-store" });
        if (cancelled) return;
        if (response.status === 401 || response.status === 403) {
          replace("/student/login");
          return;
        }
        if (!response.ok) {
          throw new Error("رحلة هِمّة غير متاحة الآن. تقدّمك محفوظ، حاول مرة أخرى لاحقًا.");
        }
        const payload = await response.json().catch(() => null) as StudentV2Home | null;
        if (!payload?.student || !payload.current_action || !payload.progress || payload.mode !== "v2") {
          throw new Error("تعذر التحقق من رحلة هِمّة. تواصل مع المشرف، ولا تبدأ اختبارًا جديدًا.");
        }
        if (!cancelled) setHome(payload);
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "تعذر الاتصال بالخادم.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [replace, reload]);

  if (home) return <V2StudentDashboard home={home} />;
  if (loading) {
    return <main dir="rtl" className="min-h-screen flex items-center justify-center">
      <p role="status" className="text-muted">جاري تحميل رحلتك...</p>
    </main>;
  }
  return <main dir="rtl" className="min-h-screen flex items-center justify-center p-6">
    <section role="alert" className="card text-center max-w-md w-full p-8 space-y-4">
      <h1 className="font-bold text-navy text-xl">تعذر فتح رحلة هِمّة</h1>
      <p>{error || "تعذر التحقق من بيانات الرحلة."}</p>
      <button className="btn-primary" type="button"
        onClick={() => { setLoading(true); setError(""); setReload(value => value + 1); }}>
        إعادة المحاولة
      </button>
    </section>
  </main>;
}
