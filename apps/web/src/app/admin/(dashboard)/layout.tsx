"use client";

import DeveloperCredit from "@/components/DeveloperCredit";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { BarChart3, BookOpenCheck, ClipboardList, Film, LayoutDashboard, LogOut, Menu, Mic, Settings, UserPlus, Users, X } from "lucide-react";
import AdminNotifications from "@/components/admin/AdminNotifications";
import PlatformState from "@/components/PlatformState";
import { useAccessibleDialog } from "@/hooks/useAccessibleDialog";
import styles from "./dashboard-layout.module.css";

const navSections = [
  { label: "الرئيسية", items: [{ href: "/admin", label: "نظرة عامة", icon: LayoutDashboard }] },
  { label: "الطلاب", items: [{ href: "/admin/students", label: "جميع الطلاب", icon: Users }, { href: "/admin/students/new", label: "إضافة طالب", icon: UserPlus }] },
  { label: "القراءة الصوتية", items: [{ href: "/admin/v2-review-center", label: "متابعة القراءة الصوتية", icon: Mic }] },
  { label: "المحتوى التعليمي", items: [{ href: "/admin/content-preview", label: "بنك الدروس والأسئلة", icon: BookOpenCheck }, { href: "/admin/v2-media", label: "الوسائط", icon: Film }] },
  { label: "النتائج والتقارير", items: [{ href: "/admin/reports", label: "التقارير", icon: BarChart3 }, { href: "/admin/skill-reports", label: "ملخص المهارات", icon: ClipboardList }] },
  { label: "إدارة المنصة", items: [{ href: "/admin/settings", label: "الإعدادات والمشرفون", icon: Settings }] },
] as const;

interface SidebarContentProps { pathname: string; supervisorName: string; onNavigate: () => void; onLogout: () => void; logoutBusy: boolean; showNotifications?: boolean; }
function SidebarContent({ pathname, supervisorName, onNavigate, onLogout, logoutBusy, showNotifications = true }: SidebarContentProps) {
  const initial = supervisorName.trim().charAt(0) || "م";
  return <><div className={styles.brand}><div className={styles.brandRow}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={112} height={38} priority />{showNotifications && <AdminNotifications surface="desktop" />}</div><span className={styles.brandLabel}>مركز متابعة المشرف</span></div><nav className={styles.nav} aria-label="التنقل في لوحة المشرف">{navSections.map((section) => <div className={styles.navSection} key={section.label}><div className={styles.navSectionTitle}>{section.label}</div><div className={styles.navSectionItems}>{section.items.map((item) => { const isActive = pathname === item.href || (item.href !== "/admin" && pathname.startsWith(`${item.href}/`)); const Icon = item.icon; return <Link key={item.href} href={item.href} onClick={onNavigate} className={`sidebar-nav-item ${styles.navItem} ${isActive ? styles.navItemActive : ""}`} aria-current={isActive ? "page" : undefined}><Icon size={19} className={styles.navIcon} aria-hidden="true" /><span>{item.label}</span></Link>; })}</div></div>)}</nav><div className={styles.sidebarFooter}><div className={styles.user}><div className={styles.avatar} aria-hidden="true">{initial}</div><div className={styles.userMeta}><div className={styles.userName}>{supervisorName || "المشرف"}</div><div className={styles.userRole}>مشرف المنصة</div></div></div><button type="button" onClick={onLogout} disabled={logoutBusy} className={styles.logout}><LogOut size={18} aria-hidden="true" /><span>{logoutBusy ? "جارٍ تسجيل الخروج..." : "تسجيل الخروج"}</span></button></div></>;
}

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authState, setAuthState] = useState<"checking" | "ready" | "error">("checking");
  const [authAttempt, setAuthAttempt] = useState(0);
  const [supervisorName, setSupervisorName] = useState("");
  const [logoutBusy, setLogoutBusy] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const logoutInFlight = useRef(false);
  const mobileDialogRef = useRef<HTMLDivElement>(null);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);
  const closeMobileMenu = useCallback(() => setMobileMenuOpen(false), []);

  useAccessibleDialog({
    open: mobileMenuOpen,
    dialogRef: mobileDialogRef,
    returnFocusRef: menuTriggerRef,
    onClose: closeMobileMenu,
  });

  useEffect(() => {
    let alive = true;
    const controller = new AbortController();
    const verify = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store", signal: controller.signal });
        // Only a confirmed expired/forbidden session redirects to login.
        // Connection problems must never kick an authenticated supervisor out.
        if (response.status === 401 || response.status === 403) {
          if (alive) router.replace("/admin/login");
          return;
        }
        if (!response.ok) {
          if (alive) setAuthState("error");
          return;
        }
        const data = await response.json().catch(() => null);
        if (data?.role !== "researcher") {
          if (alive) router.replace("/admin/login");
          return;
        }
        if (alive) { setSupervisorName(data.display_name || "المشرف"); setAuthState("ready"); }
      } catch {
        if (alive) setAuthState("error");
      }
    };
    void verify();
    return () => { alive = false; controller.abort(); };
  }, [router, authAttempt]);
  const handleLogout = async () => {
    if (logoutInFlight.current) return;
    logoutInFlight.current = true;
    setLogoutBusy(true);
    setLogoutError("");
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error("logout not acknowledged");
      router.replace("/admin/login");
      router.refresh();
    } catch {
      // A failed HTTP acknowledgement does not prove that the session ended.
      // Remain on the protected page and offer the user an explicit retry.
      setLogoutError("تعذر تأكيد تسجيل الخروج. تحقق من اتصالك ثم أعد المحاولة قبل ترك الجهاز.");
    } finally {
      logoutInFlight.current = false;
      setLogoutBusy(false);
    }
  };
  if (authState !== "ready") return <div data-testid="admin-auth-guard"><PlatformState mode={authState === "error" ? "error" : "loading"} title={authState === "error" ? "تعذر التحقق من جلسة المشرف" : "جارٍ التحقق من جلسة المشرف"} description={authState === "error" ? "تعذر الاتصال حاليًا. بيانات لوحة المشرف محمية، ويمكنك إعادة المحاولة." : "نتحقق من صلاحية الدخول قبل عرض بيانات لوحة المشرف."} onAction={authState === "error" ? () => { setAuthState("checking"); setAuthAttempt(value => value + 1); } : undefined} /></div>;
  const sidebarProps = { pathname, supervisorName, onNavigate: closeMobileMenu, onLogout: handleLogout, logoutBusy };
  return <div className={`admin-dashboard-shell ${styles.dashboardShell}`} dir="rtl"><aside className={styles.sidebarDesktop}><SidebarContent {...sidebarProps} showNotifications /></aside>{mobileMenuOpen && <div className={styles.mobileOverlay}><button className={styles.mobileBackdrop} onClick={closeMobileMenu} aria-label="إغلاق القائمة" tabIndex={-1} /><div ref={mobileDialogRef} className={styles.mobilePanel} role="dialog" aria-modal="true" aria-label="قائمة لوحة المشرف" tabIndex={-1}><button onClick={closeMobileMenu} className={styles.mobileClose} aria-label="إغلاق القائمة"><X size={24} /></button><SidebarContent {...sidebarProps} showNotifications={false} /></div></div>}<main className={styles.content}><div className={styles.mobileBar}><button ref={menuTriggerRef} onClick={() => setMobileMenuOpen(true)} className={styles.menuButton} aria-label="فتح القائمة" aria-haspopup="dialog" aria-expanded={mobileMenuOpen}><Menu size={23} /></button><Image src="/brand/logo-navy.svg" alt="هِمّة" width={92} height={30} /><span className={styles.mobileBarText}>الإدارة</span><AdminNotifications surface="mobile" /></div>{logoutError && <div role="alert" className={styles.logoutError}><span>{logoutError}</span><button type="button" onClick={() => void handleLogout()} disabled={logoutBusy}>إعادة محاولة الخروج</button></div>}{children}<DeveloperCredit /></main></div>;
}
