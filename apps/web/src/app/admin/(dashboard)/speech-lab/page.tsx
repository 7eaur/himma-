"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, Square, Upload } from "lucide-react";
import styles from "./speech-lab.module.css";

type Target = {
  target_id: string;
  canonical_id: string;
  title: string;
  group: string;
  kind: string;
  level_id: number | null;
  skill_name: string | null;
  interaction_type: string;
  round_index: number;
  reference_text: string;
};

type AlignmentRow = {
  kind: "correct" | "deletion" | "insertion" | "substitution";
  reference: string | null;
  hypothesis: string | null;
};

type Analysis = {
  lab_only: boolean;
  provider: string;
  model: string | null;
  request_id: string | null;
  reference_text: string;
  normalized_reference: string;
  raw_transcript: string;
  normalized_transcript: string;
  provider_confidence: number | null;
  duration_seconds: number | null;
  counts: Record<string, number>;
  wer: number;
  lexical_accuracy: number;
  alignment: AlignmentRow[];
  academic_effect: "none";
  pronunciation_status: string;
};

const groups = [
  ["all", "كل المحتوى"],
  ["pretest", "الاختبار القبلي"],
  ["posttest", "الاختبار البعدي"],
  ["level_1", "المستوى الأول"],
  ["level_2", "المستوى الثاني"],
  ["level_3", "المستوى الثالث"],
  ["reinforcement", "التقوية"],
] as const;

const kindLabel: Record<AlignmentRow["kind"], string> = {
  correct: "صحيح",
  deletion: "حذف",
  insertion: "إضافة",
  substitution: "استبدال",
};

function percent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 1000) / 10}%`;
}

export default function SpeechLabPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [group, setGroup] = useState("all");
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState<{ configured: boolean; provider: string | null; detail?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [message, setMessage] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [targetsResponse, providerResponse] = await Promise.all([
          fetch("/api/admin/speech-lab/targets", { cache: "no-store" }),
          fetch("/api/admin/speech-lab/provider", { cache: "no-store" }),
        ]);
        const targetData = await targetsResponse.json();
        const providerData = await providerResponse.json();
        if (!targetsResponse.ok) throw new Error(targetData?.detail || "تعذر تحميل محتوى القراءة");
        if (!providerResponse.ok) throw new Error(providerData?.detail || "تعذر قراءة حالة المزود");
        if (!active) return;
        setTargets(targetData.targets || []);
        setSelectedId(targetData.targets?.[0]?.target_id || "");
        setProvider(providerData);
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "تعذر تجهيز مختبر الصوت");
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ar");
    return targets.filter((target) => {
      const groupOk = group === "all" || target.group === group;
      const queryOk = !needle || `${target.canonical_id} ${target.title} ${target.reference_text} ${target.skill_name || ""}`.toLocaleLowerCase("ar").includes(needle);
      return groupOk && queryOk;
    });
  }, [targets, group, query]);

  const effectiveSelectedId = filtered.some((target) => target.target_id === selectedId)
    ? selectedId
    : filtered[0]?.target_id || "";
  const selected = filtered.find((target) => target.target_id === effectiveSelectedId) || null;

  const replaceAudio = (blob: Blob | null) => {
    setAnalysis(null);
    setAudioBlob(blob);
    setAudioUrl((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return blob ? URL.createObjectURL(blob) : null;
    });
  };

  const resetForCatalogChange = () => {
    setSelectedId("");
    replaceAudio(null);
    setMessage("");
  };

  const startRecording = async () => {
    setMessage("");
    if (!selected) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        replaceAudio(blob);
        stream.getTracks().forEach((track) => track.stop());
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setMessage("لم نتمكن من استخدام الميكروفون. تحقق من إذن المتصفح ثم حاول مرة أخرى.");
    }
  };

  const stopRecording = () => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") recorder.stop();
    recorderRef.current = null;
    setRecording(false);
  };

  const analyze = async () => {
    if (!selected || !audioBlob) return;
    setAnalyzing(true);
    setMessage("");
    setAnalysis(null);
    try {
      const form = new FormData();
      form.append("reference_text", selected.reference_text);
      form.append("target_id", selected.target_id);
      form.append("adaptation_mode", "reference");
      form.append("audio", audioBlob, `speech-lab-${selected.target_id}.webm`);
      const response = await fetch("/api/admin/speech-lab/analyze", { method: "POST", body: form });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تحليل التسجيل");
      setAnalysis(data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "تعذر تحليل التسجيل");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return <div className={styles.loading}>جاري تجهيز محتوى مختبر الصوت...</div>;
  }

  return (
    <div className={styles.page} data-testid="speech-lab-page">
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>أدوات التحقق والمعايرة</p>
          <h1>مختبر تحليل القراءة</h1>
          <p className={styles.intro}>اختبر أهداف القراءة المعتمدة مباشرة من كتالوج هِمّة. نتائج هذه الصفحة تجريبية ولا تغيّر درجات الطلاب أو قرارات التكيف.</p>
        </div>
        <div className={`${styles.providerBadge} ${provider?.configured ? styles.ready : styles.notReady}`}>
          <span className={styles.statusDot} aria-hidden="true" />
          <div><strong>{provider?.configured ? "المزود متصل" : "المزود غير مهيأ"}</strong><small>{provider?.provider || "Google STT V2 بانتظار بيانات الاتصال"}</small></div>
        </div>
      </header>

      {message && <div className={styles.notice} role="status">{message}</div>}

      <section className={styles.workspace}>
        <aside className={styles.catalogPanel}>
          <div className={styles.panelTitle}><h2>محتوى القراءة</h2><span>{filtered.length} هدف</span></div>
          <label className={styles.field}><span>القسم</span><select value={group} onChange={(event) => { setGroup(event.target.value); resetForCatalogChange(); }}>{groups.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className={styles.field}><span>بحث</span><input value={query} onChange={(event) => { setQuery(event.target.value); resetForCatalogChange(); }} placeholder="كلمة، مهارة، أو رمز المحتوى" /></label>
          <div className={styles.targetList}>
            {filtered.map((target) => <button key={target.target_id} className={`${styles.targetButton} ${target.target_id === effectiveSelectedId ? styles.targetActive : ""}`} onClick={() => { setSelectedId(target.target_id); replaceAudio(null); }}><span className={styles.targetCode}>{target.canonical_id} · {target.round_index}</span><strong>{target.reference_text}</strong><small>{target.skill_name || target.title}</small></button>)}
            {!filtered.length && <div className={styles.empty}>لا توجد أهداف تطابق التصفية الحالية.</div>}
          </div>
        </aside>

        <main className={styles.testPanel}>
          {selected ? <>
            <div className={styles.testMeta}><div><span>{selected.canonical_id}</span><span>{selected.skill_name}</span></div><span className={styles.interaction}>{selected.interaction_type === "timed_read_aloud" ? "قراءة مؤقتة" : "قراءة جهرية"}</span></div>
            <div className={styles.referenceCard}><span>النص المرجعي</span><p>{selected.reference_text}</p></div>
            <div className={styles.recorderCard}>
              <div className={styles.recorderText}><h2>{recording ? "جاري التسجيل" : audioBlob ? "التسجيل جاهز" : "سجّل القراءة"}</h2><p>{recording ? "اقرأ النص كما هو ظاهر، ثم أوقف التسجيل." : "يمكنك إعادة التسجيل في أي وقت قبل التحليل."}</p></div>
              <div className={styles.actions}>
                {!recording ? <button className={styles.primaryButton} onClick={startRecording}><Mic size={20} />{audioBlob ? "إعادة التسجيل" : "بدء التسجيل"}</button> : <button className={styles.stopButton} onClick={stopRecording}><Square size={19} />إيقاف التسجيل</button>}
                {audioUrl && <audio className={styles.audio} controls src={audioUrl} />}
                <button className={styles.analyzeButton} disabled={!audioBlob || analyzing || recording || !provider?.configured} onClick={analyze}><Upload size={19} />{analyzing ? "جاري التحليل..." : "تحليل القراءة"}</button>
              </div>
              {!provider?.configured && <p className={styles.providerHint}>واجهة المختبر جاهزة. يلزم تهيئة Google Cloud STT V2 على الخادم لتشغيل التحليل الحقيقي.</p>}
            </div>

            {analysis && <section className={styles.results} aria-live="polite">
              <div className={styles.resultHeader}><div><span>نتيجة المختبر</span><h2>{analysis.provider} {analysis.model ? `· ${analysis.model}` : ""}</h2></div><div className={styles.accuracy}><strong>{percent(analysis.lexical_accuracy)}</strong><span>تطابق لفظي</span></div></div>
              <div className={styles.metrics}>
                <div><span>ثقة المزود</span><strong>{percent(analysis.provider_confidence)}</strong></div>
                <div><span>صحيح</span><strong>{analysis.counts.correct || 0}</strong></div>
                <div><span>حذف</span><strong>{analysis.counts.deletion || 0}</strong></div>
                <div><span>إضافة</span><strong>{analysis.counts.insertion || 0}</strong></div>
                <div><span>استبدال</span><strong>{analysis.counts.substitution || 0}</strong></div>
                <div><span>WER</span><strong>{percent(analysis.wer)}</strong></div>
              </div>
              <div className={styles.transcripts}><div><span>النص الخام من المزود</span><p>{analysis.raw_transcript || "لم يرجع المزود نصًا."}</p></div><div><span>بعد التطبيع للمحاذاة</span><p>{analysis.normalized_transcript || "—"}</p></div></div>
              <div className={styles.alignmentWrap}><h3>المحاذاة مع النص المرجعي</h3><div className={styles.alignmentTable} role="table"><div className={styles.tableHead} role="row"><span>المرجع</span><span>المسموع</span><span>التصنيف</span></div>{analysis.alignment.map((row, index) => <div className={styles.tableRow} role="row" key={`${index}-${row.kind}`}><span>{row.reference || "—"}</span><span>{row.hypothesis || "—"}</span><span className={`${styles.tokenKind} ${styles[row.kind]}`}>{kindLabel[row.kind]}</span></div>)}</div></div>
              <div className={styles.safetyNote}>هذه النتيجة دليل مختبري فقط. تقييم الحركات والنطق الدقيق غير معتمد حتى تتم المعايرة، ولا يوجد أي أثر أكاديمي لهذه التجربة.</div>
            </section>}
          </> : <div className={styles.empty}>اختر هدف قراءة لبدء الاختبار.</div>}
        </main>
      </section>
    </div>
  );
}
