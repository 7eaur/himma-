"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpenCheck, Check, ChevronDown, LockKeyhole, Play, SkipForward } from "lucide-react";
import styles from "./learning-v2.module.css";

type LessonState = "current" | "locked" | "done" | "skipped";
interface LessonRow { lesson_id: string; title: string; level: "L1" | "L2" | "L3"; state: LessonState; preview_enabled: boolean; session_id: number | null; }
interface Catalog { test_only: true; release_version: string; lessons: LessonRow[]; }

const LEVEL_LABELS = { L1: "المستوى الأول — الاستعداد للقراءة", L2: "المستوى الثاني — بناء الكلمة", L3: "المستوى الثالث — الطلاقة والفهم" };
const STATE_LABELS: Record<LessonState, string> = { current: "الحالي", locked: "مغلق", done: "مكتمل", skipped: "تجاوزته حسب مستواك" };

export default function V2LearningCatalogPage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void fetch("/api/v2/lessons/catalog", { cache: "no-store" }).then(async (response) => {
      const data = await response.json().catch(() => null);
      if (response.status === 401 || response.status === 403) { router.replace("/student/login"); return; }
      if (!response.ok) throw new Error(data?.detail || "تعذر فتح الدروس الآن. حاول مرة أخرى لاحقًا.");
      setCatalog(data);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر تحميل الدروس")).finally(() => setLoading(false));
  }, [router]);

  const grouped = useMemo(() => ({
    L1: catalog?.lessons.filter((lesson) => lesson.level === "L1") ?? [],
    L2: catalog?.lessons.filter((lesson) => lesson.level === "L2") ?? [],
    L3: catalog?.lessons.filter((lesson) => lesson.level === "L3") ?? [],
  }), [catalog]);
  const currentLesson = catalog?.lessons.find((lesson) => lesson.state === "current");
  const doneCount = catalog?.lessons.filter((lesson) => lesson.state === "done").length ?? 0;
  const assignedCount = catalog?.lessons.filter((lesson) => lesson.state !== "skipped").length ?? 0;
  const awaitingPlacement = catalog?.lessons.length ? catalog.lessons.every((lesson) => lesson.state === "locked") : false;

  const start = async (lesson: LessonRow) => {
    if (!lesson.preview_enabled || starting) return;
    if (lesson.session_id) { router.push(`/student/learning-v2/${lesson.session_id}`); return; }
    setStarting(lesson.lesson_id); setError("");
    try {
      const response = await fetch(`/api/v2/lessons/${lesson.lesson_id}/start`, { method: "POST" });
      const data = await response.json().catch(() => null);
      if (response.status === 409 && data?.detail?.session_id) { router.push(`/student/learning-v2/${data.detail.session_id}`); return; }
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "تعذر بدء الدرس");
      router.push(`/student/learning-v2/${data.session.session_id}`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر بدء الدرس"); setStarting(null); }
  };

  if (loading) return <div className={styles.page} dir="rtl"><div className={styles.loading}><div><div className={styles.spinner} /><p>جاري تجهيز مسار الدروس...</p></div></div></div>;

  return <div className={styles.page} dir="rtl"><div className={styles.container}>
    <header className={styles.header}><Image src="/brand/logo-gradient.svg" alt="هِمّة" width={126} height={42} priority /><Link href="/student" className={styles.back}><ArrowRight size={17} /> لوحة الطالب</Link></header>
    <section className={styles.mapHero}>
      <span className={styles.eyebrow}><BookOpenCheck size={16}/> خريطة دروسي</span>
      <h1>خطوة جديدة في رحلة القراءة</h1><p>لكل درس مكانه، وهِمّة تحفظ موضعك.</p>
      {!awaitingPlacement && catalog && <span className={styles.mapCount}>{doneCount} من {assignedCount} درسًا مخصصًا لك</span>}
    </section>
    {error && <div className={styles.error} role="alert">{error}</div>}
    {awaitingPlacement ? <section className={`${styles.level} ${styles.prePlacement}`} role="status"><h2>دروسك تفتح بعد تحديد مستواك</h2><p>أكمل الاختبار القبلي أولًا، ثم تختار هِمّة الدروس المناسبة لك تلقائيًا.</p><Link href="/student" className={styles.back}>العودة إلى رحلتي</Link></section> :
      <>
        {currentLesson && <section className={styles.nextLesson} aria-label="درسك الحالي">
          <div><span className={styles.eyebrow}>خطوتك الآن</span><h2>{currentLesson.title}</h2><p>شاهد الشرح، ثم أكمل التدريب والاختبار على مهلك.</p></div>
          <button type="button" className={styles.start} disabled={Boolean(starting)} onClick={() => void start(currentLesson)}><Play size={17}/>{starting ? "جاري الفتح..." : currentLesson.session_id ? "متابعة الدرس" : "ابدأ الدرس"}</button>
        </section>}
        <div className={styles.levels}>{(["L1","L2","L3"] as const).map((level, levelIndex) => {
          const lessons = grouped[level];
          const skipped = lessons.length > 0 && lessons.every((lesson) => lesson.state === "skipped");
          const allDone = lessons.length > 0 && lessons.every((lesson) => lesson.state === "done" || lesson.state === "skipped");
          const current = lessons.some((lesson) => lesson.state === "current");
          return <details key={level} className={styles.mapLevel} open={current} data-level={level}>
            <summary><span className={`${styles.levelNumber} ${current ? styles.levelNumberCurrent : ""}`}>{levelIndex + 1}</span><span><strong>{LEVEL_LABELS[level]}</strong><small>{current ? "مستواك الحالي" : skipped ? "بدأت من مستوى أعلى" : allDone ? "أنجزت دروس هذا المستوى" : "ينتظرك في رحلتك"} · {lessons.length} دروس</small></span><ChevronDown size={18} className={styles.levelChevron}/></summary>
            {skipped && <p className={styles.placementNote}>اختارت هِمّة نقطة بداية تناسبك؛ هذه الدروس متجاوزة حسب نتيجتك، ولا تُضاف إلى إنجازات الدروس.</p>}
            <ol className={styles.lessonList}>{lessons.map((lesson, index) => <li key={lesson.lesson_id} className={styles.lessonRow} data-lesson-state={lesson.state}>
              <span className={styles.lessonNode} aria-hidden="true">{lesson.state === "done" ? <Check size={18}/> : lesson.state === "skipped" ? <SkipForward size={16}/> : lesson.state === "locked" ? <LockKeyhole size={15}/> : index + 1}</span>
              <div><h3>{lesson.title}</h3><span className={styles.lessonState}>{STATE_LABELS[lesson.state]}</span></div>
              {lesson.preview_enabled && <button type="button" className={styles.rowAction} disabled={Boolean(starting)} aria-label={`متابعة ${lesson.title}`} onClick={() => void start(lesson)}><Play size={18}/></button>}
            </li>)}</ol>
          </details>;
        })}</div>
      </>}

  </div></div>;
}
