"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type AudioQueueState = "idle" | "playing" | "paused";
export type AudioQueueApi = {
  state: AudioQueueState;
  isPlaying: boolean;
  isPaused: boolean;
  toggle: (urls: string[]) => void;
  stop: () => void;
};

function signature(urls: string[]) {
  return urls.join("\n");
}

/**
 * One cancellable audio owner per screen with a stable controller identity.
 *
 * The stable object matters because student screens keep the controller inside
 * memoized loading/reset callbacks. Playback state is still React state, so the
 * screen re-renders for play/pause icons without causing navigation effects to
 * restart.
 *
 * onQueueEnded fires only after natural playback reaches the end of the final
 * asset. Manual stop, navigation cleanup, and playback errors deliberately do
 * not count as completion.
 */
export function useAudioQueue(
  onError?: (message: string) => void,
  onQueueEnded?: () => void,
): AudioQueueApi {
  const [state, setState] = useState<AudioQueueState>("idle");
  const stateRef = useRef<AudioQueueState>("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlsRef = useRef<string[]>([]);
  const indexRef = useRef(0);
  const signatureRef = useRef("");
  const disposedRef = useRef(false);
  const onErrorRef = useRef(onError);
  const onQueueEndedRef = useRef(onQueueEnded);
  const playIndexRef = useRef<(index: number) => void>(() => undefined);
  const apiRef = useRef<AudioQueueApi | null>(null);
  onErrorRef.current = onError;
  onQueueEndedRef.current = onQueueEnded;

  const setPlaybackState = useCallback((next: AudioQueueState) => {
    stateRef.current = next;
    if (!disposedRef.current) setState(next);
  }, []);

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
    setPlaybackState("idle");
  }, [setPlaybackState]);

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
        const completed = onQueueEndedRef.current;
        stop();
        completed?.();
        return;
      }
      playIndexRef.current(next);
    };
    audio.onerror = () => {
      stop();
      onErrorRef.current?.("تعذر تشغيل الصوت. حاول مرة أخرى.");
    };
    void audio.play().then(() => {
      setPlaybackState("playing");
    }).catch(() => {
      stop();
      onErrorRef.current?.("تعذر تشغيل الصوت. حاول مرة أخرى.");
    });
  }, [setPlaybackState, stop]);
  playIndexRef.current = playIndex;

  const toggle = useCallback((urls: string[]) => {
    const clean = urls.filter(Boolean);
    if (!clean.length) return;
    const nextSignature = signature(clean);
    const current = audioRef.current;

    if (current && signatureRef.current === nextSignature) {
      if (stateRef.current === "playing") {
        current.pause();
        setPlaybackState("paused");
        return;
      }
      if (stateRef.current === "paused") {
        void current.play().then(() => setPlaybackState("playing")).catch(() => {
          stop();
          onErrorRef.current?.("تعذر استئناف الصوت. حاول مرة أخرى.");
        });
        return;
      }
    }

    stop();
    urlsRef.current = clean;
    signatureRef.current = nextSignature;
    indexRef.current = 0;
    playIndexRef.current(0);
  }, [setPlaybackState, stop]);

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

  if (!apiRef.current) {
    apiRef.current = { state, isPlaying: false, isPaused: false, toggle, stop };
  }
  apiRef.current.state = state;
  apiRef.current.isPlaying = state === "playing";
  apiRef.current.isPaused = state === "paused";
  apiRef.current.toggle = toggle;
  apiRef.current.stop = stop;
  return apiRef.current;
}
