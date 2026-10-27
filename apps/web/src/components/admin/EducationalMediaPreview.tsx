"use client";

import Image from "next/image";
import { useState } from "react";

export interface EducationalMedia {
  asset_id: string; kind: string; url: string | null; test_only: boolean;
}
export default function EducationalMediaPreview({ asset }: { asset: EducationalMedia }) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  return <div className="min-w-0 space-y-2">
    {asset.test_only && <p className="text-xs font-semibold text-amber-800">TEST ONLY · معاينة غير معتمدة للنشر</p>}
    {!asset.url ? <p className="text-sm text-muted">ملف المعاينة غير متاح.</p>
      : !open ? <button type="button" onClick={() => setOpen(true)} className="min-h-11 rounded-xl border border-border px-4 py-2 text-sm font-semibold">معاينة {asset.asset_id}</button>
      : failed ? <p role="alert" className="text-sm text-red-700">تعذر تشغيل الوسيط. لا يُستبدل بملف مختلف.</p>
      : asset.kind === "image" ? <Image src={asset.url} alt={`معاينة الأصل التعليمي ${asset.asset_id}`} width={480} height={280} unoptimized className="h-auto max-h-64 w-full object-contain" onError={() => setFailed(true)} />
      : asset.kind === "audio" ? <audio src={asset.url} controls preload="none" className="w-full max-w-full" aria-label={`تشغيل الصوت ${asset.asset_id}`} onError={() => setFailed(true)} />
      : <video src={asset.url} controls preload="none" className="w-full max-h-72 rounded-xl" aria-label={`تشغيل الفيديو ${asset.asset_id}`} onError={() => setFailed(true)} />}
  </div>;
}
