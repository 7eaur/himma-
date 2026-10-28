"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import StudentRetryTasks from "@/components/learning/StudentRetryTasks";

export default function StudentRerecordPage() {
  const params = useParams<{ taskId: string }>();
  const taskId = Number(params.taskId);
  const valid = Number.isSafeInteger(taskId) && taskId > 0;
  return <main dir="rtl" className="min-h-screen bg-slate-50 px-4 py-5 text-slate-900 sm:py-10">
    <div className="mx-auto max-w-2xl space-y-5">
      <Link href="/student" className="inline-flex min-h-11 items-center rounded-xl border border-slate-200 bg-white px-4 py-2 font-bold text-blue-800">
        العودة إلى لوحة الطالب
      </Link>
      <header className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm sm:p-7">
        <span className="text-sm font-bold text-blue-700">رحلة هِمّة</span>
        <h1 className="mt-2 text-2xl font-extrabold">إعادة تسجيل القراءة</h1>
        <p className="mt-3 leading-8 text-slate-700">اقرأ النص المعروض كما هو، واستمع إلى تسجيلك قبل إرساله. لا تحتاج إلى إعادة الدرس أو الاختبار كاملًا.</p>
      </header>
      {valid ? <StudentRetryTasks taskId={taskId} /> :
        <p role="alert" className="rounded-xl border border-red-200 bg-white p-5 text-red-800">رابط طلب القراءة غير صالح. ارجع إلى لوحة الطالب.</p>}
    </div>
  </main>;
}
