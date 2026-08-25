"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { LayoutDashboard, Users, UserPlus, Mic, BarChart2, Settings, LogOut, Menu, X } from "lucide-react";

const navItems = [
  { href: "/admin", label: "نظرة عامة", icon: LayoutDashboard },
  { href: "/admin/students", label: "الطلاب", icon: Users },
  { href: "/admin/students/new", label: "إضافة طالب", icon: UserPlus },
  { href: "/admin/audio-review", label: "مراجعة الصوت", icon: Mic },
  { href: "/admin/reports", label: "التقارير", icon: BarChart2 },
  { href: "/admin/settings", label: "الإعدادات", icon: Settings },
];

interface SidebarContentProps {
  pathname: string;
  supervisorName: string;
  onNavigate: () => void;
  onLogout: () => void;
}

function SidebarContent({ pathname, supervisorName, onNavigate, onLogout }: SidebarContentProps) {
  const initial = supervisorName.trim().charAt(0) || "م";
  return (
    <>
      <div className="sidebar-brand">
        <Image src="/brand/logo-navy.svg" alt="هِمّة" width={120} height={40} priority />
      </div>

      <nav className="sidebar-nav" aria-label="التنقل في لوحة المشرف">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/admin" && pathname.startsWith(`${item.href}/`));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={`sidebar-nav-item ${isActive ? "active" : ""}`}
            >
              <Icon size={20} className="sidebar-nav-icon" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar" aria-hidden="true">{initial}</div>
          <div>
            <div className="sidebar-user-name">{supervisorName || "المشرف"}</div>
            <div className="text-xs text-muted">مشرف المنصة</div>
          </div>
        </div>
        <button onClick={onLogout} className="sidebar-logout">
          <LogOut size={18} aria-hidden="true" />
          <span>تسجيل الخروج</span>
        </button>
      </div>
    </>
  );
}

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authState, setAuthState] = useState<"checking" | "ready">("checking");
  const [supervisorName, setSupervisorName] = useState("");

  useEffect(() => {
    let alive = true;
    const verify = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (!response.ok || data?.role !== "researcher") {
          router.replace("/admin/login");
          return;
        }
        if (alive) {
          setSupervisorName(data.display_name || "المشرف");
          setAuthState("ready");
        }
      } catch {
        router.replace("/admin/login");
      }
    };
    void verify();
    return () => {
      alive = false;
    };
  }, [router]);

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      router.replace("/admin/login");
      router.refresh();
    }
  };

  if (authState !== "ready") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-bg" dir="rtl" data-testid="admin-auth-guard">
        <Image src="/brand/logo-navy.svg" alt="هِمّة" width={130} height={46} priority />
        <div className="spinner w-12 h-12 border-4" />
        <p className="text-muted">جاري التحقق من جلسة المشرف...</p>
      </div>
    );
  }

  const sidebarProps = {
    pathname,
    supervisorName,
    onNavigate: () => setMobileMenuOpen(false),
    onLogout: handleLogout,
  };

  return (
    <div className="sidebar-layout" dir="rtl">
      <aside className="sidebar hidden md:flex">
        <SidebarContent {...sidebarProps} />
      </aside>

      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-64 max-w-sm flex-1 bg-white flex flex-col z-50 h-full">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 left-4 p-2 text-muted hover:bg-bg rounded-md"
              aria-label="إغلاق القائمة"
            >
              <X size={24} />
            </button>
            <SidebarContent {...sidebarProps} />
          </div>
        </div>
      )}

      <main className="sidebar-content">
        <div className="md:hidden flex items-center justify-between bg-white p-4 border-b border-border mb-4 rounded-md shadow-sm">
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={100} height={32} />
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 text-navy hover:bg-bg rounded-md"
            aria-label="فتح القائمة"
          >
            <Menu size={24} />
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}
