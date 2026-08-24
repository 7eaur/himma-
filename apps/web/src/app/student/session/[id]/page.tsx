'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import Image from 'next/image';
import { useParams, useRouter } from 'next/navigation';
import { Mic, MicOff, CheckCircle, AlertCircle, ChevronLeft } from 'lucide-react';

const BASE = '';

type Phase = 'loading' | 'question' | 'recording' | 'submitting' | 'finishing' | 'done' | 'error' | 'waiting_audio_review';

interface ContentOption { id: number; text: string; order_index: number; }
interface ContentStep {
  id: number; order_index: number; prompt_text: string;
  expected_reading_text: string | null; options: ContentOption[];
}
interface ContentItem {
  id: number; stable_key: string; kind: string;
  interaction_type: string; steps: ContentStep[];
  template_data?: { image_url?: string; audio_url?: string; };
}

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  
  const [phase, setPhase] = useState<Phase>('loading');
  const [item, setItem] = useState<ContentItem | null>(null);
  const [answered, setAnswered] = useState(0); // count of submitted
  const [total, setTotal] = useState(30);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [feedbackOption, setFeedbackOption] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [uploading, setUploading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Result state
  const [finalScore, setFinalScore] = useState<number | null>(null);
  const [assignedLevel, setAssignedLevel] = useState<number | null>(null);

  const finishSession = useCallback(async () => {
    setPhase('finishing');
    try {
      const res = await fetch(`${BASE}/api/assessment/session/${sessionId}/finish`, { method: 'POST' });
      const data = await res.json().catch(() => null);
      const detail = typeof data?.detail === 'string' ? data.detail : '';
      if ((res.status === 400 || res.status === 409) && detail.includes('ungraded audio')) {
        setPhase('waiting_audio_review');
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setFinalScore(Number(data.final_score));
      setAssignedLevel(data.assigned_level);
      setPhase('done');
    } catch {
      setError('حدث خطأ في إنهاء الاختبار');
      setPhase('error');
    }
  }, [sessionId]);

  const fetchNextItem = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/api/assessment/session/${sessionId}/next`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ContentItem | null = await res.json();
      if (!data) {
        await finishSession();
        return;
      }

      setSelectedOption(null);
      setFeedbackOption(null);
      setAudioBlob(null);
      setAudioUrl(previousUrl => {
        if (previousUrl) URL.revokeObjectURL(previousUrl);
        return null;
      });
      setRecordingTime(0);
      setItem(data);
      const isAudioItem = data.interaction_type === 'read_aloud' || data.interaction_type === 'audio_record';
      setPhase(isAudioItem ? 'recording' : 'question');
    } catch {
      setError('حدث خطأ في تحميل السؤال');
      setPhase('error');
    }
  }, [finishSession, sessionId]);

  const fetchProgress = useCallback(async () => {
    const res = await fetch(`${BASE}/api/assessment/session/${sessionId}/progress`);
    if (!res.ok) return;
    const data = await res.json();
    setAnswered(data.completed_items);
    if (data.total_items > 0) setTotal(data.total_items);
  }, [sessionId]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void Promise.all([fetchProgress(), fetchNextItem()]);
    }, 0);
    return () => window.clearTimeout(initialLoad);
  }, [fetchNextItem, fetchProgress]);

  const submitAnswer = async (optionId: number | null, audioKey?: string, audioSize?: number, audioMime?: string) => {
    if (!item || !item.steps[0]) return;
    setPhase('submitting');
    if (optionId) setFeedbackOption(optionId);
    try {
      const res = await fetch(`${BASE}/api/assessment/session/${sessionId}/attempt/${item.id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step_id: item.steps[0].id,
          selected_option_id: optionId,
          audio_storage_key: audioKey,
          audio_file_size: audioSize,
          audio_mime_type: audioMime,
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setAnswered(prev => prev + 1);
      // Brief feedback pause for choice questions
      if (optionId) await new Promise(r => setTimeout(r, 700));
      await fetchNextItem();
    } catch {
      setError('حدث خطأ في حفظ الإجابة');
      setPhase('error');
    }
  };

  // Audio recording logic
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const preferredMime = 'audio/webm;codecs=opus';
      const mr = MediaRecorder.isTypeSupported(preferredMime)
        ? new MediaRecorder(stream, { mimeType: preferredMime })
        : new MediaRecorder(stream);
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mr.mimeType || 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl(previousUrl => {
          if (previousUrl) URL.revokeObjectURL(previousUrl);
          return URL.createObjectURL(blob);
        });
        stream.getTracks().forEach(t => t.stop());
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setIsRecording(true);
      setRecordingTime(0);
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } catch {
      setError('لم يتم السماح بالوصول إلى الميكروفون');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const uploadAndSubmit = async () => {
    if (!audioBlob || !item) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      const uploadRes = await fetch(`${BASE}/api/assessment/session/${sessionId}/upload-audio`, {
        method: 'POST',
        body: formData
      });
      if (!uploadRes.ok) throw new Error('Upload failed');
      const { audio_storage_key, audio_file_size, audio_mime_type } = await uploadRes.json();
      await submitAnswer(null, audio_storage_key, audio_file_size, audio_mime_type);
    } catch {
      setError('فشل رفع التسجيل الصوتي — يرجى المحاولة مجدداً');
      setPhase('recording');
    } finally {
      setUploading(false);
    }
  };

  const fmtTime = (s: number) => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`;
  const levelNames: Record<number, string> = { 1: 'الاستعداد للقراءة', 2: 'بناء الكلمة', 3: 'الطلاقة والفهم' };
  const progress = Math.round((answered / total) * 100);

  // ── Render ──────────────────────────────────────────────────────

  if (phase === 'done' && assignedLevel !== null) {
    return (
      <div className="result-shell">
        <div className="result-card">
          <div className="result-icon">
            <CheckCircle size={44} color="#51B985" />
          </div>
          <h1 className="result-title">أحسنت</h1>
          <p className="result-subtitle">لقد أنهيت اختبارك بنجاح. هِمّة ستختار لك ما يناسبك.</p>
          <div className="result-score-circle">
            <span className="result-score-num">{Math.round(finalScore || 0)}%</span>
            <span className="result-score-label">نتيجتك</span>
          </div>
          <div className="result-level-badge">مستواك: {levelNames[assignedLevel] || assignedLevel}</div>
          <Image src="/characters/boy/success.png" alt="" width={140} height={180} style={{margin:'0 auto 24px',display:'block'}} />
          <button
            onClick={() => router.push('/student')}
            className="assessment-submit-btn"
          >العودة للصفحة الرئيسية</button>
        </div>
      </div>
    );
  }

  if (phase === 'waiting_audio_review') {
    return (
      <div className="result-shell">
        <div className="result-card">
          <h1 className="result-title" style={{fontSize:'1.6rem'}}>في انتظار المراجعة</h1>
          <p className="result-subtitle">أجبت على جميع الأسئلة. الباحثة ستراجع تسجيلك الصوتي قريباً، ثم ستظهر نتيجتك.</p>
          <Image src="/characters/girl/encourage.png" alt="" width={140} height={180} style={{margin:'16px auto',display:'block'}} />
          <button onClick={() => router.push('/student')} className="assessment-submit-btn" style={{background:'var(--color-muted)'}}>العودة</button>
        </div>
      </div>
    );
  }

  if (phase === 'error') {
    return (
      <div className="result-shell">
        <div className="result-card">
          <AlertCircle size={48} color="#DC2626" style={{margin:'0 auto 16px',display:'block'}} />
          <h1 className="result-title" style={{color:'#DC2626',fontSize:'1.4rem'}}>حدث خطأ</h1>
          <p className="result-subtitle">{error}</p>
          <button onClick={fetchNextItem} className="assessment-submit-btn">حاول مجدداً</button>
        </div>
      </div>
    );
  }

  if (phase === 'finishing') {
    return (
      <div className="result-shell">
        <div className="result-card">
          <div className="spinner" style={{width:48,height:48,margin:'0 auto 20px'}} />
          <p style={{textAlign:'center',color:'var(--color-muted)',fontFamily:'var(--font-student)',fontSize:'1.1rem'}}>جاري حساب نتيجتك...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-shell">
      {/* Header with progress */}
      <div className="assessment-header">
        <button
          onClick={() => router.push('/student')}
          style={{background:'none',border:'none',cursor:'pointer',color:'var(--color-muted)',display:'flex',alignItems:'center',gap:'4px',fontSize:'0.85rem',fontFamily:'var(--font-student)'}}
        >
          <ChevronLeft size={16} /> رجوع
        </button>
        <div className="assessment-progress-bar">
          <div className="assessment-progress-fill" style={{width:`${progress}%`}} />
        </div>
        <span className="assessment-counter">{answered}/{total}</span>
      </div>

      <div className="assessment-body">
        {(phase === 'loading' || phase === 'submitting') && (
          <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:'16px',padding:'60px 0'}}>
            <div className="spinner" style={{width:48,height:48}} />
            <p style={{color:'var(--color-muted)',fontFamily:'var(--font-student)',fontSize:'1rem'}}>جاري التحميل...</p>
          </div>
        )}

        {phase === 'question' && item && item.steps[0] && (
          <>
            <div className="assessment-question-card">
              <p className="assessment-question-num">السؤال {answered + 1} من {total}</p>
              <p className="assessment-question-text">{item.steps[0].prompt_text}</p>
              {item.template_data?.image_url && (
                <Image
                  src={item.template_data.image_url}
                  alt="صورة السؤال"
                  width={400} height={220}
                  className="assessment-question-img"
                />
              )}
            </div>
            <div className="assessment-options">
              {[...item.steps[0].options]
                .sort((a, b) => a.order_index - b.order_index)
                .map(opt => (
                  <button
                    key={opt.id}
                    className={`assessment-option${selectedOption === opt.id ? ' selected' : ''}${feedbackOption === opt.id ? ' feedback-chosen' : ''}`}
                    onClick={() => setSelectedOption(opt.id)}
                  >
                    {opt.text}
                    {selectedOption === opt.id && <CheckCircle size={20} style={{flexShrink:0}} />}
                  </button>
                ))}
            </div>
            {selectedOption && (
              <button
                className="assessment-submit-btn"
                onClick={() => submitAnswer(selectedOption)}
              >
                تأكيد الإجابة
              </button>
            )}
          </>
        )}

        {phase === 'recording' && item && item.steps[0] && (
          <div className="recording-card">
            <p className="assessment-question-num">السؤال {answered + 1} من {total} — تسجيل صوتي</p>
            <p className="recording-prompt">{item.steps[0].prompt_text}</p>
            {item.steps[0].expected_reading_text && (
              <div className="recording-reading-text">{item.steps[0].expected_reading_text}</div>
            )}
            {!audioBlob ? (
              <>
                <button
                  className={`recording-btn ${isRecording ? 'recording' : 'idle'}`}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={uploading}
                  aria-label={isRecording ? 'إيقاف التسجيل' : 'ابدأ التسجيل'}
                >
                  {isRecording ? <MicOff size={36} color="white" /> : <Mic size={36} color="white" />}
                </button>
                {isRecording && (
                  <>
                    <div className="recording-waveform">
                      {[1,2,3,4,5,6,7].map(i => <div key={i} className="recording-bar" />)}
                    </div>
                    <p className="recording-timer">{fmtTime(recordingTime)}</p>
                  </>
                )}
                <p className="recording-status">
                  {isRecording ? 'جاري التسجيل — اضغط للإيقاف' : 'اضغط للبدء في التسجيل'}
                </p>
              </>
            ) : (
              <>
                <audio src={audioUrl!} controls style={{width:'100%',margin:'16px 0'}} />
                <div style={{display:'flex',gap:'12px',justifyContent:'center',marginTop:'8px'}}>
                  <button
                    onClick={() => {
                      setAudioBlob(null);
                      setAudioUrl(previousUrl => {
                        if (previousUrl) URL.revokeObjectURL(previousUrl);
                        return null;
                      });
                      setRecordingTime(0);
                    }}
                    style={{padding:'12px 24px',border:'2px solid var(--color-border)',borderRadius:'var(--r-full)',background:'white',cursor:'pointer',fontFamily:'var(--font-student)',fontWeight:600,fontSize:'0.9rem'}}
                  >إعادة التسجيل</button>
                  <button
                    className="assessment-submit-btn"
                    style={{flex:1}}
                    onClick={uploadAndSubmit}
                    disabled={uploading}
                  >
                    {uploading ? 'جاري الرفع...' : 'إرسال التسجيل'}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
