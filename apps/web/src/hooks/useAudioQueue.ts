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

function detachAudio(audio: HTMLAudioElement) {
  audio.pause();
  audio.onended = null;
  audio.onerror = null;
  audio.src = "";
}

/**
 * One cancellable audio owner per screen.
 *
 * A monotonically increasing playback token makes every async `play()` result
 * belong to exactly one Audio element. Repeated taps can therefore never let an
 * old rejected promise stop a newer sound or leave the queue in a sticky error
 * state. While a play/resume request is still pending, duplicate taps for the
 * same queue are ignored instead of creating a second player.
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
  const tokenRef = useRef(0);
  const activeTokenRef = useRef(0);
  const pendingAudioRef = useRef<HTMLAudioElement | null>(null);
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

  const isCurrent = useCallback((audio: HTMLAudioElement, token: number) => (
    !disposedRef.current
    && audioRef.current === audio
    && activeTokenRef.current === token
  ), []);

  const stop = useCallback(() => {
    tokenRef.current += 1;
    activeTokenRef.current = tokenRef.current;
    pendingAudioRef.current = null;
    const audio = audioRef.current;
    if (audio) detachAudio(audio);
    audioRef.current = null;
    urlsRef.current = [];
    indexRef.current = 0;
    signatureRef.current = "";
    setPlaybackState("idle");
  }, [setPlaybackState]);

  const failCurrent = useCallback((audio: HTMLAudioElement, token: number, message: string) => {
    if (!isCurrent(audio, token)) return;
    stop();
    onErrorRef.current?.(message);
  }, [isCurrent, stop]);

  const playIndex = useCallback((index: number) => {
    const url = urlsRef.current[index];
    if (!url) {
      stop();
      return;
    }

    const previous = audioRef.current;
    if (previous) detachAudio(previous);

    const audio = new Audio(url);
    const token = ++tokenRef.current;
    activeTokenRef.current = token;
    audioRef.current = audio;
    pendingAudioRef.current = audio;
    indexRef.current = index;
    setPlaybackState("idle");

    audio.onended = () => {
      if (!isCurrent(audio, token)) return;
      pendingAudioRef.current = null;
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
      failCurrent(audio, token, "تعذر تشغيل الصوت. حاول مرة أخرى.");
    };

    void audio.play().then(() => {
      if (!isCurrent(audio, token)) return;
      pendingAudioRef.current = null;
      setPlaybackState("playing");
    }).catch(() => {
      failCurrent(audio, token, "تعذر تشغيل الصوت. حاول مرة أخرى.");
    });
  }, [failCurrent, isCurrent, setPlaybackState, stop]);

  useEffect(() => {
    playIndexRef.current = playIndex;
  }, [playIndex]);

  const toggle = useCallback((urls: string[]) => {
    const clean = urls.filter(Boolean);
    if (!clean.length) return;
    const nextSignature = signature(clean);
    const current = audioRef.current;

    // A second tap while the browser is still resolving play() must not replace
    // the active element. That replacement is what used to create the stale
    // rejection that stopped the following sound.
    if (current && signatureRef.current === nextSignature && pendingAudioRef.current === current) {
      return;
    }

    if (current && signatureRef.current === nextSignature) {
      if (stateRef.current === "playing") {
        current.pause();
        setPlaybackState("paused");
        return;
      }

      if (stateRef.current === "paused") {
        const token = activeTokenRef.current;
        pendingAudioRef.current = current;
        void current.play().then(() => {
          if (!isCurrent(current, token)) return;
          pendingAudioRef.current = null;
          setPlaybackState("playing");
        }).catch(() => {
          failCurrent(current, token, "تعذر استئناف الصوت. حاول مرة أخرى.");
        });
        return;
      }
    }

    stop();
    // Clear a stale UI error as soon as the student makes a valid new playback
    // request. The hook reports an empty message intentionally; current callers
    // use a React string error state.
    onErrorRef.current?.("");
    urlsRef.current = clean;
    signatureRef.current = nextSignature;
    indexRef.current = 0;
    playIndexRef.current(0);
  }, [failCurrent, isCurrent, setPlaybackState, stop]);

  useEffect(() => {
    disposedRef.current = false;
    return () => {
      disposedRef.current = true;
      tokenRef.current += 1;
      activeTokenRef.current = tokenRef.current;
      pendingAudioRef.current = null;
      const audio = audioRef.current;
      if (audio) detachAudio(audio);
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
