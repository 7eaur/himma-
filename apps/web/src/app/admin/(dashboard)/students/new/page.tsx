"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Copy, CheckCircle } from "lucide-react";

export default function NewStudentPage() {
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successCode, setSuccessCode] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("/api/researcher/students", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, grade_level: 3 }),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessCode(data.access_code);
      } else {
        const data = await res.json();
        setError(data.detail || "حدث خطأ أثناء إضافة الطالب");
      }
    } catch {
      setError("حدث خطأ أثناء الاتصال بالخادم");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(successCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (successCode) {
    return (
      <div className="flex-1 font-plex max-w-2xl mx-auto w-full">
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-green/10 text-green rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={32} />
          </div>
          <h2 className="text-2xl font-bold text-navy mb-2">تمت إضافة الطالب بنجاح</h2>
          <p className="text-muted mb-8">يرجى حفظ رمز الدخول التالي وإعطائه للطالب ليتمكن من الدخول إلى المنصة.</p>
          
          <div className="bg-bg p-6 rounded-lg border border-border mb-8 max-w-sm mx-auto">
            <p className="text-sm text-muted mb-2">رمز الدخول</p>
            <div className="flex items-center justify-center gap-4">
              <span
                className="text-3xl font-mono font-bold text-primary tracking-widest"
                data-testid="student-access-code"
              >
                {successCode}
              </span>
              <button 
                onClick={copyToClipboard}
                className="p-2 text-muted hover:text-primary hover:bg-primary/10 rounded-md transition-colors"
                title="نسخ الرمز"
              >
                {copied ? <CheckCircle size={20} className="text-green" /> : <Copy size={20} />}
              </button>
            </div>
          </div>
          
          <div className="flex justify-center gap-4">
            <button 
              onClick={() => {
                setSuccessCode("");
                setFullName("");
              }}
              className="btn-secondary"
            >
              إضافة طالب آخر
            </button>
            <Link href="/admin/students" className="btn-primary">
              العودة لقائمة الطلاب
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 font-plex max-w-2xl mx-auto w-full">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/students" className="p-2 text-muted hover:text-navy hover:bg-bg rounded-full transition-colors">
          <ArrowRight size={24} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-navy">إضافة طالب جديد</h1>
        </div>
      </div>

      <div className="card">
        {error && (
          <div className="alert-error mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-navy font-medium mb-2">اسم الطالب الثلاثي</label>
            <input
              type="text"
              className="input-field"
              data-testid="input-student-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="مثال: أحمد محمد عبدالله"
              required
            />
          </div>

          <div>
            <label className="block text-navy font-medium mb-2">الصف الدراسي</label>
            <select
              className="input-field"
              data-testid="input-student-grade"
              value="3"
              disabled
              aria-describedby="grade-help"
            >
              <option value="3">الصف الثالث الابتدائي</option>
            </select>
            <p id="grade-help" className="text-sm text-muted mt-2">
              عينة الدراسة معتمدة لطلاب الصف الثالث فقط.
            </p>
          </div>

          <div className="pt-4 border-t border-border flex justify-end gap-4">
            <Link href="/admin/students" className="btn-ghost">
              إلغاء
            </Link>
            <button
              type="submit"
              className="btn-primary"
              data-testid="submit-create-student"
              disabled={isLoading}
            >
              {isLoading ? <span className="spinner"></span> : "إضافة الطالب"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
