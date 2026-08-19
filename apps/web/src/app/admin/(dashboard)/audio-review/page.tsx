"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Play, Check, X, Mic } from "lucide-react";

interface AudioReview {
  id: string;
  student_name: string;
  question_text: string;
  audio_url: string;
  submitted_at: string;
}

export default function AudioReviewPage() {
  const [reviews, setReviews] = useState<AudioReview[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fake fetch for now to demonstrate layout, wait for API implementation
    // Replace with real fetch when API is ready
    const fetchReviews = async () => {
      try {
        const res = await fetch("/api/review/pending-audio");
        if (res.ok) {
          setReviews(await res.json());
        }
      } catch (err) {
        console.error("Error fetching audio reviews", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchReviews();
  }, []);

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy mb-2">مراجعة التسجيلات الصوتية</h1>
        <p className="text-muted">استمع إلى قراءة الطلاب وقم بتقييمها.</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner w-8 h-8"></div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 bg-bg rounded-full flex items-center justify-center mb-6">
            <Mic size={40} className="text-muted opacity-50" />
          </div>
          <h3 className="text-xl font-bold text-navy mb-2">لا توجد تسجيلات للمراجعة</h3>
          <p className="text-muted">لقد قمت بمراجعة جميع التسجيلات الصوتية المتاحة.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className="card flex flex-col md:flex-row gap-6 items-start md:items-center">
              <div className="flex-1 space-y-2">
                <div className="flex justify-between items-start">
                  <h3 className="font-bold text-navy text-lg">{review.student_name}</h3>
                  <span className="text-xs text-muted">{new Date(review.submitted_at).toLocaleString('ar-SA')}</span>
                </div>
                <div className="bg-bg p-3 rounded-md border border-border">
                  <p className="text-navy font-tajawal text-lg">{review.question_text}</p>
                </div>
                <div className="pt-2 w-full">
                  <audio controls className="w-full h-10" src={review.audio_url}>
                    متصفحك لا يدعم تشغيل الصوت.
                  </audio>
                </div>
              </div>
              
              <div className="flex md:flex-col gap-2 w-full md:w-auto">
                <button className="flex-1 md:flex-none btn bg-green/10 text-green hover:bg-green hover:text-white transition-colors flex gap-2">
                  <Check size={18} />
                  <span>قراءة صحيحة</span>
                </button>
                <button className="flex-1 md:flex-none btn bg-red-50 text-red-600 hover:bg-red-600 hover:text-white transition-colors flex gap-2">
                  <X size={18} />
                  <span>بحاجة للتحسين</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
