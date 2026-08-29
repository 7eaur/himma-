"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, Square, Upload } from "lucide-react";
import styles from "./speech-lab.module.css";
import { PcmWavRecorder } from "./wav-recorder";

type TargetType = "single_letter" | "letter_with_haraka" | "syllable" | "word" | "sentence" | "passage";

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
  pronunciation_reference: PronunciationReference;
  academic_effect: "none";
  pronunciation_status: string;
};

type ProviderStatus = {
  configured: boolean;
  provider: string | null;
  detail?: string;
};

type PronunciationProviderStatus = ProviderStatus & {
  locale: string | null;
  calibration_status: "not_calibrated";
  academic_effect: "none";
};

type PronunciationWordResult = {
  word: string;
  accuracy_score_raw: number | null;
  error_type: string | null;
  offset_seconds: number | null;
  duration_seconds: number | null;
  phoneme_scores_raw: number[];
};

type PronunciationAssessment = {
  lab_only: true;
  target_id: string | null;
  provider: string;
  locale: string;
  recognition_status: string;
  transcript: string;
  confidence: number | null;
  accuracy_score_raw: number | null;
  fluency_score_raw: number | null;
  completeness_score_raw: number | null;
  pronunciation_score_raw: number | null;
  words: PronunciationWordResult[];
  request_id: string | null;
  calibration_status: "not_calibrated";
  interpretation: "raw_provider_evidence_only";
  academic_effect: "none";
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

function percent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 1000) / 10}%`;
}

function rawScore(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 10) / 10}/100`;
}

function PronunciationPanel({ reference }: { reference: PronunciationReference | null }) {
  if (!reference) return <div className={styles.pronunciationLoading}>جاري تجهيز المرجع النطقي...</div>;
  return (
    <section className={styles.pronunciationPanel} data-testid="pronunciation-reference-panel">
      <div className={styles.pronunciationHeader}>
        <div>
          <span>المرجع النطقي التجريبي</span>
          <h2>{targetTypeLabel[reference.target_type]}</h2>
        </div>
        <span className={styles.calibrationBadge}>الحكم الصوتي على الحركة: غير معاير بعد</span>
      </div>
      <p className={styles.pronunciationExplain}>
        هذا التفكيك مستخرج من النص المشكول نفسه، وليس حكمًا على تسجيلك. نستخدمه لاحقًا لمقارنة الحرف والحركة صوتيًا بعد المعايرة.
      </p>
      <div className={styles.pronunciationUnits}>
        {reference.units.map((unit, index) => (
          <div className={styles.pronunciationUnit} key={`${unit.grapheme}-${index}`}>
            <strong>{unit.grapheme}</strong>
            <span>الحرف: {unit.base}</span>
            <span>الحركة: {unit.vowel_name || (unit.sukun ? "سكون" : "—")}</span>
            {unit.geminated && <span>الشدة: موجودة</span>}
            {unit.tanween_name && <span>{unit.tanween_name}</span>}
            <small dir="ltr">{unit.phonetic_hint}</small>
          </div>
        ))}
      </div>
      <div className={styles.pronunciationSafety}>لا توجد درجة للحرف أو الحركة في هذه المرحلة، ولا يؤثر هذا المرجع في نتيجة الطالب.</div>
    </section>
  );
}

export default function SpeechLabPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [group, setGroup] = useState("all");
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState<ProviderStatus | null>(null);
  const [pronunciationProvider, setPronunciationProvider] = useState<PronunciationProviderStatus | null>(null);
  const [pronunciationReference, setPronunciationReference] = useState<PronunciationReference | null>(null);
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [pronunciationAssessment, setPronunciationAssessment] = useState<PronunciationAssessment | null>(null);
  const [message, setMessage] = useState("");
  const [pronunciationMessage, setPronunciationMessage] = useState("");
  const recorderRef = useRef<PcmWavRecorder | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [targetsResponse, providerResponse, pronunciationProviderResponse] = await Promise.all([
          fetch("/api/admin/speech-lab/targets", { cache: "no-store" }),
          fetch("/api/admin/speech-lab/provider", { cache: "no-store" }),
          fetch("/api/admin/speech-lab/pronunciation-provider", { cache: "no-store" }),
        ]);
        const targetData = await targetsResponse.json();
        const providerData = await providerResponse.json();
        const pronunciationProviderData = await pronunciationProviderResponse.json();
        if (!targetsResponse.ok) throw new Error(targetData?.detail || "تعذر تحميل محتوى القراءة");
        if (!providerResponse.ok) throw new Error(providerData?.detail || "تعذر قراءة حالة مزود التعرف النصي");
        if (!pronunciationProviderResponse.ok) throw new Error(pronunciationProviderData?.detail || "تعذر قراءة حالة مزود النطق");
        if (!active) return;
        setTargets(targetData.targets || []);
        setSelectedId(targetData.targets?.[0]?.target_id || "");
        setProvider(providerData);
        setPronunciationProvider(pronunciationProviderData);
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "تعذر تجهيز مختبر الصوت");
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
      recorderRef.current?.cancel();
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

  useEffect(() => {
    let active = true;
    const referenceText = selected?.reference_text;
    if (!referenceText) return () => { active = false; };
    const loadPronunciation = async () => {
      try {
        const response = await fetch(`/api/admin/speech-lab/pronunciation-reference?reference_text=${encodeURIComponent(referenceText)}`, { cache: "no-store" });
        const data = await response.json();
        if (!response.ok) throw new Error(data?.detail || "تعذر تجهيز المرجع النطقي");
        if (active) setPronunciationReference(data);
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "تعذر تجهيز المرجع النطقي");
      }
    };
    void loadPronunciation();
    return () => { active = false; };
  }, [selected?.target_id, selected?.reference_text]);

  const replaceAudio = (blob: Blob | null) => {
    setAnalysis(null);
    setPronunciationAssessment(null);
    setPronunciationMessage("");
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
    setPronunciationMessage("");
    if (!selected) return;
    try {
      const recorder = new PcmWavRecorder();
      await recorder.start();
      recorderRef.current = recorder;
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
    recorderRef.current = null;
    setRecording(false);
    try {
      const blob = await recorder.stop();
      replaceAudio(blob);
    } catch {
      recorder.cancel();
      setMessage("لم يلتقط المتصفح صوتًا صالحًا. أعد التسجيل وحاول مرة أخرى.");
    }
  };

  const runLexicalAnalysis = async () => {
    if (!selected || !audioBlob || !provider?.configured) return;
    const form = new FormData();
    form.append("reference_text", selected.reference_text);
    form.append("target_id", selected.target_id);
    form.append("adaptation_mode", "reference");
    form.append("audio", audioBlob, `speech-lab-${selected.target_id}.wav`);
    const response = await fetch("/api/admin/speech-lab/analyze", { method: "POST", body: form });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "تعذر تحليل التسجيل نصيًا");
    setAnalysis(data);
    if (data?.pronunciation_reference) setPronunciationReference(data.pronunciation_reference);
  };

  const runPronunciationAssessment = async () => {
    if (!selected || !audioBlob || !pronunciationProvider?.configured) return;
    const form = new FormData();
    form.append("reference_text", selected.reference_text);
    form.append("target_id", selected.target_id);
    form.append("audio", audioBlob, `speech-lab-${selected.target_id}.wav`);
    const response = await fetch("/api/admin/speech-lab/assess-pronunciation", { method: "POST", body: form });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "تعذر تشغيل التقييم النطقي");
    setPronunciationAssessment(data);
  };

  const analyze = async () => {
    if (!selected || !audioBlob) return;
    setAnalyzing(true);
    setMessage("");
    setPronunciationMessage("");
    setAnalysis(null);
    setPronunciationAssessment(null);
    try {
      const [lexicalResult, pronunciationResult] = await Promise.allSettled([
        runLexicalAnalysis(),
        runPronunciationAssessment(),
      ]);
      if (lexicalResult.status === "rejected") {
        setMessage(lexicalResult.reason instanceof Error ? lexicalResult.reason.message : "تعذر التحليل النصي");
      }
      if (pronunciationResult.status === "rejected") {
        setPronunciationMessage(pronunciationResult.reason instanceof Error ? pronunciationResult.reason.message : "تعذر التقييم النطقي");
      }
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return <div className={styles.loading}>جاري تجهيز محتوى مختبر الصوت...</div>;
  }

  const anyProviderConfigured = Boolean(provider?.configured || pronunciationProvider?.configured);

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
          <div><strong>{provider?.configured ? "التعرف النصي متصل" : "المزود غير مهيأ"}</strong><small>{provider?.provider || "Azure Speech بانتظار بيانات الاتصال"}</small></div>
        </div>
      </header>

      {message && <div className={styles.notice} role="status">{message}</div>}
      {pronunciationMessage && <div className={styles.notice} role="status">التقييم النطقي: {pronunciationMessage}</div>}

      <section className={styles.workspace}>
        <aside className={styles.catalogPanel}>
          <div className={styles.panelTitle}><h2>محتوى القراءة</h2><span>{filtered.length} هدف</span></div>
          <label className={styles.field}><span>القسم</span><select value={group} onChange={(event) => { setGroup(event.target.value); resetForCatalogChange(); }}>{groups.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className={styles.field}><span>بحث</span><input value={query} onChange={(event) => { setQuery(event.target.value); resetForCatalogChange(); }} placeholder="كلمة، مهارة، أو رمز المحتوى" /></label>
          <div className={styles.targetList}>
            {filtered.map((target) => <button key={target.target_id} className={`${styles.targetButton} ${target.target_id === effectiveSelectedId ? styles.targetActive : ""}`} onClick={() => { setSelectedId(target.target_id); replaceAudio(null); }}><span className={styles.targetCode}>{target.canonical_id} · {target.round_index}</span><strong>{target.reference_text}</strong><small>{target.skill_name || target.title}</small><span className={styles.targetBadges}><span>{targetTypeLabel[target.pronunciation_target_type]}</span>{target.has_diacritics && <span>مشكول</span>}</span></button>)}
            {!filtered.length && <div className={styles.empty}>لا توجد أهداف تطابق التصفية الحالية.</div>}
          </div>
        </aside>

        <main className={styles.testPanel}>
          {selected ? <>
            <div className={styles.testMeta}><div><span>{selected.canonical_id}</span><span>{selected.skill_name}</span></div><span className={styles.interaction}>{selected.interaction_type === "timed_read_aloud" ? "قراءة مؤقتة" : "قراءة جهرية"}</span></div>
            <div className={styles.referenceCard}><span>النص المرجعي</span><p>{selected.reference_text}</p><div className={styles.referenceBadges}><span>{targetTypeLabel[selected.pronunciation_target_type]}</span>{selected.has_diacritics && <span>يحتوي حركات</span>}</div></div>
            <PronunciationPanel reference={pronunciationReference} />
            <div className={styles.recorderCard}>
              <div className={styles.recorderText}><h2>{recording ? "جاري التسجيل" : audioBlob ? "التسجيل جاهز بصيغة WAV" : "سجّل القراءة"}</h2><p>{recording ? "اقرأ النص كما هو ظاهر، ثم أوقف التسجيل." : "يسجل المختبر PCM mono 16kHz ليستخدم الملف نفسه في التحليل النصي والنطقي."}</p></div>
              <div className={styles.actions}>
                {!recording ? <button className={styles.primaryButton} onClick={startRecording}><Mic size={20} />{audioBlob ? "إعادة التسجيل" : "بدء التسجيل"}</button> : <button className={styles.stopButton} onClick={() => { void stopRecording(); }}><Square size={19} />إيقاف التسجيل</button>}
                {audioUrl && <audio className={styles.audio} controls src={audioUrl} />}
                <button className={styles.analyzeButton} data-testid="speech-lab-analyze" disabled={!audioBlob || analyzing || recording || !anyProviderConfigured} onClick={() => { void analyze(); }}><Upload size={19} />{analyzing ? "جاري التحليل..." : "تشغيل التحليلين"}</button>
              </div>
              <p className={styles.providerHint}>التعرف النصي: {provider?.configured ? "جاهز ar-OM" : "غير مهيأ"} · التقييم النطقي: {pronunciationProvider?.configured ? `تجريبي ${pronunciationProvider.locale}` : "غير مهيأ"}</p>
              {!anyProviderConfigured && <p className={styles.providerHint}>واجهة المختبر جاهزة. يلزم تهيئة Azure Speech على الخادم لتشغيل التحليل الحقيقي.</p>}
            </div>

            {analysis && <section className={styles.results} aria-live="polite">
              <div className={styles.resultHeader}><div><span>نتيجة التعرف النصي</span><h2>{analysis.provider} {analysis.model ? `· ${analysis.model}` : ""}</h2></div><div className={styles.accuracy}><strong>{percent(analysis.lexical_accuracy)}</strong><span>تطابق لفظي</span></div></div>
              <div className={styles.metrics}>
                <div><span>ثقة المزود</span><strong>{percent(analysis.provider_confidence)}</strong></div>
                <div><span>صحيح</span><strong>{analysis.counts.correct || 0}</strong></div>
                <div><span>حذف</span><strong>{analysis.counts.deletion || 0}</strong></div>
                <div><span>إضافة</span><strong>{analysis.counts.insertion || 0}</strong></div>
                <div><span>استبدال</span><strong>{analysis.counts.substitution || 0}</strong></div>
                <div><span>WER</span><strong>{percent(analysis.wer)}</strong></div>
              </div>
              <div className={styles.transcripts}><div><span>النص الخام من Azure</span><p>{analysis.raw_transcript || "لم يرجع المزود نصًا."}</p></div><div><span>بعد التطبيع للمحاذاة</span><p>{analysis.normalized_transcript || "—"}</p></div></div>
              <div className={styles.alignmentWrap}><h3>المحاذاة مع النص المرجعي</h3><div className={styles.alignmentTable} role="table"><div className={styles.tableHead} role="row"><span>المرجع</span><span>المسموع</span><span>التصنيف</span></div>{analysis.alignment.map((row, index) => <div className={styles.tableRow} role="row" key={`${index}-${row.kind}`}><span>{row.reference || "—"}</span><span>{row.hypothesis || "—"}</span><span className={`${styles.tokenKind} ${styles[row.kind]}`}>{kindLabel[row.kind]}</span></div>)}</div></div>
              <div className={styles.safetyNote}>نتيجة Azure هنا تقيس التعرف النصي والمحاذاة فقط. لا تتحول هذه النتيجة تلقائيًا إلى حكم على الحركات.</div>
            </section>}

            {pronunciationAssessment && <section className={styles.results} data-testid="pronunciation-assessment-results" aria-live="polite">
              <div className={styles.resultHeader}><div><span>التقييم النطقي التجريبي</span><h2>{pronunciationAssessment.provider} · {pronunciationAssessment.locale}</h2></div><div className={styles.accuracy}><strong>{rawScore(pronunciationAssessment.pronunciation_score_raw)}</strong><span>درجة مزود خام</span></div></div>
              <div className={styles.metrics}>
                <div><span>الدقة النطقية الخام</span><strong>{rawScore(pronunciationAssessment.accuracy_score_raw)}</strong></div>
                <div><span>الطلاقة الخام</span><strong>{rawScore(pronunciationAssessment.fluency_score_raw)}</strong></div>
                <div><span>الاكتمال الخام</span><strong>{rawScore(pronunciationAssessment.completeness_score_raw)}</strong></div>
                <div><span>ثقة التعرف</span><strong>{percent(pronunciationAssessment.confidence)}</strong></div>
              </div>
              <div className={styles.transcripts}><div><span>النص الذي قيّمه Azure</span><p>{pronunciationAssessment.transcript || "—"}</p></div><div><span>حالة المعايرة</span><p>غير معاير — لا أثر أكاديمي</p></div></div>
              {pronunciationAssessment.words.length > 0 && <div className={styles.alignmentWrap}><h3>أدلة النطق على مستوى الكلمات</h3><div className={styles.alignmentTable} role="table"><div className={styles.tableHead} role="row"><span>الكلمة</span><span>دقة خام</span><span>فونيمات خام</span></div>{pronunciationAssessment.words.map((word, index) => <div className={styles.tableRow} role="row" key={`${word.word}-${index}`}><span>{word.word || "—"}</span><span>{rawScore(word.accuracy_score_raw)}</span><span dir="ltr">{word.phoneme_scores_raw.length ? word.phoneme_scores_raw.map((score) => Math.round(score * 10) / 10).join(" · ") : "—"}</span></div>)}</div></div>}
              <div className={styles.safetyNote}>هذه قيم Azure الخام للمعايرة فقط. لا نربط ترتيب درجات الفونيمات بحرف أو فتحة أو كسرة أو ضمة لأن أسماء الفونيمات العربية لا تُعاد هنا؛ الربط بالحركة سيعتمد فقط بعد مقارنة تسجيلات معلّمة بشريًا.</div>
            </section>}
          </> : <div className={styles.empty}>اختر هدف قراءة لبدء الاختبار.</div>}
        </main>
      </section>
    </div>
  );
}