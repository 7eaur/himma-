"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
 * One cancellable audio owner per screen.
 *
 * Playback state is React state so the screen re-renders for play/pause icons.
 * The command functions stay stable; consumers that memoize navigation/reset
 * callbacks should depend on `stop`/`toggle`, not on the returned state object.
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

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    onQueueEndedRef.current = onQueueEnded;
  }, [onQueueEnded]);

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

  useEffect(() => {
    playIndexRef.current = playIndex;
  }, [playIndex]);

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

  return useMemo(() => ({
    state,
    isPlaying: state === "playing",
    isPaused: state === "paused",
    toggle,
    stop,
  }), [state, stop, toggle]);
}
