"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Play, RotateCcw } from "lucide-react";
import styles from "./VideoPlayer.module.css";

type PlayerState = "loading" | "ready" | "buffering" | "blocked" | "error" | "saving" | "save_error" | "ended";

interface VideoPlayerProps {
  src: string;
  captionsSrc?: string;
  startAt?: number;
  testOnly?: boolean;
  onCheckpoint: (position: number, duration: number) => void;
  onEnded: (position: number, duration: number) => Promise<void>;
}

// Key the entire player by its media source. A new lesson must not inherit
// pending playback promises, completion acknowledgments or checkpoints.
export default function VideoPlayer(props: VideoPlayerProps) {
  return <VideoPlayerInstance key={props.src} {...props} />;
}

function VideoPlayerInstance({ src, captionsSrc, startAt = 0, testOnly = false, onCheckpoint, onEnded }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastCheckpoint = useRef(startAt);
  const completing = useRef(false);
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
    if (video && startAt > 0 && startAt <= video.duration - 1) video.currentTime = startAt;
    setState((current) => ["error", "saving", "save_error", "ended"].includes(current) ? current : "ready");
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const restoreSavedPosition = () => {
      if (startAt > 0 && Number.isFinite(video.duration) && startAt <= video.duration - 1) video.currentTime = startAt;
      setState((current) => ["error", "saving", "save_error", "ended"].includes(current) ? current : "ready");
    };
    video.addEventListener("loadedmetadata", restoreSavedPosition);
    if (video.readyState >= HTMLMediaElement.HAVE_METADATA) restoreSavedPosition();
    return () => video.removeEventListener("loadedmetadata", restoreSavedPosition);
  }, [src, startAt]);

  const retry = () => {
    // Hold a visible error until the learner explicitly asks to reload media.
    // Native canplay/waiting events may race with an error and must not
    // silently dismiss the retry action.
    if (!videoRef.current) return;
    setState("loading");
    videoRef.current.load();
  };

  const confirmCompletion = async () => {
    const video = videoRef.current;
    if (!video || completing.current || !Number.isFinite(video.duration) || video.duration <= 0) return;
    completing.current = true;
    setState("saving");
    try {
      // The learner sees success only after the server acknowledges completion.
      await onEnded(video.currentTime, video.duration);
      setState("ended");
    } catch {
      // The page reuses its idempotency key if the acknowledgment was lost.
      setState("save_error");
    } finally {
      completing.current = false;
    }
  };

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
        onCanPlay={() => setState((current) => ["ended", "error", "saving", "save_error"].includes(current) ? current : "ready")}
        onWaiting={() => setState((current) => ["ended", "error", "saving", "save_error"].includes(current) ? current : "buffering")}
        onStalled={() => setState((current) => ["ended", "error", "saving", "save_error"].includes(current) ? current : "buffering")}
        onPlaying={() => setState((current) => ["error", "saving", "save_error", "ended"].includes(current) ? current : "ready")}
        onTimeUpdate={checkpoint}
        onPause={checkpoint}
        onError={() => setState((current) => ["saving", "save_error", "ended"].includes(current) ? current : "error")}
        onEnded={() => void confirmCompletion()}
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
        <div className={styles.status} role="alert"><div className={styles.statusCard}><AlertTriangle size={32} aria-hidden="true" /><strong>تعذر تشغيل الفيديو</strong><span>تحقق من الاتصال ثم أعد المحاولة. لن نتجاوز هذه الخطوة تلقائيًا.</span><button type="button" className={styles.action} onClick={retry}><RotateCcw size={18} /> إعادة المحاولة</button></div></div>
      )}
      {state === "saving" && (
        <div className={styles.status} role="status"><div className={styles.statusCard}><span className={styles.spinner} aria-hidden="true" /><strong>جاري حفظ اكتمال الشرح</strong><span>انتظر قليلًا حتى نتأكد من حفظ تقدمك.</span></div></div>
      )}
      {state === "save_error" && (
        <div className={styles.status} role="alert"><div className={styles.statusCard}><AlertTriangle size={32} aria-hidden="true" /><strong>تعذر تأكيد حفظ المشاهدة</strong><span>مشاهدتك لم تُفقد. أعد محاولة الحفظ دون إعادة الفيديو.</span><button type="button" className={styles.action} onClick={() => void confirmCompletion()}><RotateCcw size={18} /> إعادة حفظ المشاهدة</button></div></div>
      )}
      {state === "ended" && (
        <div className={styles.status} role="status"><div className={styles.statusCard}><strong>أكملت الشرح</strong><span>تم حفظ المشاهدة، ويمكنك الانتقال إلى التدريب الموجّه.</span><button type="button" className={styles.action} onClick={replay}><RotateCcw size={18} /> شاهد مرة أخرى</button></div></div>
      )}
      <div className={styles.meta}><span>يمكنك الإيقاف والاستكمال والتحكم بالصوت والترجمة من شريط المشغّل.</span>{testOnly && <strong className={styles.testOnly}><AlertTriangle size={14} /> فيديو TEST ONLY غير معتمد للنشر</strong>}</div>
    </section>
  );
}
