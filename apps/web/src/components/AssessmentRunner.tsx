"use client";

import { useState, useEffect } from 'react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { saveAudioToOutbox, removeAudioFromOutbox } from '../lib/idb';

export function AssessmentRunner({ sessionId, onComplete }: { sessionId: number, onComplete: () => void }) {
  const [currentItem, setCurrentItem] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    isRecording,
    audioBlob,
    error: recorderError,
    startRecording,
    stopRecording,
    resetRecording
  } = useAudioRecorder();

  const fetchNextItem = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/assessment/session/${sessionId}/next`);
      if (!res.ok) {
        if (res.status === 404) {
          // No more items
          onComplete();
          return;
        }
        throw new Error('Failed to fetch next item');
      }
      
      const data = await res.json();
      if (!data) {
        onComplete();
      } else {
        setCurrentItem(data);
        resetRecording();
      }
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchNextItem();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const handleSubmit = async (optionId?: number) => {
    try {
      setSubmitting(true);
      setError(null);
      
      let storageKey = undefined;
      let mimeType = undefined;
      let size = undefined;
      
      if (audioBlob) {
        // Init upload
        const initRes = await fetch(`/api/recordings/init`, { method: 'POST' });
        const initData = await initRes.json();
        const idempotencyKey = crypto.randomUUID();
        
        // Save to IndexedDB outbox
        await saveAudioToOutbox(idempotencyKey, initData.recording_id, audioBlob);
        
        // Upload to S3 (mocked here as API call for now)
        // In reality, we would PUT to initData.upload_url
        
        const uploadRes = await fetch(`/api/recordings/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recording_id: initData.recording_id })
        });
        
        const uploadData = await uploadRes.json();
        storageKey = uploadData.storage_key;
        mimeType = audioBlob.type;
        size = audioBlob.size;
        
        // Remove from outbox
        await removeAudioFromOutbox(idempotencyKey);
      }

      // Submit attempt
      const stepId = currentItem?.steps[0]?.id; // simplified for V1 single step
      await fetch(`/api/assessment/session/${sessionId}/attempt/${currentItem.id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify({
          step_id: stepId,
          selected_option_id: optionId,
          audio_storage_key: storageKey,
          audio_mime_type: mimeType,
          audio_file_size: size
        })
      });

      // Move to next
      fetchNextItem();
    } catch (err: unknown) {
      setError((err as Error).message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div>جاري التحميل...</div>;
  if (!currentItem) return <div>لا توجد أسئلة.</div>;

  const step = currentItem.steps[0]; // Assuming single step for simplicity
  const isAudioQuestion = currentItem.interaction_type === 'read_aloud'; // example

  return (
    <div style={{ padding: '2rem', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>{step?.prompt_text}</h2>
      {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}
      
      {isAudioQuestion ? (
        <div style={{ marginTop: '2rem' }}>
          <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{step?.expected_reading_text}</p>
          
          <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
            {!isRecording && !audioBlob && (
              <button onClick={startRecording} style={{ background: '#ef4444', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px' }}>
                بدء التسجيل 🎤
              </button>
            )}
            {isRecording && (
              <button onClick={stopRecording} style={{ background: '#f59e0b', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px' }}>
                إيقاف التسجيل ⏹
              </button>
            )}
            {audioBlob && (
              <button onClick={resetRecording} style={{ background: '#64748b', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px' }}>
                إعادة التسجيل 🔄
              </button>
            )}
          </div>
          
          {recorderError && <p style={{ color: 'red' }}>{recorderError}</p>}
          
          {audioBlob && (
             <div style={{ marginTop: '1rem' }}>
               <audio src={URL.createObjectURL(audioBlob)} controls />
             </div>
          )}
          
          <button 
            disabled={!audioBlob || submitting} 
            onClick={() => handleSubmit()}
            style={{ marginTop: '1rem', background: '#10b981', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', opacity: (!audioBlob || submitting) ? 0.5 : 1 }}
          >
            {submitting ? 'جاري الإرسال...' : 'إرسال التسجيل'}
          </button>
        </div>
      ) : (
        <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {(step?.options as {id: number, text: string}[]).map((opt) => (
            <button 
              key={opt.id} 
              onClick={() => handleSubmit(opt.id)}
              disabled={submitting}
              style={{ padding: '1rem', textAlign: 'right', border: '1px solid #e2e8f0', borderRadius: '4px', background: 'white', cursor: 'pointer' }}
            >
              {opt.text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
