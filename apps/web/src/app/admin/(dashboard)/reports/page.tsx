"use client";

import Image from "next/image";

export default function ReportsPage() {
  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto flex flex-col items-center justify-center py-20 text-center">
      <Image 
        src="/characters/boy/welcome.png" 
        alt="Coming Soon" 
        width={180} 
        height={240} 
        className="mb-8 opacity-80"
      />
      <h1 className="text-3xl font-bold text-navy mb-4">التقارير والإحصائيات</h1>
      <p className="text-muted text-lg max-w-md">
        هذه الصفحة قيد التطوير. ستتمكن قريباً من عرض تقارير تفصيلية عن أداء الطلاب ومستوى تقدمهم.
      </p>
      <div className="mt-8 badge bg-primary/10 text-primary px-4 py-2 text-sm">
        قريباً في التحديث القادم
      </div>
    </div>
  );
}
