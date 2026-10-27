"use client";

import { useState } from "react";
import { CheckCircle, Copy, KeyRound, UserPlus } from "lucide-react";
import { AdminAction, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";

export default function NewStudentPage() {
  const [fullName, setFullName] = useState("");
  const [codeMode, setCodeMode] = useState<"auto" | "manual">("auto");
  const [manualCode, setManualCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successCode, setSuccessCode] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    if (codeMode === "manual" && !/^\d{6}$/.test(manualCode)) {
      setError("رمز الدخول اليدوي يجب أن يتكون من 6 أرقام.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/researcher/students", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          grade_level: 3,
          access_code: codeMode === "manual" ? manualCode : undefined,
        }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        setError(data?.detail || "تعذر إضافة الطالب. تحقق من البيانات وحاول مرة أخرى.");
        return;
      }
      setSuccessCode(data.access_code);
    } catch {
      setError("تعذر الاتصال بالخادم الآن. حاول مرة أخرى بعد قليل.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(successCode);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const reset = () => {
    setSuccessCode("");
    setFullName("");
    setManualCode("");
    setCodeMode("auto");
    setError("");
  };

  if (successCode) {
    return (
      <AdminPage>
        <AdminPageHeader
          eyebrow="إدارة الطلاب"
          icon={CheckCircle}
          title="تمت إضافة الطالب"
          description="احفظ رمز الدخول وسلمه للطالب. يمكنك تغييره لاحقًا من ملف الطالب."
        />
        <AdminPanel>
          <div className="text-center py-6 sm:py-10 max-w-xl mx-auto" data-testid="student-created-state">
            <div className="w-16 h-16 bg-green/10 text-green rounded-full flex items-center justify-center mx-auto mb-5"><CheckCircle size={32} /></div>
            <div className="bg-bg p-5 sm:p-6 rounded-xl border border-border mb-7 max-w-sm mx-auto">
              <p className="text-sm text-muted mb-2">رمز دخول الطالب</p>
              <div className="flex items-center justify-center gap-3 flex-wrap" dir="ltr">
                <span className="text-3xl sm:text-4xl font-mono font-bold text-primary tracking-widest" data-testid="student-access-code">{successCode}</span>
                <button onClick={() => void copyToClipboard()} className="p-2 text-muted hover:text-primary hover:bg-white rounded-md" aria-label="نسخ رمز الدخول">
                  {copied ? <CheckCircle size={20} className="text-green" /> : <Copy size={20} />}
                </button>
              </div>
            </div>
            <div className="flex justify-center gap-3 flex-wrap">
              <AdminAction onClick={reset}>إضافة طالب آخر</AdminAction>
              <AdminAction href="/admin/students" tone="primary">العودة إلى الطلاب</AdminAction>
            </div>
          </div>
        </AdminPanel>
      </AdminPage>
    );
  }

  return (
    <AdminPage>
      <AdminPageHeader
        eyebrow="إدارة الطلاب"
        icon={UserPlus}
        title="إضافة طالب جديد"
        description="أدخل اسم الطالب ثم اختر طريقة إنشاء رمز الدخول. الصف الثالث مثبت لعينة الدراسة."
        actions={<AdminAction href="/admin/students">العودة إلى الطلاب</AdminAction>}
      />

      <AdminPanel>
        <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl" data-testid="create-student-form">
          {error && <div className="alert-error" role="alert">{error}</div>}

          <div>
            <label className="block text-navy font-medium mb-2" htmlFor="student-name">اسم الطالب</label>
            <input
              id="student-name"
              type="text"
              className="input-field"
              data-testid="input-student-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="مثال: سالم"
              required
              minLength={2}
              autoComplete="off"
            />
            <p className="text-sm text-muted mt-2">استخدم الاسم أو الاسم المستعار المعتمد في الدراسة.</p>
          </div>

          <div>
            <span className="block text-navy font-medium mb-2">الصف الدراسي</span>
            <div className="input-field bg-bg text-muted" aria-label="الصف الثالث الابتدائي">الصف الثالث الابتدائي</div>
            <p className="text-sm text-muted mt-2">هذا الحقل ثابت حسب نطاق الدراسة الحالي.</p>
          </div>

          <fieldset className="border border-border rounded-xl p-4 sm:p-5 bg-bg/60">
            <legend className="sr-only">طريقة إنشاء رمز دخول الطالب</legend>
            <div className="flex items-center gap-3 mb-4">
              <div className="rounded-full bg-white p-2 text-primary"><KeyRound size={20} /></div>
              <div><h2 className="font-bold text-navy">رمز دخول الطالب</h2><p className="text-sm text-muted">رمز رقمي مكوّن من 6 أرقام.</p></div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4" role="group" aria-label="طريقة إنشاء الرمز">
              <button
                type="button"
                onClick={() => { setCodeMode("auto"); setError(""); }}
                className={`border rounded-lg px-4 py-3 font-semibold ${codeMode === "auto" ? "border-primary bg-white text-primary" : "border-border text-muted"}`}
                aria-pressed={codeMode === "auto"}
              >
                توليد تلقائي
              </button>
              <button
                type="button"
                onClick={() => { setCodeMode("manual"); setError(""); }}
                className={`border rounded-lg px-4 py-3 font-semibold ${codeMode === "manual" ? "border-primary bg-white text-primary" : "border-border text-muted"}`}
                aria-pressed={codeMode === "manual"}
              >
                إدخال يدوي
              </button>
            </div>

            {codeMode === "auto" ? (
              <div className="bg-white rounded-lg border border-border p-4 flex items-start gap-3" data-testid="auto-code-explanation">
                <KeyRound size={20} className="text-primary mt-0.5 shrink-0" aria-hidden="true" />
                <div>
                  <strong className="text-navy text-sm">سيُنشأ الرمز عند حفظ الطالب</strong>
                  <p className="text-sm text-muted mt-1 leading-6">بعد الإضافة سيظهر لك الرمز الحقيقي الذي أنشأه النظام لتنسخه وتسلمه للطالب. لا نعرض رقمًا تجريبيًا قد يختلف عن الرمز الفعلي.</p>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm text-navy font-medium mb-2" htmlFor="manual-code">اكتب 6 أرقام</label>
                <input
                  id="manual-code"
                  className="input-field text-center text-2xl font-mono tracking-widest"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={manualCode}
                  onChange={(event) => setManualCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="123456"
                  dir="ltr"
                  aria-describedby="manual-code-help"
                />
                <p id="manual-code-help" className="text-sm text-muted mt-2">استخدم رمزًا لا يعرفه إلا الطالب والمشرف.</p>
              </div>
            )}
          </fieldset>

          <div className="pt-4 border-t border-border flex flex-col-reverse sm:flex-row sm:justify-end gap-3">
            <AdminAction href="/admin/students">إلغاء</AdminAction>
            <button type="submit" className="btn-primary" data-testid="submit-create-student" disabled={isLoading}>
              {isLoading ? <span className="spinner" /> : "إضافة الطالب"}
            </button>
          </div>
        </form>
      </AdminPanel>
    </AdminPage>
  );
}
