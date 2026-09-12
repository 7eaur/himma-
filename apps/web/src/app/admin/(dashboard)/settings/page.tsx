"use client";

import { useEffect, useRef, useState } from "react";
import { KeyRound, ShieldCheck, UserPlus, UsersRound } from "lucide-react";
import { AdminAction, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";
import styles from "./settings.module.css";

interface Supervisor {
  id: number;
  username: string;
  is_active: boolean;
  created_at: string;
}

type SettingsTab = "account" | "security" | "supervisors";
const TAB_ORDER: SettingsTab[] = ["account", "security", "supervisors"];

function Message({ kind, text }: { kind: "success" | "error"; text: string }) {
  if (!text) return null;
  return <div className={kind === "success" ? "alert-success mb-4" : "alert-error mb-4"} role="status">{text}</div>;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("account");
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
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      fetch("/api/researcher/account", { cache: "no-store" }),
      fetch("/api/researcher/supervisors", { cache: "no-store" }),
    ])
      .then(async ([accountResponse, supervisorsResponse]) => {
        if (!accountResponse.ok || !supervisorsResponse.ok) throw new Error("تعذر تحميل إعدادات الحساب");
        const accountData: Supervisor = await accountResponse.json();
        const supervisorsData: Supervisor[] = await supervisorsResponse.json();
        if (cancelled) return;
        setAccount(accountData);
        setUsername(accountData.username);
        setSupervisors(supervisorsData);
      })
      .catch((error: unknown) => {
        if (!cancelled) setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحميل الإعدادات" });
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const parseError = async (response: Response, fallback: string) => {
    const data = await response.json().catch(() => null);
    return typeof data?.detail === "string" ? data.detail : fallback;
  };

  const selectTab = (tab: SettingsTab, focus = false) => {
    setActiveTab(tab);
    if (focus) tabRefs.current[TAB_ORDER.indexOf(tab)]?.focus();
  };

  const handleTabKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    let targetIndex: number | null = null;
    if (event.key === "ArrowLeft") targetIndex = (index + 1) % TAB_ORDER.length;
    if (event.key === "ArrowRight") targetIndex = (index - 1 + TAB_ORDER.length) % TAB_ORDER.length;
    if (event.key === "Home") targetIndex = 0;
    if (event.key === "End") targetIndex = TAB_ORDER.length - 1;
    if (targetIndex === null) return;
    event.preventDefault();
    selectTab(TAB_ORDER[targetIndex], true);
  };

  const saveProfile = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy("profile"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/researcher/account", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username }) });
      if (!response.ok) throw new Error(await parseError(response, "تعذر حفظ اسم المشرف"));
      const updated: Supervisor = await response.json();
      setAccount(updated); setUsername(updated.username); setSupervisors((current) => current.map((supervisor) => supervisor.id === updated.id ? updated : supervisor));
      setMessage({ kind: "success", text: "تم حفظ بيانات المشرف بنجاح." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ البيانات" }); }
    finally { setBusy(""); }
  };

  const changePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) { setMessage({ kind: "error", text: "تأكيد كلمة المرور الجديدة غير مطابق." }); return; }
    setBusy("password"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/researcher/account/password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) });
      if (!response.ok) throw new Error(await parseError(response, "تعذر تغيير كلمة المرور"));
      setCurrentPassword(""); setNewPassword(""); setConfirmPassword(""); setMessage({ kind: "success", text: "تم تغيير كلمة المرور بنجاح." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تغيير كلمة المرور" }); }
    finally { setBusy(""); }
  };

  const addSupervisor = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy("supervisor"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/researcher/supervisors", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: newSupervisorName, password: newSupervisorPassword }) });
      if (!response.ok) throw new Error(await parseError(response, "تعذر إضافة المشرف"));
      const created: Supervisor = await response.json();
      setSupervisors((current) => [...current, created].sort((a, b) => a.id - b.id)); setNewSupervisorName(""); setNewSupervisorPassword(""); setMessage({ kind: "success", text: "تم إنشاء حساب المشرف الجديد." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر إضافة المشرف" }); }
    finally { setBusy(""); }
  };

  if (loading) return <div className={styles.loading} dir="rtl"><span /><span /><span /></div>;

  const tabs: Array<{ key: SettingsTab; label: string; icon: typeof ShieldCheck }> = [
    { key: "account", label: "الحساب", icon: ShieldCheck },
    { key: "security", label: "الأمان", icon: KeyRound },
    { key: "supervisors", label: "المشرفون", icon: UsersRound },
  ];

  return (
    <AdminPage className={styles.pageNarrow}>
      <AdminPageHeader
        eyebrow="إدارة المنصة"
        icon={ShieldCheck}
        title="إعدادات المشرف"
        description="الحساب والأمان وإدارة المشرفين مقسمة إلى أقسام مستقلة وواضحة."
      />

      <Message kind={message.kind} text={message.text} />

      <div className={styles.tabs} role="tablist" aria-label="أقسام إعدادات المشرف">
        {tabs.map((tab, index) => {
          const Icon = tab.icon;
          const selected = activeTab === tab.key;
          return <button
            key={tab.key}
            ref={(element) => { tabRefs.current[index] = element; }}
            id={`settings-tab-${tab.key}`}
            role="tab"
            type="button"
            aria-selected={selected}
            aria-controls={`settings-panel-${tab.key}`}
            tabIndex={selected ? 0 : -1}
            className={`${styles.tab} ${selected ? styles.tabActive : ""}`}
            onClick={() => selectTab(tab.key)}
            onKeyDown={(event) => handleTabKeyDown(event, index)}
          ><Icon size={17} aria-hidden="true" /> {tab.label}</button>;
        })}
      </div>

      {activeTab === "account" && (
        <div id="settings-panel-account" role="tabpanel" tabIndex={0} aria-labelledby="settings-tab-account">
          <AdminPanel title="بيانات الحساب" description="اسم الدخول والاسم الظاهر لهذا الحساب." actions={<span className={styles.icon}><ShieldCheck size={21} aria-hidden="true" /></span>}>
            <form onSubmit={saveProfile} className={styles.form}>
              <div className={styles.field}><label htmlFor="account-name">اسم المشرف / اسم المستخدم</label><input id="account-name" className={styles.input} value={username} onChange={(e) => setUsername(e.target.value)} required minLength={2} /></div>
              <AdminAction type="submit" tone="primary" disabled={busy === "profile" || username.trim() === account?.username}>{busy === "profile" ? "جاري الحفظ..." : "حفظ بيانات الحساب"}</AdminAction>
            </form>
          </AdminPanel>
        </div>
      )}

      {activeTab === "security" && (
        <div id="settings-panel-security" role="tabpanel" tabIndex={0} aria-labelledby="settings-tab-security">
          <AdminPanel title="الأمان وكلمة المرور" description="غيّر كلمة المرور دون خلطها بإعدادات بقية المنصة." actions={<span className={styles.icon}><KeyRound size={21} aria-hidden="true" /></span>}>
            <form onSubmit={changePassword} className={styles.form}>
              <div className={styles.field}><label htmlFor="current-password">كلمة المرور الحالية</label><input id="current-password" type="password" className={styles.input} value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required autoComplete="current-password" /></div>
              <div className={styles.grid2}>
                <div className={styles.field}><label htmlFor="new-password">كلمة المرور الجديدة</label><input id="new-password" type="password" className={styles.input} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} autoComplete="new-password" /></div>
                <div className={styles.field}><label htmlFor="confirm-password">تأكيد كلمة المرور</label><input id="confirm-password" type="password" className={styles.input} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} autoComplete="new-password" /></div>
              </div>
              <AdminAction type="submit" tone="primary" disabled={busy === "password"}>{busy === "password" ? "جاري التغيير..." : "تغيير كلمة المرور"}</AdminAction>
            </form>
          </AdminPanel>
        </div>
      )}

      {activeTab === "supervisors" && (
        <div id="settings-panel-supervisors" role="tabpanel" tabIndex={0} aria-labelledby="settings-tab-supervisors">
          <AdminPanel title="المشرفون" description="كل مشرف يملك حساب دخول مستقلًا." actions={<div className={styles.panelMeta}><span className={styles.count}>{supervisors.length} مشرف</span><span className={styles.icon}><UsersRound size={21} aria-hidden="true" /></span></div>}>
            <div className={styles.supervisorList}>
              {supervisors.map((supervisor) => <div key={supervisor.id} className={styles.supervisor}><div><strong>{supervisor.username}</strong><small>{supervisor.is_active ? "حساب نشط" : "حساب موقوف"}</small></div><span className={styles.badge}>{supervisor.id === account?.id ? "حسابك" : "مشرف"}</span></div>)}
            </div>
            <div className={styles.divider}>
              <div className={styles.subhead}><UserPlus size={19} aria-hidden="true" /> إضافة مشرف جديد</div>
              <form onSubmit={addSupervisor} className={styles.form}>
                <div className={styles.grid2}>
                  <div className={styles.field}><label htmlFor="new-supervisor-name">اسم المستخدم</label><input id="new-supervisor-name" className={styles.input} value={newSupervisorName} onChange={(e) => setNewSupervisorName(e.target.value)} required minLength={2} placeholder="مثال: supervisor2" /></div>
                  <div className={styles.field}><label htmlFor="new-supervisor-password">كلمة المرور المؤقتة</label><input id="new-supervisor-password" type="password" className={styles.input} value={newSupervisorPassword} onChange={(e) => setNewSupervisorPassword(e.target.value)} required minLength={8} autoComplete="new-password" /></div>
                </div>
                <AdminAction type="submit" tone="primary" icon={UserPlus} disabled={busy === "supervisor"}>{busy === "supervisor" ? "جاري الإضافة..." : "إضافة المشرف"}</AdminAction>
              </form>
            </div>
          </AdminPanel>
        </div>
      )}
    </AdminPage>
  );
}