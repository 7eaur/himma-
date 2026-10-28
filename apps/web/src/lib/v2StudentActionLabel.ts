export function v2StudentActionLabel(action: { action: string; state?: string | null; label: string }) {
  if (action.action === "migration_review") return "انتقال للمشرف";
  if (action.action === "start_pretest") return "بانتظار القبلي";
  if (action.state === "waiting_review") return "بانتظار مراجعة القراءة";
  if (action.state === "placement_pending_review") return "جارٍ تحديد المستوى تلقائيًا";
  if (action.action === "complete") return "أكمل الرحلة";
  return action.label;
}
