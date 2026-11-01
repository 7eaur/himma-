/** Single user-facing error policy for supervisor screens.
 * Keep backend diagnostics in server logs. Never display raw SQL, internal V2
 * identifiers, HTTP traces or Pydantic validation messages to a supervisor.
 */
const technical = /(?:\b(?:V[12]|SQL|SELECT|INSERT|UPDATE|DELETE|TRACEBACK|Exception|TypeError|ValueError|Pydantic|Internal Server Error|undefined|null|HTTP\s*\d{3})\b|\/api\/|localhost|\.py\b|\.tsx?\b|\{[\s\S]*\}|\[[\s\S]*\]|\b(?:source|schema|payload|constraint|stack)\b)/i;
const arabic = /[\u0600-\u06FF]/;

export function adminErrorMessage(status: number, detail: unknown, fallback: string): string {
  if (status === 401) return "انتهت جلسة المشرف. سجّل الدخول مرة أخرى ثم أعد المحاولة.";
  if (status === 403) return "ليس لديك صلاحية لتنفيذ هذا الإجراء.";
  if (status === 429) return "تكررت المحاولات خلال وقت قصير. حاول مجددًا بعد قليل.";
  if (status >= 500) return `${fallback.replace(/[.،؛\s]+$/g, "")}. الخدمة غير متاحة مؤقتًا؛ أعد المحاولة بعد قليل.`;
  if (typeof detail === "string") {
    const text = detail.trim();
    if (text && text.length <= 180 && arabic.test(text) && !technical.test(text)
      && !/[<>\x00-\x1f]/.test(text)) return text;
  }
  if (status === 422) return "تحقق من البيانات المدخلة ثم أعد المحاولة.";
  return fallback;
}

export async function readAdminApiError(response: Response, fallback: string): Promise<string> {
  const payload: unknown = await response.json().catch(() => null);
  const detail = payload && typeof payload === "object" && "detail" in payload
    ? (payload as {detail: unknown}).detail : null;
  return adminErrorMessage(response.status, detail, fallback);
}

export const adminConnectionError = "تعذر الاتصال بالخدمة. تحقق من اتصال الإنترنت ثم أعد المحاولة.";

/** Normalize network/JSON/unexpected failures without exposing stack traces,
 * field names, SQL errors or English parser diagnostics to staff.
 */
export function safeAdminCaughtError(cause: unknown, fallback: string): string {
  if (cause instanceof TypeError) {
    // Preserve the failed action: "the student's progress did not load"
    // is more useful than a generic network error shared by every page.
    const action = fallback.replace(/[.،؛\s]+$/g, "");
    return fallback === adminConnectionError ? adminConnectionError
      : `${action}. تحقق من اتصال الإنترنت ثم أعد المحاولة.`;
  }
  return cause instanceof Error ? adminErrorMessage(400, cause.message, fallback) : fallback;
}
