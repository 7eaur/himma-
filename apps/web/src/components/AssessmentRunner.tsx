"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Image from "next/image";
import type { ContentItem } from "../types/api";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { saveAudioToOutbox, removeAudioFromOutbox } from "../lib/idb";
import styles from "./AssessmentRunner.module.css";



export function AssessmentRunner({
  sessionId,
  onComplete,
}: {
  sessionId: number;
  onComplete: () => void;
}) {
  const [currentItem, setCurrentItem] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions] = useState(30);
  const [refreshKey, setRefreshKey] = useState(0);

  const onCompleteRef = useRef(onComplete);
  useEffect(() => { onCompleteRef.current = onComplete; });

  const {
    isRecording,
    audioBlob,
    error: recorderError,
    startRecording,
    stopRecording,
    resetRecording,
  } = useAudioRecorder();

  // Fetch next item — setState inside async callback, not synchronously
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const res = await fetch(
          `/api/assessment/session/${sessionId}/next`,
          { credentials: "include" }
        );
        if (cancelled) return;
        if (res.status === 404) { onCompleteRef.current(); return; }
        if (!res.ok) throw new Error("Failed to fetch next item");

        const data: ContentItem | null = await res.json();
        if (cancelled) return;
        if (!data) { onCompleteRef.current(); return; }

        setCurrentItem(data);
        resetRecording();
        setQuestionIndex((prev) => prev + 1);
      } catch (err: unknown) {
        if (!cancelled) setError((err as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [sessionId, refreshKey, resetRecording]);

  const advanceToNext = useCallback(() => setRefreshKey((k) => k + 1), []);

  const handleSubmit = useCallback(
    async (optionId?: number) => {
      if (!currentItem) return;
      setSubmitting(true);
      setError(null);

      try {
        let storageKey: string | undefined;
        let mimeType: string | undefined;
        let size: number | undefined;

        if (audioBlob) {
          const initRes = await fetch(`/api/recordings/init`, {
            method: "POST",
            credentials: "include",
          });
          if (!initRes.ok) throw new Error("Failed to initialise recording");
          const initData: { recording_id: string; upload_url: string } =
            await initRes.json();
          const idempotencyKey = crypto.randomUUID();

          await saveAudioToOutbox(
            idempotencyKey,
            initData.recording_id,
            audioBlob
          );

          const uploadRes = await fetch(`/api/recordings/complete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ recording_id: initData.recording_id }),
          });
          if (!uploadRes.ok) throw new Error("Failed to complete recording upload");
          const uploadData: { storage_key: string } = await uploadRes.json();
          storageKey = uploadData.storage_key;
          mimeType = audioBlob.type;
          size = audioBlob.size;
          await removeAudioFromOutbox(idempotencyKey);
        }

        const stepId = currentItem.steps[0]?.id;
        const submitRes = await fetch(
          `/api/assessment/session/${sessionId}/attempt/${currentItem.id}/submit`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Idempotency-Key": crypto.randomUUID(),
            },
            credentials: "include",
            body: JSON.stringify({
              step_id: stepId,
              selected_option_id: optionId,
              audio_storage_key: storageKey,
              audio_mime_type: mimeType,
              audio_file_size: size,
            }),
          }
        );
        if (!submitRes.ok) throw new Error("Failed to submit answer");

        advanceToNext();
      } catch (err: unknown) {
        setError((err as Error).message || "حدث خطأ. حاول مرة أخرى.");
      } finally {
        setSubmitting(false);
      }
    },
    [currentItem, sessionId, audioBlob, advanceToNext]
  );

  // ── Render states ──
  if (loading) {
    return (
      <div className={styles.loadingWrap}>
        <div className="spinner" />
        <p className={`${styles.loadingText} font-child`}>جاري التحميل...</p>
      </div>
    );
  }

  if (!currentItem) {
    return (
      <div className={styles.emptyWrap}>
        <p className="font-child">لا توجد أسئلة متبقية.</p>
      </div>
    );
  }

  const step = currentItem.steps[0];
  const isAudio = currentItem.interaction_type === "read_aloud";
  const progress = Math.round(((questionIndex - 1) / totalQuestions) * 100);

  return (
    <div className={styles.runner}>
      {/* Progress */}
      <div className={styles.progressSection}>
        <div className={styles.progressLabels}>
          <span className={styles.progressText}>السؤال {questionIndex} من {totalQuestions}</span>
          <span className={styles.progressPct}>{progress}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar__fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Character encourage */}
      <div className={styles.characterRow} aria-hidden="true">
        <Image
          src="/characters/boy-explain.png"
          alt=""
          width={80}
          height={80}
          className={styles.sideCharacter}
        />
        {step?.prompt_text && (
          <div className={`${styles.promptBubble} font-child`}>
            {step.prompt_text}
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: "var(--space-4)" }}>
          {error}
        </div>
      )}

      {/* Question content */}
      {isAudio ? (
        <div className={styles.audioSection}>
          {step?.expected_reading_text && (
            <p className={`${styles.readingText} font-child`}>
              {step.expected_reading_text}
            </p>
          )}

          <div className={styles.recordControls}>
            {!isRecording && !audioBlob && (
              <button
                onClick={startRecording}
                className="btn btn-child"
                style={{ background: "var(--color-error)", color: "white" }}
              >
                🎤 ابدأ التسجيل
              </button>
            )}
            {isRecording && (
              <button
                onClick={stopRecording}
                className="btn btn-child"
                style={{ background: "var(--color-warning)", color: "white" }}
              >
                ⏹ إيقاف التسجيل
              </button>
            )}
            {audioBlob && !isRecording && (
              <button
                onClick={resetRecording}
                className="btn btn-ghost btn-child"
              >
                🔄 إعادة التسجيل
              </button>
            )}
          </div>

          {recorderError && (
            <div className="alert alert-error">{recorderError}</div>
          )}

          {audioBlob && (
            <div className={styles.audioPreview}>
              <audio src={URL.createObjectURL(audioBlob)} controls />
            </div>
          )}

          <button
            disabled={!audioBlob || submitting}
            onClick={() => handleSubmit()}
            className="btn btn-secondary btn-child"
            style={{ marginTop: "var(--space-4)" }}
          >
            {submitting ? "جاري الإرسال..." : "إرسال التسجيل ✅"}
          </button>
        </div>
      ) : (
        <div className={styles.optionsGrid}>
          {step?.options.map((opt) => (
            <button
              key={opt.id}
              onClick={() => handleSubmit(opt.id)}
              disabled={submitting}
              className={`${styles.optionBtn} font-child`}
            >
              {opt.text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
