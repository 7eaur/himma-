/**
 * Himma Educational Content Catalog
 * Exposes 105 verified items (30 pretest, 30 posttest, 30 core, 15 remedial)
 */

export interface ContentItemDef {
  stable_key: string;
  kind: "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
  level_id: number;
  skill_id: number;
  interaction_type: "multiple_choice" | "audio_record" | "sequence" | "matching";
  order_index: number;
  prompt_text: string;
  expected_reading_text?: string;
  points: number;
  rubric?: string;
  version: string;
  template_data?: any;
  options: {
    text: string;
    is_correct: boolean;
    order_index: number;
  }[];
  assets: {
    manifest_asset_id: string;
    asset_type: "image" | "audio";
    usage_context: string;
  }[];
}

// TODO: Import from actual manifests and map to exactly 105 items.
export const catalog: ContentItemDef[] = [];
