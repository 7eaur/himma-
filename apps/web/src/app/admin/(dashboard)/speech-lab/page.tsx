"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, Square, Upload } from "lucide-react";
import styles from "./speech-lab.module.css";
import { PcmWavRecorder } from "./wav-recorder";

type TargetType = "single_letter" | "letter_with_haraka" | "syllable" | "word" | "sentence" | "passage";
type SpeechMode = "targeted_pronunciation" | "lexical" | "fluency" | "unclassified";

type PronunciationUnit = {
  grapheme: string;
  base: string;
  vowel: string | null;
  vowel_name: string | null;
  vowel_symbol: string | null;
  geminated: boolean;
  sukun: boolean;
  tanween: string | null;
  tanween_name: string | null;
  phonetic_hint: string;
};

type PronunciationReference = {
  target_type: TargetType;
  reference_text: string;
  units: PronunciationUnit[];
  has_diacritics: boolean;
  acoustic_status: "not_calibrated";
  academic_effect: "none";
};

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
  pronunciation_target_type: TargetType;
  has_diacritics: boolean;
  speech_mode: SpeechMode;
  pronunciation_focus: string | null;
  lexical_reference: string;
};

type AlignmentRow = {
  kind: "correct" | "deletion" | "insertion" | "substitution";
  reference: string | null;
  hypothesis: string | null;
};

type PronunciationAssessment = {
  provider: string;
  locale: string;
  transcript: string;
  confidence: number | null;
  accuracy_score: number | null;
  fluency_score: number | null;
  completeness_score: number | null;
  pronunciation_score: number | null;
  pronunciation_focus: string | null;
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
  pronunciation_reference: PronunciationReference | null;
  academic_effect: "none";
  pronunciation_status: string;
  speech_mode: SpeechMode;
  pronunciation_focus: string | null;
  analysis_path: string;
  fluency: {
    client_duration_seconds: number | null;
    provider_duration_seconds: number | null;
    reference_word_count: number;
  } | null;
  decision_preview: {
    state: "correct" | "incorrect" | "retry_required";
    reason: string;
    academic_effect: "none";
  };
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

const targetTypeLabel: Record<TargetType, string> = {
  single_letter: "حرف",
  letter_with_haraka: "حرف مع حركة",
  syllable: "مقطع",
  word: "كلمة",
  sentence: "جملة",
  passage: "نص",
};

const decisionLabel = {
  correct: "صحيح",
  incorrect: "خطأ",
  retry_required: "أعد التسجيل / يحتاج دليل إضافي",
} as const;

const speechModeLabel: Record<SpeechMode, string> = {
  targeted_pronunciation: "نطق مستهدف",
  lexical: "قراءة نصية",
  fluency: "طلاقة",
  unclassified: "غير مصنف",
};

function percent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 1000) / 10}%`;
}

function PronunciationPanel({ reference }: { reference: PronunciationReference | null }) {
  if (!reference) return <div className={styles.pronunciationLoading}>جاري تجهيز المرجع النطقي...</div>;
  return (
    <section className={styles.pronunciationPanel} data-testid="pronunciation-reference-panel">
      <div className={styles.pronunciationHeader}>
        <div><span>المرجع النطقي التجريبي</span><h2>{targetTypeLabel[reference.target_type]}</h2></div>
        <span className={styles.calibrationBadge}>مرجع النطق المستهدف</span>
      </div>
      <p className={styles.pronunciationExplain}>هذا يوضح الجزء الذي نهتم بنطقه في المهمة القصيرة. الحكم الفعلي يأتي من التسجيل ونتيجة مزود النطق، وليس من شكل النص وحده.</p>
      <div className={styles.pronunciationUnits}>
        {reference.units.map((unit, index) => (
          <div className={styles.pronunciationUnit} key={`${unit.grapheme}-${index}`}>
            <strong>{unit.grapheme}</strong><span>الحرف: {unit.base}</span><span>الحركة: {unit.vowel_name || (unit.sukun ? "سكون" : "—")}</span>
            {unit.geminated && <span>الشدة: موجودة</span>}{unit.tanween_name && <span>{unit.tanween_name}</span>}<small dir="ltr">{unit.phonetic_hint}</small>
          </div>
        ))}
      </div>
      <div className={styles.pronunciationSafety}>إذا لم تكن النتيجة واضحة فلن نعتبر الطفل مخطئًا؛ نطلب إعادة التسجيل.</div>
    </section>
  );
}

export default function SpeechLabPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [group, setGroup] = useState("all");
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState<{
    lexical: { configured: boolean; provider: string | null; detail?: string };
    pronunciation: { configured: boolean; provider: string; locale?: string; detail?: string };
  } | null>(null);
  const [pronunciationReference, setPronunciationReference] = useState<PronunciationReference | null>(null);
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [pronunciationAssessment, setPronunciationAssessment] = useState<PronunciationAssessment | null>(null);
  const [message, setMessage] = useState("");
  const recorderRef = useRef<PcmWavRecorder | null>(null);
  const recordingStartedAtRef = useRef<number | null>(null);
  const [clientDurationSeconds, setClientDurationSeconds] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [targetsResponse, providerResponse] = await Promise.all([fetch("/api/admin/speech-lab/targets", { cache: "no-store" }), fetch("/api/admin/speech-lab/provider", { cache: "no-store" })]);
        const targetData = await targetsResponse.json(); const providerData = await providerResponse.json();
        if (!targetsResponse.ok) throw new Error(targetData?.detail || "تعذر تحميل محتوى القراءة");
        if (!providerResponse.ok) throw new Error(providerData?.detail || "تعذر قراءة حالة المزود");
        if (!active) return;
        setTargets(targetData.targets || []); setSelectedId(targetData.targets?.[0]?.target_id || ""); setProvider(providerData);
      } catch (error) { if (active) setMessage(error instanceof Error ? error.message : "تعذر تجهيز مختبر الصوت"); }
      finally { if (active) setLoading(false); }
    };
    void load(); return () => { active = false; };
  }, []);

  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ar");
    return targets.filter((target) => {
      const groupOk = group === "all" || target.group === group;
      const queryOk = !needle || `${target.canonical_id} ${target.title} ${target.reference_text} ${target.skill_name || ""}`.toLocaleLowerCase("ar").includes(needle);
      return groupOk && queryOk;
    });
  }, [targets, group, query]);

  const effectiveSelectedId = filtered.some((target) => target.target_id === selectedId) ? selectedId : filtered[0]?.target_id || "";
  const selected = filtered.find((target) => target.target_id === effectiveSelectedId) || null;

  useEffect(() => {
    let active = true;
    const referenceText = selected?.reference_text;
    if (!referenceText || selected?.speech_mode !== "targeted_pronunciation") {
      return () => { active = false; };
    }
    const loadReference = async () => {
      try {
        const encoded = encodeURIComponent(referenceText);
        const response = await fetch(`/api/admin/speech-lab/pronunciation-reference?reference_text=${encoded}`, { cache: "no-store" });
        const data = await response.json();
        if (!response.ok) throw new Error(data?.detail || "تعذر تجهيز المرجع النطقي");
        if (active) setPronunciationReference(data);
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "تعذر تجهيز المرجع النطقي");
      }
    };
    void loadReference();
    return () => { active = false; };
  }, [selected?.target_id, selected?.reference_text, selected?.speech_mode]);

  const replaceAudio = (blob: Blob | null) => {
    setAnalysis(null); setPronunciationAssessment(null); setAudioBlob(blob);
    setAudioUrl((previous) => { if (previous) URL.revokeObjectURL(previous); return blob ? URL.createObjectURL(blob) : null; });
  };
  const resetForCatalogChange = () => { setSelectedId(""); replaceAudio(null); setMessage(""); };

  const startRecording = async () => {
    setMessage(""); if (!selected) return;
    try {
      const recorder = new PcmWavRecorder();
      await recorder.start();
      recorderRef.current = recorder;
      recordingStartedAtRef.current = performance.now();
      setClientDurationSeconds(null);
      setRecording(true);
    } catch {
      recorderRef.current?.cancel();
      recorderRef.current = null;
      setMessage("لم نتمكن من استخدام الميكروفون. تحقق من إذن المتصفح ثم حاول مرة أخرى.");
    }
  };
  const stopRecording = async () => {
    const recorder = recorderRef.current;
    if (!recorder) return;
    try {
      const blob = await recorder.stop();
      const startedAt = recordingStartedAtRef.current;
      setClientDurationSeconds(startedAt == null ? null : Math.max(0, (performance.now() - startedAt) / 1000));
      replaceAudio(blob);
    } catch {
      recorder.cancel();
      setMessage("تعذر تجهيز التسجيل بصيغة WAV. أعد التسجيل.");
    } finally {
      recorderRef.current = null;
      recordingStartedAtRef.current = null;
      setRecording(false);
    }
  };

  const analyze = async () => {
    if (!selected || !audioBlob) return;
    setAnalyzing(true); setMessage(""); setAnalysis(null); setPronunciationAssessment(null);
    try {
      const makeForm = () => {
        const form = new FormData();
        form.append("reference_text", selected.reference_text);
        form.append("target_id", selected.target_id);
        form.append("adaptation_mode", "reference");
        if (clientDurationSeconds != null) form.append("client_duration_seconds", String(clientDurationSeconds));
        form.append("audio", audioBlob, `speech-lab-${selected.target_id}.wav`);
        return form;
      };

      const lexicalPromise = fetch("/api/admin/speech-lab/analyze", { method: "POST", body: makeForm() });
      const pronunciationPromise = selected.speech_mode === "targeted_pronunciation" && provider?.pronunciation.configured
        ? fetch("/api/admin/speech-lab/pronunciation-assess", { method: "POST", body: makeForm() })
        : null;

      const response = await lexicalPromise;
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تحليل التسجيل");
      setAnalysis(data);

      if (pronunciationPromise) {
        const pronunciationResponse = await pronunciationPromise;
        const pronunciationData = await pronunciationResponse.json().catch(() => null);
        if (!pronunciationResponse.ok) throw new Error(pronunciationData?.detail || "تعذر تقييم النطق المستهدف");
        setPronunciationAssessment(pronunciationData);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "تعذر تحليل التسجيل");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className={styles.loading}>جاري تجهيز محتوى مختبر الصوت...</div>;

  return (
    <div className={styles.page} data-testid="speech-lab-page">
      <header className={styles.header}><div><p className={styles.eyebrow}>اختبار النموذج الصوتي</p><h1>مختبر تحليل القراءة</h1><p className={styles.intro}>جرّب القراءة كما سيستخدمها الطالب: قراءة نصية للجمل والنصوص، ونطق مستهدف للحروف والكلمات الحساسة.</p></div><div className={`${styles.providerBadge} ${provider?.lexical.configured ? styles.ready : styles.notReady}`}><span className={styles.statusDot} aria-hidden="true" /><div><strong>{provider?.lexical.configured ? "مزود القراءة متصل" : "مزود القراءة غير مهيأ"}</strong><small>{provider?.lexical.provider || "مزود ASR بانتظار بيانات الاتصال"}</small></div></div></header>
      {message && <div className={styles.notice} role="status">{message}</div>}
      <section className={styles.workspace}>
        <aside className={styles.catalogPanel}><div className={styles.panelTitle}><h2>محتوى القراءة</h2><span>{filtered.length} هدف</span></div><label className={styles.field}><span>القسم</span><select value={group} onChange={(event) => { setGroup(event.target.value); resetForCatalogChange(); }}>{groups.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className={styles.field}><span>بحث</span><input value={query} onChange={(event) => { setQuery(event.target.value); resetForCatalogChange(); }} placeholder="كلمة، مهارة، أو رمز المحتوى" /></label><div className={styles.targetList}>{filtered.map((target) => <button key={target.target_id} className={`${styles.targetButton} ${target.target_id === effectiveSelectedId ? styles.targetActive : ""}`} onClick={() => { setSelectedId(target.target_id); replaceAudio(null); }}><span className={styles.targetCode}>{target.canonical_id} · {target.round_index}</span><strong>{target.reference_text}</strong><small>{target.skill_name || target.title}</small><span className={styles.targetBadges}><span>{speechModeLabel[target.speech_mode]}</span><span>{targetTypeLabel[target.pronunciation_target_type]}</span></span></button>)}{!filtered.length && <div className={styles.empty}>لا توجد أهداف تطابق التصفية الحالية.</div>}</div></aside>
        <main className={styles.testPanel}>
          {selected ? <>
            <div className={styles.testMeta}><div><span>{selected.canonical_id}</span><span>{selected.skill_name}</span></div><span className={styles.interaction}>{selected.interaction_type === "timed_read_aloud" ? "قراءة مؤقتة" : "قراءة جهرية"}</span></div>
            <div className={styles.referenceCard}><span>النص المرجعي</span><p>{selected.reference_text}</p><div className={styles.referenceBadges}><span>{speechModeLabel[selected.speech_mode]}</span><span>{targetTypeLabel[selected.pronunciation_target_type]}</span></div></div>
            {selected.speech_mode === "targeted_pronunciation" && <>
              <PronunciationPanel reference={pronunciationReference?.reference_text === selected.reference_text ? pronunciationReference : null} />
            </>}
            <div className={styles.recorderCard}><div className={styles.recorderText}><h2>{recording ? "جاري التسجيل" : audioBlob ? "التسجيل جاهز" : "سجّل القراءة"}</h2><p>{recording ? "اقرأ النص كما هو ظاهر، ثم أوقف التسجيل." : "يمكنك إعادة التسجيل في أي وقت قبل التحليل."}</p></div><div className={styles.actions}>{!recording ? <button className={styles.primaryButton} onClick={startRecording}><Mic size={20} />{audioBlob ? "إعادة التسجيل" : "بدء التسجيل"}</button> : <button className={styles.stopButton} onClick={() => void stopRecording()}><Square size={19} />إيقاف التسجيل</button>}{audioUrl && <audio className={styles.audio} controls src={audioUrl} />}<button className={styles.analyzeButton} data-testid="speech-lab-analyze" disabled={!audioBlob || analyzing || recording || !provider?.lexical.configured || selected.speech_mode === "unclassified"} onClick={analyze}><Upload size={19} />{analyzing ? "جاري التحليل..." : "تحليل القراءة"}</button></div>{!provider?.lexical.configured && <p className={styles.providerHint}>واجهة المختبر جاهزة. يلزم تهيئة مزود ASR على الخادم لتشغيل التحليل الحقيقي.</p>}
              {selected.speech_mode === "unclassified" && <p className={styles.providerHint}>هذا المحتوى يحتاج Speech Profile صريح قبل التحليل.</p>}</div>
            {pronunciationAssessment && <section className={styles.results} aria-live="polite">
              <div className={styles.resultHeader}><div><span>تقييم النطق المستهدف</span><h2>{pronunciationAssessment.provider} · {pronunciationAssessment.locale}</h2></div><div className={styles.accuracy}><strong>{percent(pronunciationAssessment.pronunciation_score == null ? null : pronunciationAssessment.pronunciation_score / 100)}</strong><span>درجة النطق التجريبية</span></div></div>
              <div className={styles.metrics}><div><span>الدقة</span><strong>{percent(pronunciationAssessment.accuracy_score == null ? null : pronunciationAssessment.accuracy_score / 100)}</strong></div><div><span>الطلاقة</span><strong>{percent(pronunciationAssessment.fluency_score == null ? null : pronunciationAssessment.fluency_score / 100)}</strong></div><div><span>الاكتمال</span><strong>{percent(pronunciationAssessment.completeness_score == null ? null : pronunciationAssessment.completeness_score / 100)}</strong></div><div><span>ثقة التعرف</span><strong>{percent(pronunciationAssessment.confidence)}</strong></div></div>
              <div className={styles.transcripts}><div><span>النص الذي تعرف عليه مزود النطق</span><p>{pronunciationAssessment.transcript || "—"}</p></div><div><span>الهدف التعليمي</span><p>{selected?.pronunciation_focus || "نطق مستهدف"}</p></div></div>
              <div className={styles.safetyNote}>هذه النتيجة تجريبية داخل المختبر فقط، وليست قرارًا أكاديميًا بعد.</div>
            </section>}
            {analysis && <section className={styles.results} aria-live="polite"><div className={styles.resultHeader}><div><span>نتيجة التعرف النصي</span><h2>{analysis.provider} {analysis.model ? `· ${analysis.model}` : ""}</h2><small>{decisionLabel[analysis.decision_preview.state]}</small></div><div className={styles.accuracy}><strong>{percent(analysis.lexical_accuracy)}</strong><span>تطابق لفظي</span></div></div><div className={styles.metrics}><div><span>ثقة المزود</span><strong>{percent(analysis.provider_confidence)}</strong></div><div><span>صحيح</span><strong>{analysis.counts.correct || 0}</strong></div><div><span>حذف</span><strong>{analysis.counts.deletion || 0}</strong></div><div><span>إضافة</span><strong>{analysis.counts.insertion || 0}</strong></div><div><span>استبدال</span><strong>{analysis.counts.substitution || 0}</strong></div><div><span>WER</span><strong>{percent(analysis.wer)}</strong></div></div><div className={styles.transcripts}><div><span>النص الخام من Azure</span><p>{analysis.raw_transcript || "لم يرجع المزود نصًا."}</p></div><div><span>بعد التطبيع للمحاذاة</span><p>{analysis.normalized_transcript || "—"}</p></div></div><div className={styles.alignmentWrap}><h3>المحاذاة مع النص المرجعي</h3><div className={styles.alignmentTable} role="table"><div className={styles.tableHead} role="row"><span>المرجع</span><span>المسموع</span><span>التصنيف</span></div>{analysis.alignment.map((row, index) => <div className={styles.tableRow} role="row" key={`${index}-${row.kind}`}><span>{row.reference || "—"}</span><span>{row.hypothesis || "—"}</span><span className={`${styles.tokenKind} ${styles[row.kind]}`}>{kindLabel[row.kind]}</span></div>)}</div></div><div className={styles.safetyNote}>نتيجة Azure هنا تقيس التعرف النصي والمحاذاة فقط. تقييم الحرف والحركة والشدة والسكون صوتيًا غير معتمد حتى تتم المعايرة، ولا يوجد أي أثر أكاديمي لهذه التجربة.</div></section>}
          </> : <div className={styles.empty}>اختر هدف قراءة لبدء الاختبار.</div>}
        </main>
      </section>
    </div>
  );
}
