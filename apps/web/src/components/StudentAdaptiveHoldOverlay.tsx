"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { CheckCircle2, Clock3, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

interface AdaptationStatus {
  ready?: boolean;
  explanation?: Record<string, unknown>;
}

export default function StudentAdaptiveHoldOverlay() {
  const router = useRouter();
  const [held, setHeld] = useState(false);
  const [checking, setChecking] = useState(false);
  const checkingRef = useRef(false);

  const poll = useCallback(async () => {
    if (checkingRef.current) return;
    checkingRef.current = true;
    try {
      const response = await fetch("/api/adaptation/status", { cache: "no-store" });
      if (!response.ok) return;
      const data: AdaptationStatus = await response.json();
      setHeld(Boolean(data.explanation?.mapping_gap));
    } catch {
      // The activity page keeps its own recoverable network handling.
    } finally {
      checkingRef.current = false;
    }
  }, []);

  const manualCheck = async () => {
    setChecking(true);
    try {
      await poll();
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    const first = window.setTimeout(() => void poll(), 0);
    const timer = window.setInterval(() => void poll(), 1800);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(timer);
    };
  }, [poll]);

  if (!held) return null;

  return (
    <div className="fixed inset-0 z-[70] overflow-y-auto bg-[#F7FBFF]/95 px-4 py-8 backdrop-blur-sm" dir="rtl" data-testid="student-adaptive-hold">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-3xl items-center justify-center">
        <section className="w-full overflow-hidden rounded-[32px] border border-[#DCE8F2] bg-white shadow-[0_25px_70px_rgba(32,54,77,.12)]">
          <div className="grid md:grid-cols-[1.1fr_.9fr]">
            <div className="flex flex-col justify-center p-7 md:p-10">
              <span className="mb-4 inline-flex w-fit items-center gap-2 rounded-full bg-[#EDF9F4] px-3 py-2 text-sm font-bold text-[#347b5b]">
                <CheckCircle2 size={17} /> أنهيت خطوتك بنجاح
              </span>
              <h1 className="text-3xl font-black leading-[1.45] text-[#20364D] md:text-4xl">أحسنت! نجهّز لك الخطوة الأنسب.</h1>
              <p className="mt-4 text-base leading-8 text-slate-600">لاحظت هِمّة أن اختيار نشاط التقوية التالي يحتاج مراجعة المشرف حتى تحصل على تدريب مناسب فعلًا، وليس نشاطًا عشوائيًا.</p>
              <div className="mt-6 flex items-start gap-3 rounded-2xl border border-[#DCE8F2] bg-[#F7FBFF] p-4 text-sm leading-7 text-slate-600">
                <Clock3 className="mt-1 shrink-0 text-[#347FD9]" size={20} />
                <p><strong className="text-[#20364D]">لا يوجد خطأ في إجابتك.</strong><br />يمكنك العودة إلى مسارك الآن، وبعد أن يحدد المشرف نشاط التقوية سيظهر لك عند المتابعة.</p>
              </div>
              <div className="mt-7 flex flex-wrap gap-3">
                <button className="btn-primary" onClick={() => router.push("/student")}>العودة إلى مساري</button>
                <button className="btn-secondary" disabled={checking} onClick={() => void manualCheck()}><RefreshCw size={17} /> {checking ? "جاري الفحص..." : "تحقق من الخطوة"}</button>
              </div>
            </div>
            <div className="relative flex min-h-72 items-end justify-center bg-gradient-to-b from-[#EDF5FF] to-[#F4FBF8] px-6 pt-8">
              <div className="absolute top-8 rounded-full bg-white px-4 py-2 text-sm font-bold text-[#347FD9] shadow-sm">المشرف يراجع المسار</div>
              <Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع الطالب" width={260} height={320} className="h-auto max-h-72 w-auto object-contain" priority />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
