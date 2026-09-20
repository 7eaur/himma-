"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import {
  BookOpenCheck,
  CheckCircle2,
  ChevronDown,
  FileAudio,
  Filter,
  ImageIcon,
  ListChecks,
  Mic2,
  RefreshCw,
  Search,
  Volume2,
} from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";

type Kind = "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
type Interaction = string;

interface Asset {
  asset_id: string;
  asset_type: string;
  usage?: string | null;
  semantic_text?: string | null;
  url: string;
  option_id?: number | null;
}
interface Option {
  id: number;
  text: string;
  order_index: number;
  is_correct: boolean;
}
interface AnswerContract {
  kind: "recording_target" | "ordered_sequence" | "correct_options" | "none";
  label: string;
  values: string[];
  option_ids: number[];
}
interface ReviewSummary {
  id: number;
  canonical_id: string;
  stable_key: string;
  kind: Kind;
  level_id?: number | null;
  order_index: number;
  interaction_type: Interaction;
  title: string;
  skill: string;
  status: string;
  round_count: number;
  has_audio: boolean;
  has_images: boolean;
  requires_recording: boolean;
  release_version?: string | null;
  release_sha256?: string | null;
}
interface ReviewIndex {
  mode: "read_only";
  purpose: "admin_content_review";
  writes_progress: false;
  count: number;
  items: ReviewSummary[];
  active_release?: { version: string; is_active: boolean; released_at?: string | null } | null;
}
interface ContextIntro {
  kind?: string;
  title?: string;
  instruction?: string;
  text?: string;
  audio_asset_id?: string;
  image_asset_id?: string;
}
interface ReviewRound {
  id: number;
  order_index: number;
  round_number: number;
  round_total: number;
  question_text: string;
  instruction_text: string;
  encouragement: string;
  hint: string;
  stimulus: { kind?: string; text?: string | null; audio_target?: string | null; audio_targets?: string[] | null };
  stimulus_text: string;
  expected_reading_text?: string | null;
  options: Option[];
  assets: Asset[];
  media_gaps: unknown[];
  answer: AnswerContract;
}
interface ReviewDetail {
  mode: "read_only";
  purpose: "admin_content_review";
  writes_progress: false;
  summary: ReviewSummary;
  item: {
    id: number;
    canonical_id: string;
    stable_key: string;
    kind: Kind;
    level_id?: number | null;
    order_index: number;
    interaction_type: Interaction;
    title: string;
    skill: string;
    criterion?: string | null;
    status: string;
    layout_hint?: string | null;
    context_intro?: ContextIntro | null;
    item_assets: Asset[];
  };
  rounds: ReviewRound[];
}

const KIND_LABEL: Record<Kind, string> = {
  pretest_question: "الاختبار القبلي",
  posttest_question: "الاختبار البعدي",
  core_activity: "نشاط أساسي",
  reinforcement_activity: "تقوية",
};

const INTERACTION_LABEL: Record<string, string> = {
  choose_one: "اختيار واحد",
  choose_many: "اختيار متعدد",
  choose_image: "اختيار صورة",
  listen_choose_one: "استماع واختيار",
  listen_choose_many: "استماع واختيار متعدد",
  listen_choose_image: "استماع واختيار صورة",
  sequence: "ترتيب",
  memory_sequence: "ترتيب من الذاكرة",
  path_sequence: "تسلسل",
  build_word: "بناء كلمة",
  read_aloud: "تسجيل قراءة",
  timed_read_aloud: "تسجيل قراءة موقّت",
};

function sectionKey(item: ReviewSummary) {
  if (item.kind === "pretest_question") return "pretest";
  if (item.kind === "posttest_question") return "posttest";
  return `l${item.level_id || 0}-${item.kind === "core_activity" ? "core" : "rein"}`;
}

function sectionLabel(key: string) {
  const labels: Record<string, string> = {
    pretest: "الاختبار القبلي",
    "l1-core": "المستوى الأول — الأنشطة",
    "l1-rein": "المستوى الأول — التقوية",
    "l2-core": "المستوى الثاني — الأنشطة",
    "l2-rein": "المستوى الثاني — التقوية",
    "l3-core": "المستوى الثالث — الأنشطة",
    "l3-rein": "المستوى الثالث — التقوية",
    posttest: "الاختبار البعدي",
  };
  return labels[key] || "محتوى آخر";
}

function interactionGroup(item: ReviewSummary) {
  if (item.requires_recording) return "recording";
  if (item.interaction_type.startsWith("listen_")) return "listening";
  if (["choose_image"].includes(item.interaction_type)) return "images";
  if (["sequence", "memory_sequence", "path_sequence", "build_word"].includes(item.interaction_type)) return "ordering";
  return "choice";
}

async function fetchIndex(): Promise<ReviewIndex> {
  const response = await fetch("/api/researcher/content-preview", { cache: "no-store" });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || "تعذر تحميل المحتوى المعتمد");
  return data as ReviewIndex;
}

async function fetchDetail(canonicalId: string): Promise<ReviewDetail> {
  const response = await fetch(`/api/researcher/content-preview/${encodeURIComponent(canonicalId)}`, { cache: "no-store" });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || "تعذر تحميل تفاصيل المحتوى");
  return data as ReviewDetail;
}

function MediaBlock({ assets, title = "الوسائط المعتمدة", hideMappedImages = false }: { assets: Asset[]; title?: string; hideMappedImages?: boolean }) {
  const visible = assets.filter((asset) => !(hideMappedImages && asset.asset_type === "image" && asset.option_id));
  if (!visible.length) return null;
  const audio = visible.filter((asset) => asset.asset_type === "audio");
  const images = visible.filter((asset) => asset.asset_type === "image");
  return <div className="rounded-2xl border border-border bg-bg p-4 space-y-4">
    <div className="text-sm font-extrabold text-navy flex items-center gap-2"><FileAudio size={17} className="text-primary" />{title}</div>
    {audio.map((asset) => <div key={`a-${asset.asset_id}-${asset.usage || ""}`} className="rounded-xl bg-white border border-border p-3 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-bold text-navy">{asset.semantic_text || asset.asset_id}</span>
        <span className="text-muted">{asset.usage || "audio"}</span>
      </div>
      <audio src={asset.url} controls preload="metadata" className="w-full" />
    </div>)}
    {images.length > 0 && <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">{images.map((asset) => <figure key={`i-${asset.asset_id}-${asset.usage || ""}`} className="rounded-xl border border-border bg-white p-3">
      <div className="min-h-36 flex items-center justify-center"><Image src={asset.url} alt={asset.semantic_text || "صورة معتمدة"} width={260} height={180} className="max-h-44 w-auto object-contain" unoptimized /></div>
      <figcaption className="mt-2 text-xs text-center text-muted">{asset.semantic_text || asset.asset_id}</figcaption>
    </figure>)}</div>}
  </div>;
}

function OptionsReview({ options, assets, answer }: { options: Option[]; assets: Asset[]; answer: AnswerContract }) {
  if (!options.length) return null;
  const imageByOption = new Map<number, Asset>();
  assets.forEach((asset) => {
    if (asset.asset_type === "image" && asset.option_id) imageByOption.set(Number(asset.option_id), asset);
  });
  const answerIds = new Set(answer.option_ids);
  return <div className="space-y-3">
    <div className="flex items-center gap-2 font-extrabold text-navy"><ListChecks size={18} className="text-primary" />الخيارات</div>
    <div className="grid md:grid-cols-2 gap-3">
      {options.map((option, index) => {
        const image = imageByOption.get(option.id);
        const isCorrect = option.is_correct || answerIds.has(option.id);
        return <div key={option.id} className={`rounded-2xl border p-4 space-y-3 ${isCorrect ? "border-emerald-300 bg-emerald-50/70" : "border-border bg-white"}`}>
          {image && <div className="min-h-36 flex items-center justify-center rounded-xl bg-bg border border-border">
            <Image src={image.url} alt={image.semantic_text || option.text || "خيار مصور"} width={240} height={160} className="max-h-40 w-auto object-contain" unoptimized />
          </div>}
          <div className="flex items-start gap-3">
            <span className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center text-sm font-extrabold ${isCorrect ? "bg-emerald-600 text-white" : "bg-bg text-primary"}`}>{index + 1}</span>
            <div className="min-w-0 flex-1">
              <div className="font-bold text-navy leading-7">{option.text || image?.semantic_text || "خيار مصور"}</div>
              {isCorrect && <div className="mt-1 inline-flex items-center gap-1 text-xs font-bold text-emerald-700"><CheckCircle2 size={14} />إجابة صحيحة</div>}
            </div>
          </div>
        </div>;
      })}
    </div>
  </div>;
}

function AnswerBlock({ answer }: { answer: AnswerContract }) {
  if (answer.kind === "none" || answer.values.length === 0) return null;
  const recording = answer.kind === "recording_target";
  return <div className={`rounded-2xl border p-4 ${recording ? "border-sky-200 bg-sky-50" : "border-emerald-200 bg-emerald-50"}`}>
    <div className={`text-sm font-extrabold flex items-center gap-2 ${recording ? "text-sky-800" : "text-emerald-800"}`}>
      {recording ? <Mic2 size={18} /> : <CheckCircle2 size={18} />}{answer.label}
    </div>
    {answer.kind === "ordered_sequence"
      ? <ol className="mt-3 flex flex-wrap gap-2">{answer.values.map((value, index) => <li key={`${index}-${value}`} className="rounded-full bg-white border border-emerald-200 px-3 py-2 text-sm font-bold text-navy"><span className="text-emerald-700 me-1">{index + 1}.</span>{value}</li>)}</ol>
      : <div className="mt-3 space-y-2">{answer.values.map((value, index) => <div key={`${index}-${value}`} className="rounded-xl bg-white/80 px-4 py-3 font-bold text-navy leading-8">{value}</div>)}</div>}
  </div>;
}

function ContextIntroReview({ intro, assets }: { intro?: ContextIntro | null; assets: Asset[] }) {
  if (!intro) return null;
  const attached = assets.filter((asset) =>
    (intro.audio_asset_id && asset.asset_id === intro.audio_asset_id)
    || (intro.image_asset_id && asset.asset_id === intro.image_asset_id)
  );
  return <AdminPanel title={intro.title || "مقدمة النشاط"} description={intro.kind === "audio_story" ? "مقدمة استماع معتمدة قبل الأسئلة" : "سياق قراءة معتمد قبل الأسئلة"}>
    <div className="space-y-4">
      {intro.text && <div className="rounded-2xl bg-bg border border-border p-5 text-lg font-bold text-navy leading-9">{intro.text}</div>}
      {intro.instruction && <div className="text-sm text-muted leading-7"><span className="font-bold text-navy">التعليمة: </span>{intro.instruction}</div>}
      <MediaBlock assets={attached} title="وسائط المقدمة" />
    </div>
  </AdminPanel>;
}

function RoundReview({ round, interaction }: { round: ReviewRound; interaction: Interaction }) {
  const stimulusText = String(round.stimulus_text || round.stimulus?.text || "").trim();
  return <details className="group rounded-3xl border border-border bg-white overflow-hidden" open={round.round_number === 1}>
    <summary className="cursor-pointer list-none px-5 py-4 flex items-center justify-between gap-4 bg-bg/70">
      <div>
        <div className="text-xs text-primary font-bold">الجولة {round.round_number} من {round.round_total}</div>
        <div className="font-extrabold text-navy mt-1 line-clamp-2">{round.question_text || "جولة محتوى"}</div>
      </div>
      <ChevronDown className="text-muted shrink-0 transition-transform group-open:rotate-180" size={20} />
    </summary>
    <div className="p-5 space-y-5">
      {round.encouragement && <div className="text-sm font-bold text-primary">{round.encouragement}</div>}
      <section>
        <div className="text-xs text-muted mb-1">السؤال المعروض</div>
        <div className="text-xl sm:text-2xl font-extrabold text-navy leading-10">{round.question_text}</div>
      </section>
      {stimulusText && <div className="rounded-2xl border border-border bg-bg p-5 text-center text-xl font-bold text-navy leading-9">{stimulusText}</div>}
      <div className="rounded-2xl border border-border bg-white p-4 text-sm leading-7 text-navy"><span className="font-extrabold">التعليمة للطالب: </span>{round.instruction_text}</div>
      {round.hint && <div className="rounded-2xl border border-dashed border-border p-4 text-sm leading-7 text-muted"><span className="font-extrabold text-navy">التلميح عند الخطأ: </span>{round.hint}</div>}
      <MediaBlock assets={round.assets} hideMappedImages title="الصوت والصور المرتبطة بالجولة" />
      <OptionsReview options={round.options} assets={round.assets} answer={round.answer} />
      <AnswerBlock answer={round.answer} />
      {round.media_gaps.length > 0 && <div className="alert-error">توجد فجوات وسائط مسجلة في هذه الجولة وتحتاج مراجعة.</div>}
      <div className="text-[11px] text-muted border-t border-border pt-3">نوع التفاعل: {INTERACTION_LABEL[interaction] || interaction} · رقم الجولة في قاعدة المحتوى: {round.order_index}</div>
    </div>
  </details>;
}

export default function ContentPreviewPage() {
  const [index, setIndex] = useState<ReviewIndex | null>(null);
  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [selected, setSelected] = useState("");
  const [section, setSection] = useState("all");
  const [interaction, setInteraction] = useState("all");
  const [media, setMedia] = useState("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  const loadIndex = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchIndex();
      setIndex(data);
      if (!selected && data.items.length) setSelected(data.items[0].canonical_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تعذر تحميل المحتوى المعتمد");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    void fetchIndex()
      .then((data) => {
        if (cancelled) return;
        setIndex(data);
        if (data.items.length) setSelected(data.items[0].canonical_id);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل المحتوى المعتمد");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ar");
    return (index?.items || []).filter((item) => {
      if (section !== "all" && sectionKey(item) !== section) return false;
      if (interaction !== "all" && interactionGroup(item) !== interaction) return false;
      if (media === "audio" && !item.has_audio) return false;
      if (media === "images" && !item.has_images) return false;
      if (media === "recording" && !item.requires_recording) return false;
      if (normalized) {
        const haystack = `${item.canonical_id} ${item.title} ${item.skill}`.toLocaleLowerCase("ar");
        if (!haystack.includes(normalized)) return false;
      }
      return true;
    });
  }, [index, section, interaction, media, query]);

  const effectiveSelected = filtered.some((item) => item.canonical_id === selected)
    ? selected
    : (filtered[0]?.canonical_id || "");

  useEffect(() => {
    if (!effectiveSelected) return;
    let cancelled = false;
    void fetchDetail(effectiveSelected)
      .then((data) => { if (!cancelled) setDetail(data); })
      .catch((caught: unknown) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل تفاصيل المحتوى"); })
      .finally(() => { if (!cancelled) setDetailLoading(false); });
    return () => { cancelled = true; };
  }, [effectiveSelected]);

  const grouped = useMemo(() => {
    const result: Array<{ key: string; label: string; items: ReviewSummary[] }> = [];
    for (const item of filtered) {
      const key = sectionKey(item);
      let group = result.find((value) => value.key === key);
      if (!group) {
        group = { key, label: sectionLabel(key), items: [] };
        result.push(group);
      }
      group.items.push(item);
    }
    return result;
  }, [filtered]);

  const current = detail && detail.summary.canonical_id === effectiveSelected ? detail : null;

  return <AdminPage>
    <AdminPageHeader
      eyebrow="إدارة المحتوى"
      icon={BookOpenCheck}
      title="المحتوى المعتمد"
      description="مراجعة إدارية مباشرة للمحتوى المنشور: الأسئلة والإجابات الصحيحة والصور والأصوات ومهام التسجيل، بدون محاكاة واجهة الطالب وبدون أي كتابة على تقدم الطلاب."
      actions={<AdminAction icon={RefreshCw} onClick={() => void loadIndex()} disabled={loading}>{loading ? "جاري التحديث..." : "تحديث المحتوى"}</AdminAction>}
    />

    {index?.active_release && <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex flex-wrap items-center justify-between gap-2 text-sm">
      <span className="font-extrabold text-emerald-800 flex items-center gap-2"><CheckCircle2 size={17} />الإصدار النشط والمعتمد</span>
      <span className="text-emerald-800 font-mono text-xs">{index.active_release.version}</span>
    </div>}
    {error && <div className="alert-error" role="alert">{error}</div>}

    <AdminPanel title="البحث والتصفية" description="صفِّ المحتوى حسب المسار أو نوع المهمة أو الوسائط.">
      <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-3">
        <label className="relative">
          <span className="sr-only">بحث</span>
          <Search size={18} className="absolute end-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
          <input className="input-field pe-10" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ابحث بالسؤال أو المهارة أو الرمز..." />
        </label>
        <label className="text-xs text-muted"><span className="flex items-center gap-1 mb-2"><Filter size={14} />المسار</span>
          <select className="input-field" value={section} onChange={(event) => setSection(event.target.value)}>
            <option value="all">كل المحتوى</option>
            <option value="pretest">الاختبار القبلي</option>
            <option value="l1-core">المستوى الأول — الأنشطة</option><option value="l1-rein">المستوى الأول — التقوية</option>
            <option value="l2-core">المستوى الثاني — الأنشطة</option><option value="l2-rein">المستوى الثاني — التقوية</option>
            <option value="l3-core">المستوى الثالث — الأنشطة</option><option value="l3-rein">المستوى الثالث — التقوية</option>
            <option value="posttest">الاختبار البعدي</option>
          </select>
        </label>
        <label className="text-xs text-muted"><span className="block mb-2">نوع المهمة</span>
          <select className="input-field" value={interaction} onChange={(event) => setInteraction(event.target.value)}>
            <option value="all">كل الأنواع</option><option value="choice">اختيارات</option><option value="images">اختيار صور</option>
            <option value="listening">استماع</option><option value="recording">تسجيل صوتي</option><option value="ordering">ترتيب وتسلسل</option>
          </select>
        </label>
        <label className="text-xs text-muted"><span className="block mb-2">الوسائط</span>
          <select className="input-field" value={media} onChange={(event) => setMedia(event.target.value)}>
            <option value="all">الكل</option><option value="audio">يحتوي صوتًا</option><option value="images">يحتوي صورًا</option><option value="recording">يتطلب تسجيلًا</option>
          </select>
        </label>
      </div>
    </AdminPanel>

    <div className="grid xl:grid-cols-[360px_minmax(0,1fr)] gap-5 items-start">
      <AdminPanel title="فهرس المحتوى" description={`${filtered.length} من ${index?.count || 0} عنصرًا معتمدًا`}>
        {loading ? <div className="min-h-52 flex items-center justify-center"><div className="spinner w-9 h-9" /></div>
          : filtered.length === 0 ? <AdminEmptyState title="لا توجد نتائج" description="غيّر البحث أو المرشحات لعرض محتوى آخر." />
          : <div className="max-h-[72vh] overflow-auto pe-1 space-y-5">
            {grouped.map((group) => <section key={group.key}>
              <div className="sticky top-0 z-10 bg-white/95 backdrop-blur py-2 text-xs font-extrabold text-primary">{group.label}</div>
              <div className="space-y-2">{group.items.map((item) => {
                const active = item.canonical_id === effectiveSelected;
                return <button key={item.canonical_id} type="button" onClick={() => { setDetailLoading(true); setError(""); setSelected(item.canonical_id); }} className={`w-full text-start rounded-2xl border p-3 transition ${active ? "border-primary bg-teal/10 shadow-sm" : "border-border bg-white hover:border-primary/40"}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0"><div className="font-extrabold text-navy line-clamp-2">{item.title}</div><div className="text-xs text-muted mt-1">{item.skill || KIND_LABEL[item.kind]}</div></div>
                    <span className="text-[10px] font-mono text-muted shrink-0">{item.canonical_id}</span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    <span className="rounded-full bg-bg px-2 py-1 text-[10px] text-navy">{item.round_count} {item.round_count === 1 ? "جولة" : "جولات"}</span>
                    {item.has_audio && <span className="rounded-full bg-sky-50 px-2 py-1 text-[10px] text-sky-800 inline-flex items-center gap-1"><Volume2 size={11} />صوت</span>}
                    {item.has_images && <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] text-amber-800 inline-flex items-center gap-1"><ImageIcon size={11} />صور</span>}
                    {item.requires_recording && <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] text-violet-800 inline-flex items-center gap-1"><Mic2 size={11} />تسجيل</span>}
                  </div>
                </button>;
              })}</div>
            </section>)}
          </div>}
      </AdminPanel>

      <div className="space-y-5 min-w-0">
        {detailLoading || (effectiveSelected && !current) ? <AdminPanel><div className="min-h-72 flex items-center justify-center"><div className="spinner w-10 h-10" /></div></AdminPanel>
          : !current ? <AdminEmptyState title="اختر عنصر محتوى" description="اختر سؤالًا أو نشاطًا من الفهرس لمراجعة تفاصيله." />
          : <>
            <AdminPanel>
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                <div>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="rounded-full bg-teal/10 text-primary px-3 py-1 text-xs font-bold">{KIND_LABEL[current.item.kind]}</span>
                    {current.item.level_id && <span className="rounded-full bg-bg text-navy px-3 py-1 text-xs font-bold">المستوى {current.item.level_id}</span>}
                    <span className="rounded-full bg-bg text-navy px-3 py-1 text-xs font-bold">{INTERACTION_LABEL[current.item.interaction_type] || current.item.interaction_type}</span>
                    <span className="rounded-full bg-emerald-50 text-emerald-700 px-3 py-1 text-xs font-bold">معتمد</span>
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-navy leading-tight">{current.item.title}</h2>
                  <p className="text-muted mt-2">{current.item.skill}</p>
                </div>
                <div className="text-xs text-muted lg:text-end space-y-1">
                  <div className="font-mono">{current.item.canonical_id}</div>
                  <div>{current.rounds.length} {current.rounds.length === 1 ? "جولة" : "جولات"}</div>
                </div>
              </div>
              {current.item.criterion && <div className="mt-4 rounded-2xl bg-bg border border-border p-4 text-sm text-navy"><span className="font-extrabold">معيار التقييم: </span>{current.item.criterion}</div>}
            </AdminPanel>

            <ContextIntroReview intro={current.item.context_intro} assets={current.item.item_assets} />
            <MediaBlock assets={current.item.item_assets.filter((asset) => {
              const intro = current.item.context_intro;
              return asset.asset_id !== intro?.audio_asset_id && asset.asset_id !== intro?.image_asset_id;
            })} title="وسائط مرتبطة بالنشاط كاملًا" />

            <AdminPanel title="الجولات والأسئلة" description="كل الجولات مع الإجابات والوسائط المعتمدة. افتح أي جولة لمراجعتها.">
              <div className="space-y-3">{current.rounds.map((round) => <RoundReview key={round.id} round={round} interaction={current.item.interaction_type} />)}</div>
            </AdminPanel>
          </>}
      </div>
    </div>
  </AdminPage>;
}
