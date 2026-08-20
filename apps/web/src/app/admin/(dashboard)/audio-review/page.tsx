'use client';
import { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, XCircle } from 'lucide-react';

interface AudioSubmission {
  id: number;
  storage_key: string;
  status: string;
  submitted_at: string;
}

export default function AudioReviewPage() {
  const [submissions, setSubmissions] = useState<AudioSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [gradingId, setGradingId] = useState<number | null>(null);
  const [isValid, setIsValid] = useState<boolean>(true);
  const [targetUnits, setTargetUnits] = useState<number>(10);
  const [deletions, setDeletions] = useState<number>(0);
  const [substitutions, setSubstitutions] = useState<number>(0);
  const [insertions, setInsertions] = useState<number>(0);
  const [notes, setNotes] = useState<string>('');

  const fetchSubmissions = async () => {
    try {
      const res = await fetch('/api/review/pending-audio');
      if (!res.ok) throw new Error('Failed to fetch pending audio');
      const data = await res.json();
      setSubmissions(data);
    } catch (e) {
      setError('Error loading audio submissions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubmissions();
    const interval = setInterval(fetchSubmissions, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleGrade = async (id: number) => {
    setGradingId(id);
    try {
      const payload = {
        is_valid: isValid,
        target_units: isValid ? targetUnits : undefined,
        deletions: isValid ? deletions : undefined,
        substitutions: isValid ? substitutions : undefined,
        insertions: isValid ? insertions : undefined,
        pronunciation_notes: notes,
      };

      const res = await fetch(`/api/review/audio/${id}/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Grading failed');
      
      setSubmissions(s => s.filter(x => x.id !== id));
      
      // Reset form
      setIsValid(true);
      setTargetUnits(10);
      setDeletions(0);
      setSubstitutions(0);
      setInsertions(0);
      setNotes('');
    } catch (e) {
      alert('Error grading submission');
    } finally {
      setGradingId(null);
    }
  };

  if (loading) return <div style={{padding:40, textAlign:'center'}}>جاري التحميل...</div>;
  if (error) return <div style={{padding:40, color:'red', textAlign:'center'}}>{error}</div>;

  return (
    <div style={{padding:'40px 24px', maxWidth:800, margin:'0 auto', fontFamily:'var(--font-student)'}} dir="rtl">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:24}}>
        <h1 style={{fontSize:'1.8rem', color:'var(--color-navy)', margin:0}}>مراجعة التسجيلات الصوتية</h1>
        <button 
          onClick={fetchSubmissions}
          style={{padding:'8px 16px', background:'white', border:'1px solid var(--color-border)', borderRadius:'var(--r-md)', cursor:'pointer'}}
        >تحديث القائمة</button>
      </div>

      {submissions.length === 0 ? (
        <div className="review-empty">
          <CheckCircle size={64} color="#51B985" style={{margin:'0 auto 16px'}} />
          <h2>لا توجد تسجيلات بانتظار المراجعة</h2>
          <p>جميع التسجيلات تمت مراجعتها بنجاح.</p>
        </div>
      ) : (
        <div className="review-queue">
          {submissions.map(sub => (
            <div key={sub.id} className="review-item" style={{display:'block'}}>
              <div style={{display:'flex', justifyContent:'space-between', marginBottom:12}}>
                <strong>التسجيل رقم {sub.id}</strong>
                <span style={{fontSize:'0.85rem', color:'var(--color-muted)'}}>
                  {new Date(sub.submitted_at).toLocaleString('ar-SA')}
                </span>
              </div>
              <div className="review-audio-player" style={{marginBottom:16}}>
                {/* Normally we'd use a presigned URL or proxy route to access MinIO */}
                {/* For P04, we assume the frontend can load it if it's public or through an API */}
                <audio src={`/api/audio/${sub.storage_key}`} controls />
              </div>

              <div className="review-grade-form">
                <div className="review-valid-toggle" style={{marginBottom:16}}>
                  <span className="review-rubric-label">حالة التسجيل:</span>
                  <button 
                    className={`review-valid-btn ${isValid ? 'active-valid' : ''}`}
                    onClick={() => setIsValid(true)}
                  >
                    <CheckCircle size={16} /> تسجيل صالح
                  </button>
                  <button 
                    className={`review-valid-btn ${!isValid ? 'active-invalid' : ''}`}
                    onClick={() => setIsValid(false)}
                  >
                    <XCircle size={16} /> غير صالح (إعادة تسجيل)
                  </button>
                </div>

                {isValid && (
                  <div style={{display:'flex', gap:16, flexWrap:'wrap', marginBottom:16}}>
                    <div className="review-rubric-row">
                      <span className="review-rubric-label">الكلمات المستهدفة:</span>
                      <input type="number" min={1} value={targetUnits} onChange={e => setTargetUnits(Number(e.target.value))} className="review-rubric-input" />
                    </div>
                    <div className="review-rubric-row">
                      <span className="review-rubric-label">الأخطاء (حذف):</span>
                      <input type="number" min={0} value={deletions} onChange={e => setDeletions(Number(e.target.value))} className="review-rubric-input" />
                    </div>
                    <div className="review-rubric-row">
                      <span className="review-rubric-label">الأخطاء (استبدال):</span>
                      <input type="number" min={0} value={substitutions} onChange={e => setSubstitutions(Number(e.target.value))} className="review-rubric-input" />
                    </div>
                    <div className="review-rubric-row">
                      <span className="review-rubric-label">الأخطاء (إضافة):</span>
                      <input type="number" min={0} value={insertions} onChange={e => setInsertions(Number(e.target.value))} className="review-rubric-input" />
                    </div>
                  </div>
                )}

                <div className="review-rubric-row" style={{alignItems:'flex-start', marginBottom:16}}>
                  <span className="review-rubric-label">ملاحظات:</span>
                  <textarea 
                    value={notes} 
                    onChange={e => setNotes(e.target.value)}
                    style={{flex:1, border:'1.5px solid var(--color-border)', borderRadius:'var(--r-md)', padding:'8px 12px', minHeight:60, fontFamily:'var(--font-student)'}}
                    placeholder="ملاحظات حول النطق أو الطلاقة..."
                  />
                </div>

                <button 
                  className="review-submit-btn" 
                  onClick={() => handleGrade(sub.id)}
                  disabled={gradingId === sub.id}
                >
                  {gradingId === sub.id ? 'جاري الحفظ...' : 'حفظ التقييم'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
