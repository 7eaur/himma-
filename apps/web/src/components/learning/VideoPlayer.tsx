"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Play, RotateCcw } from "lucide-react";
import styles from "./VideoPlayer.module.css";

type PlayerState = "loading" | "ready" | "buffering" | "blocked" | "error" | "ended";

interface VideoPlayerProps {
  src: string;
  captionsSrc?: string;
  startAt?: number;
  testOnly?: boolean;
  onCheckpoint: (position: number, duration: number) => void;
  onEnded: (position: number, duration: number) => void;
}

export default function VideoPlayer({ src, captionsSrc, startAt = 0, testOnly = false, onCheckpoint, onEnded }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastCheckpoint = useRef(startAt);
  const [state, setState] = useState<PlayerState>("loading");

  const play = async () => {
    try {
      await videoRef.current?.play();
      setState("ready");
    } catch {
      setState("blocked");
    }
  };

  const checkpoint = () => {
    const video = videoRef.current;
    if (!video || !Number.isFinite(video.duration) || video.duration <= 0) return;
    if (Math.abs(video.currentTime - lastCheckpoint.current) >= 5) {
      lastCheckpoint.current = video.currentTime;
      onCheckpoint(video.currentTime, video.duration);
    }
  };

  const resume = () => {
    const video = videoRef.current;
    if (video && startAt > 0 && startAt < video.duration - 1) video.currentTime = startAt;
    setState("ready");
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const restoreSavedPosition = () => {
      if (startAt > 0 && Number.isFinite(video.duration) && startAt < video.duration - 1) video.currentTime = startAt;
      setState("ready");
    };
    video.addEventListener("loadedmetadata", restoreSavedPosition);
    if (video.readyState >= HTMLMediaElement.HAVE_METADATA) restoreSavedPosition();
    return () => video.removeEventListener("loadedmetadata", restoreSavedPosition);
  }, [src, startAt]);

  const replay = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    void play();
  };

  return (
    <section className={styles.shell} aria-label="مشغّل فيديو الدرس" data-testid="v2-video-player">
      <video
        ref={videoRef}
        className={styles.video}
        src={src}
        controls
        playsInline
        preload="metadata"
        onLoadedMetadata={resume}
        onCanPlay={() => setState((current) => current === "ended" ? current : "ready")}
        onWaiting={() => setState("buffering")}
        onStalled={() => setState("buffering")}
        onPlaying={() => setState("ready")}
        onTimeUpdate={checkpoint}
        onPause={checkpoint}
        onError={() => setState("error")}
        onEnded={() => {
          const video = videoRef.current;
          setState("ended");
          if (video && Number.isFinite(video.duration)) onEnded(video.currentTime, video.duration);
        }}
      >
        {captionsSrc && <track kind="captions" src={captionsSrc} srcLang="ar" label="العربية" default />}
        متصفحك لا يدعم تشغيل الفيديو.
      </video>

      {(state === "loading" || state === "buffering") && (
        <div className={styles.status} role="status">
          <div className={styles.statusCard}><span className={styles.spinner} aria-hidden="true" /><strong>{state === "loading" ? "جاري تجهيز الفيديو" : "الاتصال بطيء قليلًا"}</strong><span>سنكمل من الموضع المحفوظ فور جاهزية الفيديو.</span></div>
        </div>
      )}
      {state === "blocked" && (
        <div className={styles.status} role="status"><div className={styles.statusCard}><Play size={32} aria-hidden="true" /><strong>اضغط لبدء الفيديو</strong><span>منع المتصفح التشغيل التلقائي، وتقدّمك ما زال محفوظًا.</span><button type="button" className={styles.action} onClick={() => void play()}><Play size={18} /> تشغيل</button></div></div>
      )}
      {state === "error" && (
        <div className={styles.status} role="alert"><div className={styles.statusCard}><AlertTriangle size={32} aria-hidden="true" /><strong>تعذر تشغيل الفيديو</strong><span>تحقق من الاتصال ثم أعد المحاولة. لن نتجاوز هذه الخطوة تلقائيًا.</span><button type="button" className={styles.action} onClick={() => videoRef.current?.load()}><RotateCcw size={18} /> إعادة المحاولة</button></div></div>
      )}
      {state === "ended" && (
        <div className={styles.status} role="status"><div className={styles.statusCard}><strong>أكملت الشرح</strong><span>تم حفظ المشاهدة، ويمكنك الانتقال إلى التدريب الموجّه.</span><button type="button" className={styles.action} onClick={replay}><RotateCcw size={18} /> شاهد مرة أخرى</button></div></div>
      )}
      <div className={styles.meta}><span>يمكنك الإيقاف والاستكمال والتحكم بالصوت والترجمة من شريط المشغّل.</span>{testOnly && <strong className={styles.testOnly}><AlertTriangle size={14} /> فيديو TEST ONLY غير معتمد للنشر</strong>}</div>
    </section>
  );
}
