"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import type { ContentItem } from '../types/api';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { saveAudioToOutbox, removeAudioFromOutbox } from '../lib/idb';

export function AssessmentRunner({ sessionId, onComplete }: { sessionId: number, onComplete: () => void }) {
  const [currentItem, setCurrentItem] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Use a refresh counter to trigger re-fetches without calling setState in effect
  const [refreshKey, setRefreshKey] = useState(0);

  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  });

  const {
    isRecording,
    audioBlob,
    error: recorderError,
    startRecording,
    stopRecording,
    resetRecording,
  } = useAudioRecorder();

  // This effect runs only when sessionId or refreshKey changes.
  // State updates happen inside an async callback, not synchronously.
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const res = await fetch(`/api/assessment/session/${sessionId}/next`);
        if (cancelled) return;
        if (!res.ok) {
          if (res.status === 404) { onCompleteRef.current(); return; }
          throw new Error('Failed to fetch next item');
        }
        const data: ContentItem | null = await res.json();
        if (cancelled) return;
        if (!data) {
          onCompleteRef.current();
        } else {
          setCurrentItem(data);
          resetRecording();
        }
      } catch (err: unknown) {
        if (!cancelled) setError((err as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [sessionId, refreshKey, resetRecording]);

  const advanceToNext = useCallback(() => {
    setRefreshKey(k => k + 1);
  }, []);

  const handleSubmit = useCallback(async (optionId?: number) => {
    if (!currentItem) return;
    setSubmitting(true);
    setError(null);

    try {
      let storageKey: string | undefined;
      let mimeType: string | undefined;
      let size: number | undefined;

      if (audioBlob) {
        const initRes = await fetch(`/api/recordings/init`, { method: 'POST' });
        const initData: { recording_id: string; upload_url: string } = await initRes.json();
        const idempotencyKey = crypto.randomUUID();
        await saveAudioToOutbox(idempotencyKey, initData.recording_id, audioBlob);

        const uploadRes = await fetch(`/api/recordings/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recording_id: initData.recording_id }),
        });
        const uploadData: { storage_key: string } = await uploadRes.json();
        storageKey = uploadData.storage_key;
        mimeType = audioBlob.type;
        size = audioBlob.size;
        await removeAudioFromOutbox(idempotencyKey);
      }

      const stepId = currentItem.steps[0]?.id;
      await fetch(`/api/assessment/session/${sessionId}/attempt/${currentItem.id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': crypto.randomUUID(),
        },
        body: JSON.stringify({
          step_id: stepId,
          selected_option_id: optionId,
          audio_storage_key: storageKey,
          audio_mime_type: mimeType,
          audio_file_size: size,
        }),
      });

      advanceToNext();
    } catch (err: unknown) {
      setError((err as Error).message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [currentItem, sessionId, audioBlob, advanceToNext]);

  if (loading) return <div style={{ padding: '1rem' }}>جاري التحميل...</div>;
  if (!currentItem) return <div style={{ padding: '1rem' }}>لا توجد أسئلة متبقية.</div>;

  const step = currentItem.steps[0];
  const isAudioQuestion = currentItem.interaction_type === 'read_aloud';

  return (
    <div style={{ padding: '2rem', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2 style={{ marginBottom: '1rem' }}>{step?.prompt_text}</h2>
      {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

      {isAudioQuestion ? (
        <div style={{ marginTop: '1.5rem' }}>
          <p style={{ fontSize: '1.4rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            {step?.expected_reading_text}
          </p>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {!isRecording && !audioBlob && (
              <button
                onClick={startRecording}
                style={{ background: '#ef4444', color: 'white', padding: '0.5rem 1.2rem', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                بدء التسجيل 🎤
              </button>
            )}
            {isRecording && (
              <button
                onClick={stopRecording}
                style={{ background: '#f59e0b', color: 'white', padding: '0.5rem 1.2rem', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                إيقاف التسجيل ⏹
              </button>
            )}
            {audioBlob && (
              <button
                onClick={resetRecording}
                style={{ background: '#64748b', color: 'white', padding: '0.5rem 1.2rem', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                إعادة التسجيل 🔄
              </button>
            )}
          </div>
          {recorderError && <p style={{ color: 'red', marginTop: '0.5rem' }}>{recorderError}</p>}
          {audioBlob && (
            <div style={{ marginTop: '1rem' }}>
              <audio src={URL.createObjectURL(audioBlob)} controls />
            </div>
          )}
          <button
            disabled={!audioBlob || submitting}
            onClick={() => handleSubmit()}
            style={{
              marginTop: '1rem',
              background: '#10b981',
              color: 'white',
              padding: '0.5rem 1.5rem',
              border: 'none',
              borderRadius: '6px',
              cursor: audioBlob && !submitting ? 'pointer' : 'not-allowed',
              opacity: !audioBlob || submitting ? 0.5 : 1,
            }}
          >
            {submitting ? 'جاري الإرسال...' : 'إرسال التسجيل'}
          </button>
        </div>
      ) : (
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {step?.options.map((opt) => (
            <button
              key={opt.id}
              onClick={() => handleSubmit(opt.id)}
              disabled={submitting}
              style={{
                padding: '1rem',
                textAlign: 'right',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                background: 'white',
                cursor: submitting ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
              }}
            >
              {opt.text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
