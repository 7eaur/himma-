"use client";

import { Mic2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import styles from "./StudentRerecordTasks.module.css";

type StudentProfile = {
  active_session: {
    id: number;
    session_type: "pretest" | "posttest" | "core" | string;
  } | null;
};

type RerecordTask = {
  submission_id: number;
  session_id: number;
  attempt_id: number;
  item_id: number;
  step_id: number;
  stable_key: string;
  title: string;
  expected_reading_text?: string | null;
  flow: "assessment" | "activity";
};

function taskEndpoint(sessionType: string, sessionId: number) {
  return sessionType === "core"
    ? `/api/activities/session/${sessionId}/rerecord-tasks`
    : `/api/assessment/session/${sessionId}/rerecord-tasks`;
}

export default function StudentRerecordTasks() {
  const router = useRouter();
  const [tasks, setTasks] = useState<RerecordTask[]>([]);
  const [opening, setOpening] = useState<number | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const profileResponse = await fetch("/api/profile", { cache: "no-store" });
      if (!profileResponse.ok) {
        setTasks([]);
        return;
      }
      const profile = await profileResponse.json() as StudentProfile;
      const session = profile.active_session;
      if (!session || !["core", "pretest", "posttest"].includes(session.session_type)) {
        setTasks([]);
        return;
      }

      const response = await fetch(taskEndpoint(session.session_type, session.id), { cache: "no-store" });
      if (!response.ok) {
        setTasks([]);
        return;
      }
      const flow: RerecordTask["flow"] = session.session_type === "core" ? "activity" : "assessment";
      const rows = await response.json() as Omit<RerecordTask, "flow">[];
      setTasks(rows.map((row) => ({ ...row, flow })));
    } catch {
      // The underlying student screen owns network recovery; this task cue is supplemental.
    }
  }, []);

  useEffect(() => {
    const first = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), 4000);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(timer);
    };
  }, [refresh]);

  const openTask = async (task: RerecordTask) => {
    setOpening(task.submission_id);
    setError("");
    try {
      const prefix = task.flow === "activity" ? "/api/activities" : "/api/assessment";
      const response = await fetch(
        `${prefix}/session/${task.session_id}/attempt/${task.item_id}/step/${task.step_id}/rerecord/start`,
        { method: "POST" },
      );
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر فتح مهمة إعادة التسجيل");
      setTasks((current) => current.filter((value) => value.submission_id !== task.submission_id));
      router.push(task.flow === "activity"
        ? `/student/activity/${task.session_id}`
        : `/student/session/${task.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر فتح مهمة إعادة التسجيل");
      setOpening(null);
    }
  };

  if (!tasks.length) return null;
  const task = tasks[0];

  return (
    <aside className={styles.task} dir="rtl" aria-live="polite" data-testid="student-rerecord-task">
      <div className={styles.icon}><Mic2 size={22} aria-hidden="true" /></div>
      <div className={styles.copy}>
        <strong>{task.title || "إعادة تسجيل القراءة"}</strong>
        <span>طلب المشرف محاولة جديدة لهذه القراءة. أكمل مسارك بشكل طبيعي، وافتح المهمة عندما تكون مستعدًا.</span>
        {tasks.length > 1 && <small>لديك {tasks.length} مهام إعادة تسجيل جاهزة.</small>}
        {error && <small className={styles.error} role="alert">{error}</small>}
      </div>
      <button type="button" className={styles.button} onClick={() => void openTask(task)} disabled={opening === task.submission_id}>
        {opening === task.submission_id ? "جاري الفتح..." : "فتح مهمة التسجيل"}
      </button>
    </aside>
  );
}
