"use client";

import { useEffect, useState } from "react";
import { User, Settings as SettingsIcon, Shield } from "lucide-react";

interface Researcher {
  id: string;
  username: string;
  role: string;
}

export default function SettingsPage() {
  const [researcher, setResearcher] = useState<Researcher | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await fetch("/api/me");
        if (res.ok) {
          setResearcher(await res.json());
        }
      } catch (err) {
        console.error("Error fetching researcher info", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMe();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex justify-center py-12">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 font-plex max-w-4xl w-full mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy mb-2">إعدادات الحساب</h1>
        <p className="text-muted">إدارة معلومات حسابك وتفضيلات النظام.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-bg text-primary font-medium rounded-md transition-colors text-right">
            <User size={18} />
            <span>المعلومات الشخصية</span>
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-muted hover:bg-bg rounded-md transition-colors text-right">
            <Shield size={18} />
            <span>الأمان وكلمة المرور</span>
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-muted hover:bg-bg rounded-md transition-colors text-right">
            <SettingsIcon size={18} />
            <span>تفضيلات النظام</span>
          </button>
        </div>
        
        <div className="md:col-span-2">
          <div className="card">
            <h2 className="text-xl font-bold text-navy mb-6">المعلومات الشخصية</h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-navy font-medium mb-2">اسم المستخدم</label>
                <input
                  type="text"
                  className="input-field bg-bg"
                  value={researcher?.username || ""}
                  disabled
                />
                <p className="text-xs text-muted mt-2">لا يمكن تغيير اسم المستخدم حالياً.</p>
              </div>
              
              <div>
                <label className="block text-navy font-medium mb-2">الدور</label>
                <input
                  type="text"
                  className="input-field bg-bg"
                  value={researcher?.role === "researcher" ? "باحثة" : researcher?.role || ""}
                  disabled
                />
              </div>
              
              <div className="pt-4 border-t border-border">
                <button className="btn-primary opacity-50 cursor-not-allowed">
                  حفظ التغييرات
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
