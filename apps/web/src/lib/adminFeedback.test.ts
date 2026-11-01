import { adminConnectionError, adminErrorMessage, readAdminApiError, safeAdminCaughtError } from "./adminFeedback";

it("preserves short actionable Arabic validation messages without technical content", () => {
  expect(adminErrorMessage(409, "اسم المستخدم مستخدم بالفعل.", "تعذر الحفظ"))
    .toBe("اسم المستخدم مستخدم بالفعل.");
  expect(adminErrorMessage(422, "الحقل غير صالح", "تعذر الحفظ"))
    .toBe("الحقل غير صالح");
});

it("never exposes internal exceptions, API paths or version identifiers", () => {
  const fallback = "تعذر حفظ بيانات الحساب.";
  for (const raw of [
    "Traceback (most recent call last): SQL SELECT * FROM users",
    "خطأ في API V2 /api/researcher/account",
    "TypeError: undefined",
    {type: "value_error", loc: ["body", "username"]},
    "Database constraint UNIQUE_V2",
  ]) {
    expect(adminErrorMessage(400, raw, fallback)).toBe(fallback);
  }
});

it("maps common authorization, limit, server and validation errors consistently", () => {
  expect(adminErrorMessage(401, "anything", "تعذر الحفظ")).toMatch(/جلسة المشرف/);
  expect(adminErrorMessage(403, null, "تعذر الحفظ")).toMatch(/صلاحية/);
  expect(adminErrorMessage(429, null, "تعذر الحفظ")).toMatch(/المحاولات/);
  expect(adminErrorMessage(503, "Database down", "تعذر الحفظ")).toMatch(/غير متاحة/);
  expect(adminErrorMessage(422, [{loc: ["body"]}], "تعذر الحفظ")).toMatch(/تحقق من البيانات/);
  expect(adminConnectionError).toMatch(/اتصال الإنترنت/);
});

it("handles malformed HTTP error payloads without displaying raw data", async () => {
  const response = {status: 422, json: async () => ({detail: [{msg: "field required", loc: ["body","name"]}]})} as Response;
  expect(await readAdminApiError(response, "تعذر إضافة الطالب")).toBe("تحقق من البيانات المدخلة ثم أعد المحاولة.");
});

it("converts parser and unexpected JavaScript diagnostics into usable error messages", () => {
  expect(safeAdminCaughtError(new SyntaxError("Unexpected token < in JSON at position 0"), "تعذر تحميل التقارير"))
    .toBe("تعذر تحميل التقارير");
  expect(safeAdminCaughtError(new Error("خطأ قاعدة البيانات SQL INSERT"), "تعذر حفظ الملف"))
    .toBe("تعذر حفظ الملف");
  expect(safeAdminCaughtError(new TypeError("Failed to fetch"), "تعذر التحميل"))
    .toBe("تعذر التحميل. تحقق من اتصال الإنترنت ثم أعد المحاولة.");
  expect(safeAdminCaughtError(new TypeError("Failed to fetch"), adminConnectionError)).toBe(adminConnectionError);
  expect(safeAdminCaughtError(new Error("اسم المستخدم مستخدم بالفعل."), "تعذر الحفظ"))
    .toBe("اسم المستخدم مستخدم بالفعل.");
});
