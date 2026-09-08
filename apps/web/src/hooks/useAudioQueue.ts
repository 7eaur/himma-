"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type AudioQueueState = "idle" | "playing" | "paused";

function signature(urls: string[]) {
  return urls.join("\n");
}

/**
 * One cancellable audio owner per screen.
 *
 * Replaces chained `new Audio()` promises that could leave old playback alive
 * after navigation or make the control untappable while its visual state moved.
 */
export function useAudioQueue(onError?: (message: string) => void) {
  const [state, setState] = useState<AudioQueueState>("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlsRef = useRef<string[]>([]);
  const indexRef = useRef(0);
  const signatureRef = useRef("");
  const disposedRef = useRef(false);

  const stop = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.onended = null;
      audio.onerror = null;
      audio.src = "";
    }
    audioRef.current = null;
    urlsRef.current = [];
    indexRef.current = 0;
    signatureRef.current = "";
    if (!disposedRef.current) setState("idle");
  }, []);

  const playIndex = useCallback((index: number) => {
    const url = urlsRef.current[index];
    if (!url) {
      stop();
      return;
    }

    const audio = new Audio(url);
    audioRef.current = audio;
    indexRef.current = index;
    audio.onended = () => {
      if (disposedRef.current) return;
      const next = indexRef.current + 1;
      if (next >= urlsRef.current.length) {
        stop();
        return;
      }
      playIndex(next);
    };
    audio.onerror = () => {
      stop();
      onError?.("تعذر تشغيل الصوت. حاول مرة أخرى.");
    };
    void audio.play().then(() => {
      if (!disposedRef.current) setState("playing");
    }).catch(() => {
      stop();
      onError?.("تعذر تشغيل الصوت. حاول مرة أخرى.");
    });
  }, [onError, stop]);

  const toggle = useCallback((urls: string[]) => {
    const clean = urls.filter(Boolean);
    if (!clean.length) return;
    const nextSignature = signature(clean);
    const current = audioRef.current;

    if (current && signatureRef.current === nextSignature) {
      if (state === "playing") {
        current.pause();
        setState("paused");
        return;
      }
      if (state === "paused") {
        void current.play().then(() => setState("playing")).catch(() => {
          stop();
          onError?.("تعذر استئناف الصوت. حاول مرة أخرى.");
        });
        return;
      }
    }

    stop();
    urlsRef.current = clean;
    signatureRef.current = nextSignature;
    indexRef.current = 0;
    playIndex(0);
  }, [onError, playIndex, state, stop]);

  useEffect(() => {
    disposedRef.current = false;
    return () => {
      disposedRef.current = true;
      const audio = audioRef.current;
      if (audio) {
        audio.pause();
        audio.onended = null;
        audio.onerror = null;
        audio.src = "";
      }
      audioRef.current = null;
    };
  }, []);

  return {
    state,
    isPlaying: state === "playing",
    isPaused: state === "paused",
    toggle,
    stop,
  };
}
