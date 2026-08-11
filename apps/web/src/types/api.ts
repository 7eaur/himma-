// ────────────────────────────────────────────────────────────────────────────
// Himma API Type Definitions — aligned with backend schemas and catalog v2.0
// ────────────────────────────────────────────────────────────────────────────

/** A single answer option for MCQ items */
export interface ContentOption {
  id: number;
  text: string;
  order_index: number;
  // is_correct is intentionally NOT exposed to the client
}

/** A single step within a content item (one question/round) */
export interface ContentStep {
  id: number;
  order_index: number;
  prompt_text: string;
  expected_reading_text: string | null;
  options: ContentOption[];
}

/** A content item (pretest question, posttest question, or activity) */
export interface ContentItem {
  id: number;
  stable_key: string;
  kind: "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
  level_id: number;
  interaction_type: "multiple_choice" | "read_aloud" | "fill_in_blank";
  order_index: number;
  steps: ContentStep[];
}

/** Assessment session (pretest / posttest / core) */
export interface AssessmentSession {
  id: number;
  student_id: number;
  session_type: "pretest" | "posttest" | "core";
  status: "in_progress" | "completed" | "abandoned";
  started_at: string;
  completed_at: string | null;
  final_score: number | null;
  assigned_level: number | null;
}

/** Audio submission awaiting researcher review */
export interface AudioSubmission {
  id: number;
  response_id: number;
  storage_key: string;
  file_size: number;
  mime_type: string;
  duration_seconds: number | null;
  status: "uploaded" | "graded" | "rerecord_required" | "pending_review";
  submitted_at: string;
}

/** Researcher user profile */
export interface ResearcherProfile {
  id: number;
  username: string;
  full_name: string;
  role: "researcher";
}

/** Student profile returned from /profile */
export interface StudentProfile {
  id: number;
  full_name: string;
  access_code: string;
  grade: number;
  current_level: number;
  status: "active" | "inactive";
}

/** Student as returned in researcher list */
export interface StudentListItem {
  id: number;
  full_name: string;
  access_code: string;
  grade: number;
  current_level: number;
  status: "active" | "inactive";
}
