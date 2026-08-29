"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, Square, Upload } from "lucide-react";
import styles from "./speech-lab.module.css";

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

type AcousticEvidenceUnit = {
  unit_index: number;
  grapheme: string;
  base: string;
  expected_vowel_class: string | null;
  contrast_vowel_classes: string[];
  expects_gemination: boolean;
  expects_tanween: string | null;
  acoustic_score: number | null;
  acoustic_label: string | null;
  evidence_status: string;
};

type AcousticEvidencePlan = {
  status: string;
  reference_text: string;
  target_type: TargetType;
  stt_locale: string;
  azure_pronunciation_assessment: {
    enabled_for_judgement: boolean;
    candidate_locales: string[];
    note: string;
  };
  direct_haraka_judgement: boolean;
  requires_ground_truth: boolean;
  calibration_version: string | null;
  units: AcousticEvidenceUnit[];
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
  acoustic_evidence: AcousticEvidencePlan;
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

const targetTypeLabel: Record<TargetType, string> = {
  single_letter: "حرف",
  letter_with_haraka: "حرف مع حركة",
  syllable: "مقطع",
  word: "كلمة",
  sentence: "جملة",
  passage: "نص",
};

const vowelClassLabel: Record<string, string> = {
  fatha: "فتحة",
  kasra: "كسرة",
  damma: "ضمة",
  sukun: "سكون",
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
        <div>
          <span>المرجع النطقي التجريبي</span>
          <h2>{targetTypeLabel[reference.target_type]}</h2>
        </div>
        <span className={styles.calibrationBadge}>الحكم الصوتي على الحركة: غير معاير بعد</span>
      </div>
      <p className={styles.pronunciationExplain}>
        هذا التفكيك مستخرج من النص المشكول نفسه، وليس حكمًا على التسجيل. نستخدمه لاحقًا لمقارنة الحرف والحركة صوتيًا بعد المعايرة.
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

function AcousticEvidencePanel({ plan }: { plan: AcousticEvidencePlan | null }) {
  if (!plan) return <div className={styles.pronunciationLoading}>جاري تجهيز خطة الأدلة الصوتية...</div>;
  return (
    <section className={styles.pronunciationPanel} data-testid="acoustic-evidence-panel">
      <div className={styles.pronunciationHeader}>
        <div>
          <span>المعايرة وجمع العينات</span>
          <h2>خطة الأدلة الصوتية التجريبية</h2>
        </div>
        <span className={styles.calibrationBadge}>غير معاير — لا توجد درجة معتمدة</span>
      </div>
      <p className={styles.pronunciationExplain}>
        هذه الخطة تحدد ما نحتاج جمعه ومعايرته لكل حرف وحركة. ثقة Azure ونتيجة التعرف النصي لا تتحولان إلى درجة نطق أو حركة.
      </p>
      <div className={styles.pronunciationUnits}>
        <div className={styles.pronunciationUnit}>
          <strong dir="ltr">{plan.stt_locale}</strong>
          <span>لغة التعرف النصي الحالية</span>
          <span>الحكم المباشر على الحركة: غير مفعّل</span>
        </div>
        <div className={styles.pronunciationUnit}>
          <strong dir="ltr">{plan.azure_pronunciation_assessment.candidate_locales.join(" / ") || "—"}</strong>
          <span>لغات Azure المرشحة للمقارنة فقط</span>
          <span>ليست حكمًا مباشرًا على الفتحة أو الكسرة أو الضمة</span>
        </div>
        {plan.units.map((unit) => (
          <div className={styles.pronunciationUnit} key={`acoustic-${unit.unit_index}`}>
            <strong>{unit.grapheme}</strong>
            <span>الحرف المرجعي: {unit.base}</span>
            <span>الحركة المرجعية: {unit.expected_vowel_class ? (vowelClassLabel[unit.expected_vowel_class] || unit.expected_vowel_class) : "—"}</span>
            {unit.contrast_vowel_classes.length > 0 && (
              <span>مقارنات مطلوبة: {unit.contrast_vowel_classes.map((value) => vowelClassLabel[value] || value).join("، ")}</span>
            )}
            {unit.expects_gemination && <span>الشدة المرجعية: مطلوبة</span>}
            {unit.expects_tanween && <span>التنوين المرجعي: موجود</span>}
            <span data-testid={`acoustic-score-${unit.unit_index}`}>الدرجة الصوتية: {unit.acoustic_score === null ? "—" : percent(unit.acoustic_score)}</span>
            <small>الحالة: بانتظار المعايرة البشرية</small>
          </div>
        ))}
      </div>
      <div className={styles.pronunciationSafety}>
        يلزم Ground Truth بشري وتسجيلات ممثلة قبل اعتماد أي حد أو تصنيف. هذه الخطة لا تغيّر درجة الطالب ولا التكيف ولا التقوية.
      </div>
    </section>
  );
}

export default function SpeechLabPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [group, setGroup] = useState("all");
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState<{ configured: boolean; provider: string | null; detail?: string } | null>(null);
  const [pronunciationReference, setPronunciationReference] = useState<PronunciationReference | null>(null);
  const [acousticPlan, setAcousticPlan] = useState<AcousticEvidencePlan | null>(null);
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
    return () => { active = false; };
  }, []);

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

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
    if (!referenceText) {
      setPronunciationReference(null);
      setAcousticPlan(null);
      return () => { active = false; };
    }

    const loadEvidence = async () => {
      setPronunciationReference(null);
      setAcousticPlan(null);
      try {
        const encoded = encodeURIComponent(referenceText);
        const [pronunciationResponse, acousticResponse] = await Promise.all([
          fetch(`/api/admin/speech-lab/pronunciation-reference?reference_text=${encoded}`, { cache: "no-store" }),
          fetch(`/api/admin/speech-lab/acoustic-plan?reference_text=${encoded}`, { cache: "no-store" }),
        ]);
        const pronunciationData = await pronunciationResponse.json();
        const acousticData = await acousticResponse.json();
        if (!pronunciationResponse.ok) throw new Error(pronunciationData?.detail || "تعذر تجهيز المرجع النطقي");
        if (!acousticResponse.ok) throw new Error(acousticData?.detail || "تعذر تجهيز خطة الأدلة الصوتية");
        if (!active) return;
        setPronunciationReference(pronunciationData);
        setAcousticPlan(acousticData);
      } catch (error) {
        if (active) setMessage(error instanceof Error ? error.message : "تعذر تجهيز الأدلة الصوتية");
      }
    };
    void loadEvidence();
    return () => { active = false; };
  }, [selected?.target_id, selected?.reference_text]);

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
      if (data?.pronunciation_reference) setPronunciationReference(data.pronunciation_reference);
      if (data?.acoustic_evidence) setAcousticPlan(data.acoustic_evidence);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "تعذر تحليل التسجيل");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className={styles.loading}>جاري تجهيز محتوى مختبر الصوت...</div>;

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
          <div><strong>{provider?.configured ? "المزود متصل" : "المزود غير مهيأ"}</strong><small>{provider?.provider || "Azure Speech بانتظار بيانات الاتصال"}</small></div>
        </div>
      </header>

      {message && <div className={styles.notice} role="status">{message}</div>}

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
            <AcousticEvidencePanel plan={acousticPlan} />

            <div className={styles.recorderCard}>
              <div className={styles.recorderText}><h2>{recording ? "جاري التسجيل" : audioBlob ? "التسجيل جاهز" : "سجّل القراءة"}</h2><p>{recording ? "اقرأ النص كما هو ظاهر، ثم أوقف التسجيل." : "يمكنك إعادة التسجيل في أي وقت قبل التحليل."}</p></div>
              <div className={styles.actions}>
                {!recording ? <button className={styles.primaryButton} onClick={startRecording}><Mic size={20} />{audioBlob ? "إعادة التسجيل" : "بدء التسجيل"}</button> : <button className={styles.stopButton} onClick={stopRecording}><Square size={19} />إيقاف التسجيل</button>}
                {audioUrl && <audio className={styles.audio} controls src={audioUrl} />}
                <button className={styles.analyzeButton} data-testid="speech-lab-analyze" disabled={!audioBlob || analyzing || recording || !provider?.configured} onClick={analyze}><Upload size={19} />{analyzing ? "جاري التحليل..." : "تحليل القراءة"}</button>
              </div>
              {!provider?.configured && <p className={styles.providerHint}>واجهة المختبر جاهزة. يلزم تهيئة Azure Speech على الخادم لتشغيل التحليل الحقيقي.</p>}
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
              <div className={styles.safetyNote}>نتيجة Azure هنا تقيس التعرف النصي والمحاذاة فقط. تقييم الحرف والحركة والشدة والسكون صوتيًا غير معتمد حتى تتم المعايرة، ولا يوجد أي أثر أكاديمي لهذه التجربة.</div>
            </section>}
          </> : <div className={styles.empty}>اختر هدف قراءة لبدء الاختبار.</div>}
        </main>
      </section>
    </div>
  );
}
