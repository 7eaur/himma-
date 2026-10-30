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
        if (!response.ok) throw new Error("تعذر تحميل تقارير V2. أعد المحاولة.");
        const result = await response.json() as V2Report;
        if (result.source !== "himma_v2_persisted_evidence" || !Array.isArray(result.students) || !Array.isArray(result.skills)) throw new Error("مصدر التقرير غير متطابق مع V2.");
        if (!controller.signal.aborted) setData(result);
      } catch (cause) { if (!controller.signal.aborted) { setData(null); setError(cause instanceof Error ? cause.message : "تعذر تحميل التقرير"); } }
      finally { if (!controller.signal.aborted) setLoading(false); }
    };
    void load(); return () => controller.abort();
  }, [reload]);
  return { data, loading, error, refresh: () => setReload(value => value + 1) };
}
