"use client";
import { useEffect, useState } from "react";

export interface V2StudentReport {
  student_id: number; student_name: string; current_level: number | null; journey_state: string;
  pretest: { score: number; attempt_no: number; release_version: string | null } | null;
  posttest: { score: number; attempt_no: number; release_version: string | null } | null;
  comparison_state: string; improvement_points: number | null; relative_improvement: number | null;
  progress: { completed_lessons: number | null; assigned_lessons: number | null; skipped_by_placement: number | null; percent: number | null };
  support: { total: number; resolved: number; mastered: number; needs_followup: number; waiting: number; escalated: number }; pending_assessment_reviews: number;
}
export interface V2Report {
  source: "himma_v2_persisted_evidence"; students: V2StudentReport[];
  skills: { student_id: number; phase: string; skill_group: string; graded: number; correct: number; observed_accuracy_percent: number }[];
  summary: { students: number; official_pretests: number; official_posttests: number; paired: number; average_pretest: number | null; average_posttest: number | null; average_improvement_points: number | null };
  methodology: string;
}
// Fail closed when the staff reporting endpoint returns a partial or stale
// payload. Without shape guards an HTTP 200 can crash the report UI while
// rendering summary/support/progress fields or silently hide skills.
const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const isFiniteCount = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value) && value >= 0;
const isOptionalNumber = (value: unknown) =>
  value === null || (typeof value === "number" && Number.isFinite(value));

export function isValidV2Report(value: unknown): value is V2Report {
  if (!isObject(value) || value.source !== "himma_v2_persisted_evidence"
    || !isObject(value.summary) || !Array.isArray(value.students) || !Array.isArray(value.skills)) return false;
  const summary = value.summary;
  if (!["students", "official_pretests", "official_posttests", "paired"].every(key => isFiniteCount(summary[key]))
    || !["average_pretest", "average_posttest", "average_improvement_points"].every(key => isOptionalNumber(summary[key]))) return false;
  for (const row of value.students) {
    if (!isObject(row) || !Number.isSafeInteger(row.student_id) || typeof row.student_name !== "string"
      || !isObject(row.progress) || !isObject(row.support)
      || !isOptionalNumber(row.improvement_points)
      || !isOptionalNumber(row.progress.assigned_lessons)
      || !isFiniteCount(row.progress.completed_lessons)
      || !["total", "mastered", "needs_followup"].every(key => isFiniteCount(row.support[key]))) {
      // completed_lessons may be null while placement is not yet confirmed.
      if (!(isObject(row) && isObject(row.progress) && row.progress.completed_lessons === null
        && !Number.isNaN(row.student_id) && typeof row.student_name === "string"
        && isObject(row.support) && !["total","mastered","needs_followup"].some(key => !isFiniteCount(row.support[key]))
        && isOptionalNumber(row.progress.assigned_lessons) && isOptionalNumber(row.improvement_points))) return false;
    }
  }
  return value.skills.every(row => isObject(row) && Number.isSafeInteger(row.student_id)
    && typeof row.phase === "string" && typeof row.skill_group === "string"
    && isFiniteCount(row.graded) && isFiniteCount(row.correct)
    && isFiniteCount(row.observed_accuracy_percent));
}
export function useV2Reports() {
  const [data, setData] = useState<V2Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true); setError("");
      try {
        const response = await fetch("/api/v2/reports/summary", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("تعذر تحميل التقارير. أعد المحاولة.");
        const result: unknown = await response.json();
        if (!isValidV2Report(result)) throw new Error("بيانات التقارير غير مكتملة. أعد المحاولة، وإن استمرت المشكلة تواصل مع مسؤول النظام.");
        if (!controller.signal.aborted) setData(result);
      } catch (cause) { if (!controller.signal.aborted) { setData(null); setError(cause instanceof Error ? cause.message : "تعذر تحميل التقرير"); } }
      finally { if (!controller.signal.aborted) setLoading(false); }
    };
    void load(); return () => controller.abort();
  }, [reload]);
  return { data, loading, error, refresh: () => setReload(value => value + 1) };
}
