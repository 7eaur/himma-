"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpenCheck, LockKeyhole, Play } from "lucide-react";
import styles from "./learning-v2.module.css";

type LessonState = "current" | "locked" | "done";
interface LessonRow { lesson_id: string; title: string; level: "L1" | "L2" | "L3"; state: LessonState; preview_enabled: boolean; session_id: number | null; }
interface Catalog { test_only: true; release_version: string; lessons: LessonRow[]; }

const LEVEL_LABELS = { L1: "المستوى الأول — الاستعداد للقراءة", L2: "المستوى الثاني — بناء الكلمة", L3: "المستوى الثالث — الطلاقة والفهم" };
const STATE_LABELS: Record<LessonState, string> = { current: "الحالي", locked: "مغلق", done: "مكتمل" };

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
      if (!response.ok) throw new Error(data?.detail || "معاينة V2 غير متاحة في هذه البيئة");
      setCatalog(data);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر تحميل الدروس")).finally(() => setLoading(false));
  }, [router]);

  const grouped = useMemo(() => ({
    L1: catalog?.lessons.filter((lesson) => lesson.level === "L1") ?? [],
    L2: catalog?.lessons.filter((lesson) => lesson.level === "L2") ?? [],
    L3: catalog?.lessons.filter((lesson) => lesson.level === "L3") ?? [],
  }), [catalog]);

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
    <section className={styles.hero}><div><span className={styles.eyebrow}><BookOpenCheck size={16} /> معاينة مشغّل الدروس P03</span><h1>رحلة درس واضحة ومحفوظة</h1><p>المقدمة ثم الفيديو ثم التدريب الموجّه والاختبار المستقل. تحفظ هِمّة موضعك لتعود من المكان نفسه.</p></div><Image className={styles.character} src="/characters/girl/explain.png" alt="شخصية هِمّة تشرح" width={180} height={210} priority /></section>
    <p className={styles.notice}>هذه معاينة مرحلية TEST ONLY للمشغّل والبنية التعليمية. المحتوى والفيديو غير معتمدين للنشر، ولا تُحسب المشاهدة وحدها إتقانًا.</p>
    {error && <div className={styles.error} role="alert">{error}</div>}
    <div className={styles.levels}>{(["L1","L2","L3"] as const).map((level) => <section key={level} className={styles.level}><h2>{LEVEL_LABELS[level]}</h2><div className={styles.cards}>{grouped[level].map((lesson) => <article key={lesson.lesson_id} className={`${styles.card} ${lesson.state === "current" ? styles.cardCurrent : ""} ${lesson.state === "done" ? styles.cardDone : ""} ${lesson.state === "locked" ? styles.cardLocked : ""}`}><div className={styles.cardTop}><span>{lesson.lesson_id}</span><span className={styles.state}>{STATE_LABELS[lesson.state]}</span></div><h3>{lesson.title}</h3><p>{lesson.preview_enabled ? "متاح لمراجعة P03 في بيئة الاختبار." : "يبقى ضمن المسار، ويفتح وفق تقدم الطالب بعد اكتمال المراحل التالية."}</p><button type="button" className={styles.start} disabled={!lesson.preview_enabled || Boolean(starting)} onClick={() => void start(lesson)}>{lesson.preview_enabled ? <><Play size={16} />{starting === lesson.lesson_id ? "جاري الفتح..." : lesson.session_id ? "متابعة الدرس" : "معاينة الدرس"}</> : <><LockKeyhole size={15} /> غير متاح بعد</>}</button></article>)}</div></section>)}</div>
  </div></div>;
}
