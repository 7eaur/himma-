/** Shared API types for Himma frontend */

export interface ContentStep {
  id: number;
  order_index: number;
  prompt_text: string;
  expected_reading_text: string | null;
  options: ContentOption[];
}

export interface ContentOption {
  id: number;
  text: string;
  is_correct: boolean;
  order_index: number;
}

export interface ContentItem {
  id: number;
  stable_key: string;
  kind: string;
  interaction_type: string;
  version: string;
  status: string;
  steps: ContentStep[];
}

export interface AssessmentSession {
  id: number;
  session_type: string;
  status: string;
  started_at: string;
}

export interface AudioSubmission {
  id: number;
  submitted_at: string;
  storage_key: string;
  mime_type: string;
  file_size: number;
  status: string;
}
