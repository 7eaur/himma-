"use client";

import { useEffect, useState } from "react";
import { KeyRound, ShieldCheck, UserPlus, UsersRound } from "lucide-react";

interface Supervisor {
  id: number;
  username: string;
  is_active: boolean;
  created_at: string;
}

function Message({ kind, text }: { kind: "success" | "error"; text: string }) {
  if (!text) return null;
  return (
    <div className={kind === "success" ? "alert-success mb-4" : "alert-error mb-4"} role="status">
      {text}
    </div>
  );
}

export default function SettingsPage() {
  const [account, setAccount] = useState<Supervisor | null>(null);
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [username, setUsername] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [newSupervisorName, setNewSupervisorName] = useState("");
  const [newSupervisorPassword, setNewSupervisorPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });

  useEffect(() => {
    let cancelled = false;

    void Promise.all([
      fetch("/api/researcher/account", { cache: "no-store" }),
      fetch("/api/researcher/supervisors", { cache: "no-store" }),
    ])
      .then(async ([accountResponse, supervisorsResponse]) => {
        if (!accountResponse.ok || !supervisorsResponse.ok) {
          throw new Error("تعذر تحميل إعدادات الحساب");
        }
        const accountData: Supervisor = await accountResponse.json();
        const supervisorsData: Supervisor[] = await supervisorsResponse.json();
        if (cancelled) return;
        setAccount(accountData);
        setUsername(accountData.username);
        setSupervisors(supervisorsData);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setMessage({
          kind: "error",
          text: error instanceof Error ? error.message : "تعذر تحميل الإعدادات",
        });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const parseError = async (response: Response, fallback: string) => {
    const data = await response.json().catch(() => null);
    return typeof data?.detail === "string" ? data.detail : fallback;
  };

  const saveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy("profile");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/researcher/account", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      if (!response.ok) throw new Error(await parseError(response, "تعذر حفظ اسم المشرف"));
      const updated: Supervisor = await response.json();
      setAccount(updated);
      setUsername(updated.username);
      setSupervisors((current) => current.map((supervisor) => supervisor.id === updated.id ? updated : supervisor));
      setMessage({ kind: "success", text: "تم حفظ بيانات المشرف بنجاح." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ البيانات" });
    } finally {
      setBusy("");
    }
  };

  const changePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage({ kind: "error", text: "تأكيد كلمة المرور الجديدة غير مطابق." });
      return;
    }
    setBusy("password");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/researcher/account/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!response.ok) throw new Error(await parseError(response, "تعذر تغيير كلمة المرور"));
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage({ kind: "success", text: "تم تغيير كلمة المرور بنجاح." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تغيير كلمة المرور" });
    } finally {
      setBusy("");
    }
  };

  const addSupervisor = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy("supervisor");
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/researcher/supervisors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: newSupervisorName, password: newSupervisorPassword }),
      });
      if (!response.ok) throw new Error(await parseError(response, "تعذر إضافة المشرف"));
      const created: Supervisor = await response.json();
      setSupervisors((current) => [...current, created].sort((a, b) => a.id - b.id));
      setNewSupervisorName("");
      setNewSupervisorPassword("");
      setMessage({ kind: "success", text: "تم إنشاء حساب المشرف الجديد." });
    } catch (error) {
      setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر إضافة المشرف" });
    } finally {
      setBusy("");
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 py-16" dir="rtl">
        <div className="spinner w-10 h-10" />
        <p className="text-muted">جاري تحميل الإعدادات...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 font-plex max-w-5xl w-full mx-auto" dir="rtl">
      <div className="mb-8">
        <p className="text-sm text-primary font-semibold mb-2">إدارة الحساب والصلاحيات</p>
        <h1 className="text-3xl font-bold text-navy mb-2">إعدادات المشرف</h1>
        <p className="text-muted">حدّث بيانات دخولك، غيّر كلمة المرور، أو أضف مشرفًا آخر للمنصة.</p>
      </div>

      <Message kind={message.kind} text={message.text} />

      <div className="grid grid-cols-1 gap-6">
        <section className="card" aria-labelledby="profile-title">
          <div className="flex items-center gap-3 mb-6">
            <div className="rounded-full bg-bg p-3 text-primary"><ShieldCheck size={24} /></div>
            <div>
              <h2 id="profile-title" className="text-xl font-bold text-navy">بيانات الحساب</h2>
              <p className="text-sm text-muted">الاسم التالي هو اسم الدخول واسم المشرف الظاهر في اللوحة.</p>
            </div>
          </div>
          <form onSubmit={saveProfile} className="space-y-4 max-w-lg">
            <div>
              <label className="block text-navy font-medium mb-2" htmlFor="account-name">اسم المشرف / اسم المستخدم</label>
              <input id="account-name" className="input-field" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={2} />
            </div>
            <button className="btn-primary" disabled={busy === "profile" || username.trim() === account?.username}>
              {busy === "profile" ? "جاري الحفظ..." : "حفظ الاسم"}
            </button>
          </form>
        </section>

        <section className="card" aria-labelledby="password-title">
          <div className="flex items-center gap-3 mb-6">
            <div className="rounded-full bg-bg p-3 text-primary"><KeyRound size={24} /></div>
            <div>
              <h2 id="password-title" className="text-xl font-bold text-navy">تغيير كلمة المرور</h2>
              <p className="text-sm text-muted">استخدم كلمة مرور لا تقل عن 8 أحرف ولا تشاركها مع الآخرين.</p>
            </div>
          </div>
          <form onSubmit={changePassword} className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
            <div className="md:col-span-2">
              <label className="block text-navy font-medium mb-2" htmlFor="current-password">كلمة المرور الحالية</label>
              <input id="current-password" type="password" className="input-field" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required autoComplete="current-password" />
            </div>
            <div>
              <label className="block text-navy font-medium mb-2" htmlFor="new-password">كلمة المرور الجديدة</label>
              <input id="new-password" type="password" className="input-field" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
            </div>
            <div>
              <label className="block text-navy font-medium mb-2" htmlFor="confirm-password">تأكيد كلمة المرور</label>
              <input id="confirm-password" type="password" className="input-field" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
            </div>
            <div className="md:col-span-2">
              <button className="btn-primary" disabled={busy === "password"}>{busy === "password" ? "جاري التغيير..." : "تغيير كلمة المرور"}</button>
            </div>
          </form>
        </section>

        <section className="card" aria-labelledby="supervisors-title">
          <div className="flex items-center justify-between gap-4 flex-wrap mb-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-bg p-3 text-primary"><UsersRound size={24} /></div>
              <div>
                <h2 id="supervisors-title" className="text-xl font-bold text-navy">المشرفون</h2>
                <p className="text-sm text-muted">كل مشرف يملك حساب دخول مستقلًا.</p>
              </div>
            </div>
            <span className="rounded-full bg-bg px-4 py-2 text-sm text-primary font-semibold">{supervisors.length} مشرف</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
            {supervisors.map((supervisor) => (
              <div key={supervisor.id} className="border border-border rounded-xl p-4 flex items-center justify-between gap-3">
                <div>
                  <p className="font-bold text-navy">{supervisor.username}</p>
                  <p className="text-xs text-muted">{supervisor.is_active ? "حساب نشط" : "حساب موقوف"}</p>
                </div>
                <div className={`rounded-full px-3 py-1 text-xs font-semibold ${supervisor.is_active ? "bg-green-50 text-green" : "bg-bg text-muted"}`}>
                  {supervisor.id === account?.id ? "حسابك" : "مشرف"}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-border pt-6">
            <div className="flex items-center gap-2 mb-4"><UserPlus size={20} className="text-primary" /><h3 className="font-bold text-navy">إضافة مشرف جديد</h3></div>
            <form onSubmit={addSupervisor} className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
              <div>
                <label className="block text-navy font-medium mb-2" htmlFor="new-supervisor-name">اسم المستخدم</label>
                <input id="new-supervisor-name" className="input-field" value={newSupervisorName} onChange={(e) => setNewSupervisorName(e.target.value)} required minLength={2} placeholder="مثال: مشرف همة" />
              </div>
              <div>
                <label className="block text-navy font-medium mb-2" htmlFor="new-supervisor-password">كلمة المرور المؤقتة</label>
                <input id="new-supervisor-password" type="password" className="input-field" value={newSupervisorPassword} onChange={(e) => setNewSupervisorPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
              </div>
              <div className="md:col-span-2">
                <button className="btn-primary" disabled={busy === "supervisor"}>{busy === "supervisor" ? "جاري الإضافة..." : "إضافة المشرف"}</button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
