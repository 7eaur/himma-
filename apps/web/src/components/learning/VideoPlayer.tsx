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
  temporary?: boolean;
  onCheckpoint: (position: number, duration: number) => void;
  onEnded: (position: number, duration: number) => Promise<void>;
}

// Key the entire player by its media source. A new lesson must not inherit
// pending playback promises, completion acknowledgments or checkpoints.
export default function VideoPlayer(props: VideoPlayerProps) {
  return <VideoPlayerInstance key={props.src} {...props} />;
}

function VideoPlayerInstance({ src, captionsSrc, startAt = 0, onCheckpoint, onEnded }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastCheckpoint = useRef(startAt);
  // An explicit retry must restore this local playback position, not jump
  // back to a stale server checkpoint or start the lesson over.
  const recoveryPosition = useRef<number | null>(null);
  const appliedStartAt = useRef<number | null>(null);
  // Completion is an idempotent learner action: native duplicate ended events
  // must not silently retry a failed save or re-submit after replay.
  const completionStatus = useRef<"idle" | "saving" | "failed" | "confirmed">("idle");
  // A lost acknowledgment must reuse the same completion evidence after media resets.
  const completionEvidence = useRef<{ position: number; duration: number } | null>(null);
  // Only the newest explicit play request may change the playback state.
  const playAttempt = useRef(0);
  const [state, setState] = useState<PlayerState>("loading");

  const play = async () => {
    const attempt = ++playAttempt.current;
    try {
      await videoRef.current?.play();
      if (attempt !== playAttempt.current) return;
      // A late play() result must not dismiss a media error or an in-flight
      // completion save. Only playback states may transition to ready.
      setState((current) => ["loading", "ready", "buffering", "blocked"].includes(current) ? "ready" : current);
    } catch {
      if (attempt !== playAttempt.current) return;
      setState((current) => ["loading", "ready", "buffering", "blocked"].includes(current) ? "blocked" : current);
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
    // Seeking is owned by one metadata listener below; React's event handler
    // must not seek AGAIN to the older server checkpoint after recovery.
    setState((current) => ["blocked", "error", "saving", "save_error", "ended"].includes(current) ? current : "ready");
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const restoreSavedPosition = () => {
      const recovering = recoveryPosition.current !== null;
      const position = recovering ? recoveryPosition.current : appliedStartAt.current === startAt ? null : startAt;
      if (position !== null && position > 0 && Number.isFinite(video.duration) && position <= video.duration - 1 && Math.abs(video.currentTime - position) > 0.5) {
        video.currentTime = position;
      }
      if (recovering) recoveryPosition.current = null;
      appliedStartAt.current = startAt;
      setState((current) => ["blocked", "error", "saving", "save_error", "ended"].includes(current) ? current : "ready");
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
    // A promise from before the retry must not mark the new load as blocked.
    playAttempt.current += 1;
    const video = videoRef.current;
    const position = Number.isFinite(video.currentTime) && video.currentTime > 0 ? video.currentTime : lastCheckpoint.current;
    recoveryPosition.current = position > 0 ? position : null;
    setState("loading");
    video.load();
  };

  const confirmCompletion = async (manualRetry = false) => {
    const video = videoRef.current;
    if (!video) return;
    // An ended event with unusable metadata must offer a recovery action.
    // Silently returning leaves the learner stuck with no completion or retry.
    const evidence = manualRetry && completionStatus.current === "failed"
      ? completionEvidence.current
      : { position: video.currentTime, duration: video.duration };
    if (!evidence || !Number.isFinite(evidence.duration) || evidence.duration <= 0 || !Number.isFinite(evidence.position)) {
      setState("error");
      return;
    }
    // Match the server's >=90% completion gate. A premature native ended
    // event (e.g. interrupted media) must not submit a doomed completion or
    // present a save-retry error for a video the learner has not finished.
    const reachedEnd = evidence.position / evidence.duration >= 0.9;
    if (completionStatus.current === "confirmed") {
      // After replay(), a stale ended event from the previous playback must
      // not cover the video while the learner is watching it again.
      if (reachedEnd) setState("ended");
      return;
    }
    if (completionStatus.current === "saving" || (completionStatus.current === "failed" && !manualRetry)) return;
    if (!reachedEnd) {
      setState("error");
      return;
    }
    completionEvidence.current = evidence;
    completionStatus.current = "saving";
    setState("saving");
    try {
      // The learner sees success only after the server acknowledges completion.
      await onEnded(evidence.position, evidence.duration);
      completionStatus.current = "confirmed";
      setState("ended");
    } catch {
      // A lost acknowledgment is retried only by the explicit learner action.
      // The parent reuses the same idempotency key for that retry.
      completionStatus.current = "failed";
      setState("save_error");
    }
  };

  const replay = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    // A completed lesson can be replayed, but an old play() promise must
    // never override a later error/saving state.
    setState("ready");
    void play();
  };

  return (
    <section className={styles.shell} aria-label="مشغّل فيديو الدرس" data-testid="v2-video-player">
      <video
        ref={videoRef}
        className={styles.video}
        src={src}
        controls={state === "ready" || state === "buffering"}
        playsInline
        preload="metadata"
        onLoadedMetadata={resume}
        onCanPlay={() => setState((current) => ["blocked", "ended", "error", "saving", "save_error"].includes(current) ? current : "ready")}
        onWaiting={() => setState((current) => ["blocked", "ended", "error", "saving", "save_error"].includes(current) ? current : "buffering")}
        onStalled={() => setState((current) => ["blocked", "ended", "error", "saving", "save_error"].includes(current) ? current : "buffering")}
        onPlaying={() => setState((current) => ["blocked", "error", "saving", "save_error", "ended"].includes(current) ? current : "ready")}
        onTimeUpdate={checkpoint}
        onPause={checkpoint}
        onError={() => {
          playAttempt.current += 1;
          setState((current) => ["saving", "save_error", "ended"].includes(current) ? current : "error");
        }}
        onEnded={() => void confirmCompletion()}
      >
        {captionsSrc && <track kind="captions" src={captionsSrc} srcLang="ar" label="العربية" default />}
        متصفحك لا يدعم تشغيل الفيديو.
      </video>

      {state === "loading" && (
        <div className={styles.status} role="status">
          <div className={styles.statusCard}><span className={styles.spinner} aria-hidden="true" /><strong>جاري تجهيز الفيديو</strong><span>يمكنك البدء عندما يصبح المقطع جاهزًا.</span></div>
        </div>
      )}
      {state === "buffering" && (
        <div className={styles.bufferNotice} role="status">
          <span>الفيديو يتوقف مؤقتًا لاستكمال التحميل. يبقى الموضع الحالي محفوظًا داخل المشغّل.</span>
          <button type="button" className={styles.bufferAction} onClick={retry}><RotateCcw size={16} aria-hidden="true"/> إعادة محاولة التحميل</button>
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
        <div className={styles.status} role="alert"><div className={styles.statusCard}><AlertTriangle size={32} aria-hidden="true" /><strong>تعذر تأكيد حفظ المشاهدة</strong><span>مشاهدتك لم تُفقد. أعد محاولة الحفظ دون إعادة الفيديو.</span><button type="button" className={styles.action} onClick={() => void confirmCompletion(true)}><RotateCcw size={18} /> إعادة حفظ المشاهدة</button></div></div>
      )}
      {state === "ended" && (
        <div className={styles.status} role="status"><div className={styles.statusCard}><strong>أكملت الشرح</strong><span>تم حفظ المشاهدة، ويمكنك الانتقال إلى التدريب الموجّه.</span><button type="button" className={styles.action} onClick={replay}><RotateCcw size={18} /> شاهد مرة أخرى</button></div></div>
      )}
      <div className={styles.meta}><span>يمكنك الإيقاف والاستكمال والتحكم بالصوت والترجمة من شريط المشغّل.</span></div>
    </section>
  );
}
