"use client";

import Image from "next/image";
import { useState } from "react";

export interface EducationalMedia {
  asset_id: string; kind: string; url: string | null; test_only: boolean;
}
const labels: Record<string, string> = { image: "الصورة", audio: "الصوت", video: "الفيديو" };
export default function EducationalMediaPreview({ asset }: { asset: EducationalMedia }) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const label = labels[asset.kind] ?? "الملف التعليمي";
  return <div className="min-w-0 space-y-2">
    {asset.test_only && <p className="text-xs font-semibold text-amber-800">ملف للمعاينة فقط، وليس أصلًا تعليميًا مستقلًا معتمدًا</p>}
    {!asset.url ? <p className="text-sm text-muted">ملف المعاينة غير متاح.</p>
      : !open ? <button type="button" onClick={() => setOpen(true)}
        className="min-h-11 rounded-xl border border-border px-4 py-2 text-sm font-semibold"
        aria-label={`معاينة ${label} للوسيط ${asset.asset_id}`}>معاينة {label}</button>
      : failed ? <div role="alert" className="space-y-2 text-sm">
          <p className="text-red-700">تعذر تشغيل الملف. تحقق من الاتصال ثم أعد المحاولة.</p>
          <button type="button" onClick={() => { setFailed(false); setAttempt(value => value + 1); }}
            className="min-h-11 rounded-xl border border-border px-4 py-2 font-semibold">إعادة المحاولة</button>
        </div>
      : asset.kind === "image" ? <Image key={attempt} src={asset.url} alt={`معاينة الأصل التعليمي ${asset.asset_id}`}
          width={480} height={280} unoptimized className="h-auto max-h-64 w-full object-contain" onError={() => setFailed(true)} />
      : asset.kind === "audio" ? <audio key={attempt} src={asset.url} controls preload="none"
          className="w-full max-w-full" aria-label={`تشغيل الصوت ${asset.asset_id}`} onError={() => setFailed(true)} />
      : <video key={attempt} src={asset.url} controls preload="none"
          className="w-full max-h-72 rounded-xl" aria-label={`تشغيل الفيديو ${asset.asset_id}`} onError={() => setFailed(true)} />}
  </div>;
}
