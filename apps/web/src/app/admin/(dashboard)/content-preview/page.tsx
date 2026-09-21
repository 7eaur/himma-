"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import {
  ArrowLeft,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  ChevronDown,
  FileAudio,
  Filter,
  ImageIcon,
  ListChecks,
  Menu,
  Mic2,
  RefreshCw,
  Search,
  Volume2,
  X,
} from "lucide-react";
import { AdminAction, AdminPage, AdminPageHeader } from "@/components/admin/AdminUI";
import styles from "./content-preview.module.css";

type Kind = "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
type Interaction = string;
type Scope = "all" | "pretest" | "l1" | "l2" | "l3" | "posttest";
type ContentKind = "all" | "core" | "rein";

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
  reinforcement_candidates: string[];
  search_text: string;
  release_version?: string | null;
  release_sha256?: string | null;
}

interface ReviewIndex {
  mode: "read_only";
  purpose: "admin_content_review";
  writes_progress: false;
  count: number;
  items: ReviewSummary[];
  active_release?: {
    version: string;
    is_active: boolean;
    released_at?: string | null;
  } | null;
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
  stimulus: {
    kind?: string;
    text?: string | null;
    audio_target?: string | null;
    audio_targets?: string[] | null;
  };
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
    reinforcement_candidates: string[];
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

const SCOPE_OPTIONS: Array<{ value: Scope; label: string }> = [
  { value: "all", label: "الكل" },
  { value: "pretest", label: "القبلي" },
  { value: "l1", label: "المستوى 1" },
  { value: "l2", label: "المستوى 2" },
  { value: "l3", label: "المستوى 3" },
  { value: "posttest", label: "البعدي" },
];

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
  if (item.interaction_type === "choose_image") return "images";
  if (["sequence", "memory_sequence", "path_sequence", "build_word"].includes(item.interaction_type)) return "ordering";
  return "choice";
}

function scopeMatches(item: ReviewSummary, scope: Scope) {
  if (scope === "all") return true;
  if (scope === "pretest") return item.kind === "pretest_question";
  if (scope === "posttest") return item.kind === "posttest_question";
  if (scope === "l1") return item.level_id === 1 && (item.kind === "core_activity" || item.kind === "reinforcement_activity");
  if (scope === "l2") return item.level_id === 2 && (item.kind === "core_activity" || item.kind === "reinforcement_activity");
  return item.level_id === 3 && (item.kind === "core_activity" || item.kind === "reinforcement_activity");
}

function kindMatches(item: ReviewSummary, kind: ContentKind) {
  if (kind === "all") return true;
  if (kind === "core") return item.kind === "core_activity";
  return item.kind === "reinforcement_activity";
}

function scopeForItem(item: ReviewSummary): Scope {
  if (item.kind === "pretest_question") return "pretest";
  if (item.kind === "posttest_question") return "posttest";
  if (item.level_id === 1) return "l1";
  if (item.level_id === 2) return "l2";
  return "l3";
}

function contentKindForItem(item: ReviewSummary): ContentKind {
  if (item.kind === "core_activity") return "core";
  if (item.kind === "reinforcement_activity") return "rein";
  return "all";
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

function MediaBlock({
  assets,
  title = "الوسائط",
  hideMappedImages = false,
}: {
  assets: Asset[];
  title?: string;
  hideMappedImages?: boolean;
}) {
  const visible = assets.filter((asset) => !(hideMappedImages && asset.asset_type === "image" && asset.option_id));
  if (!visible.length) return null;

  const audio = visible.filter((asset) => asset.asset_type === "audio");
  const images = visible.filter((asset) => asset.asset_type === "image");

  return <section className={styles.mediaBlock}>
    <div className={styles.subsectionTitle}><FileAudio size={16} aria-hidden="true" />{title}</div>

    {audio.length > 0 && <div className={styles.audioList}>
      {audio.map((asset) => <div key={`a-${asset.asset_id}-${asset.usage || ""}`} className={styles.audioCard}>
        <div className={styles.audioMeta}>
          <span className={styles.audioName}>{asset.semantic_text || asset.asset_id}</span>
          <span>{asset.usage || "audio"}</span>
        </div>
        <audio src={asset.url} controls preload="metadata" className={styles.audioPlayer} />
      </div>)}
    </div>}

    {images.length > 0 && <div className={styles.imageGrid}>
      {images.map((asset) => <figure key={`i-${asset.asset_id}-${asset.usage || ""}`} className={styles.imageCard}>
        <div className={styles.imageCardVisual}>
          <Image
            src={asset.url}
            alt={asset.semantic_text || "صورة معتمدة"}
            width={220}
            height={150}
            className={styles.image}
            unoptimized
          />
        </div>
        <figcaption className={styles.imageCaption}>{asset.semantic_text || asset.asset_id}</figcaption>
      </figure>)}
    </div>}
  </section>;
}

function AnswerReview({ round }: { round: ReviewRound }) {
  const { answer, options, assets } = round;
  const imageByOption = new Map<number, Asset>();

  assets.forEach((asset) => {
    if (asset.asset_type === "image" && asset.option_id) {
      imageByOption.set(Number(asset.option_id), asset);
    }
  });

  if (answer.kind === "ordered_sequence" && answer.values.length > 0) {
    return <section>
      <div className={styles.subsectionTitle}><ListChecks size={16} aria-hidden="true" />{answer.label || "الترتيب الصحيح"}</div>
      <ol className={styles.orderedList} data-testid="ordered-answer-review">
        {answer.values.map((value, index) => {
          const matched = options.find((option) => option.text === value);
          const image = matched ? imageByOption.get(matched.id) : undefined;
          return <li key={`${index}-${value}`} className={styles.orderedStep}>
            <span className={styles.stepNumber}>{index + 1}</span>
            <div className={styles.orderedContent}>
              {image && <Image
                src={image.url}
                alt={image.semantic_text || value || "عنصر مرتب"}
                width={60}
                height={60}
                className={styles.orderedImage}
                unoptimized
              />}
              <span className={styles.orderedText}>{value}</span>
            </div>
          </li>;
        })}
      </ol>
    </section>;
  }

  if (options.length > 0) {
    const answerIds = new Set(answer.kind === "correct_options" ? answer.option_ids : []);

    return <section>
      <div className={styles.subsectionTitle}><ListChecks size={16} aria-hidden="true" />الخيارات</div>
      <div className={styles.optionsGrid} data-testid="preview-image-options">
        {options.map((option, index) => {
          const image = imageByOption.get(option.id);
          const isCorrect = option.is_correct || answerIds.has(option.id);

          return <div key={option.id} className={`${styles.optionCard} ${isCorrect ? styles.optionCorrect : ""}`.trim()}>
            {image && <div className={styles.optionImageWrap}>
              <Image
                src={image.url}
                alt={image.semantic_text || option.text || "خيار مصور"}
                width={180}
                height={120}
                className={styles.optionImage}
                unoptimized
              />
            </div>}
            <div className={styles.optionLine}>
              <span className={styles.optionNumber}>{index + 1}</span>
              <div>
                <div className={styles.optionText}>{option.text || image?.semantic_text || "خيار مصور"}</div>
                {isCorrect && <span className={styles.correctMark}><CheckCircle2 size={13} aria-hidden="true" />الإجابة الصحيحة</span>}
              </div>
            </div>
          </div>;
        })}
      </div>
    </section>;
  }

  if (answer.kind === "recording_target" && answer.values.length > 0) {
    return <section className={styles.recordingTarget}>
      <div className={styles.recordingLabel}><Mic2 size={16} aria-hidden="true" />{answer.label || "النص المطلوب تسجيله"}</div>
      {answer.values.map((value, index) => <div key={`${index}-${value}`} className={styles.recordingValue}>{value}</div>)}
    </section>;
  }

  if (answer.kind === "correct_options" && answer.values.length > 0) {
    return <section className={styles.recordingTarget}>
      <div className={styles.recordingLabel}><CheckCircle2 size={16} aria-hidden="true" />{answer.label || "الإجابة الصحيحة"}</div>
      {answer.values.map((value, index) => <div key={`${index}-${value}`} className={styles.recordingValue}>{value}</div>)}
    </section>;
  }

  return null;
}

function ContextIntroReview({ intro, assets }: { intro?: ContextIntro | null; assets: Asset[] }) {
  if (!intro) return null;

  const attached = assets.filter((asset) =>
    (intro.audio_asset_id && asset.asset_id === intro.audio_asset_id)
    || (intro.image_asset_id && asset.asset_id === intro.image_asset_id)
  );

  return <section className={styles.detailCard}>
    <div className={styles.sectionHeader}>
      <h3 className={styles.sectionTitle}>{intro.title || "مقدمة النشاط"}</h3>
      <p className={styles.sectionDescription}>
        {intro.kind === "audio_story" ? "مقدمة الاستماع المرتبطة بهذا المحتوى." : "السياق الذي يسبق الأسئلة."}
      </p>
    </div>
    {intro.text && <div className={styles.contextText} data-testid="preview-context-reading-text">{intro.text}</div>}
    {intro.instruction && <p className={styles.contextInstruction}><strong>التعليمة:</strong> {intro.instruction}</p>}
    <MediaBlock assets={attached} title="وسائط المقدمة" />
  </section>;
}

function RoundReview({
  round,
  interaction,
  forceOpen = false,
}: {
  round: ReviewRound;
  interaction: Interaction;
  forceOpen?: boolean;
}) {
  const stimulusText = String(round.stimulus_text || round.stimulus?.text || "").trim();
  const normalizedQuestion = round.question_text.trim();
  const showStimulus = Boolean(stimulusText && stimulusText !== normalizedQuestion);
  const hasStudentCopy = Boolean(round.encouragement || round.instruction_text || round.hint);

  return <details className={styles.roundDetails} open={forceOpen || round.round_number === 1} data-testid="content-round">
    <summary className={styles.roundSummary}>
      <div className={styles.roundSummaryMain}>
        <div className={styles.roundNumber}>الجولة {round.round_number} من {round.round_total}</div>
        <div className={styles.roundQuestion} data-preview-question>{round.question_text || "جولة محتوى"}</div>
      </div>
      <ChevronDown className={styles.chevron} size={19} aria-hidden="true" />
    </summary>

    <div className={styles.roundBody}>
      {showStimulus && <div className={styles.stimulus} data-preview-stimulus>{stimulusText}</div>}

      {hasStudentCopy && <div className={styles.studentCopy} aria-label="نصوص العرض للطالب">
        {round.encouragement && <div className={styles.copyRow}>
          <span className={styles.copyLabel}>العبارة التشجيعية</span>
          <span>{round.encouragement}</span>
        </div>}
        {round.instruction_text && <div className={styles.copyRow}>
          <span className={styles.copyLabel}>التعليمة</span>
          <span>{round.instruction_text}</span>
        </div>}
        {round.hint && <div className={styles.copyRow}>
          <span className={styles.copyLabel}>التلميح عند الخطأ</span>
          <span>{round.hint}</span>
        </div>}
      </div>}

      <MediaBlock assets={round.assets} hideMappedImages title="الوسائط المرتبطة" />
      <AnswerReview round={round} />

      {round.media_gaps.length > 0 && <div className={styles.mediaGap}>توجد فجوات وسائط مسجلة في هذه الجولة وتحتاج مراجعة.</div>}

      <details className={styles.technical}>
        <summary>تفاصيل تقنية</summary>
        <div className={styles.technicalBody}>
          نوع التفاعل: {INTERACTION_LABEL[interaction] || interaction} · ترتيب الجولة في المحتوى: {round.order_index}
        </div>
      </details>
    </div>
  </details>;
}

export default function ContentPreviewPage() {
  const [index, setIndex] = useState<ReviewIndex | null>(null);
  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [selected, setSelected] = useState("");
  const [scope, setScope] = useState<Scope>("all");
  const [contentKind, setContentKind] = useState<ContentKind>("all");
  const [interaction, setInteraction] = useState("all");
  const [media, setMedia] = useState("all");
  const [query, setQuery] = useState("");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [mobileNavigatorOpen, setMobileNavigatorOpen] = useState(false);
  const [activeMobileRound, setActiveMobileRound] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadIndex = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchIndex();
      setIndex(data);
      if (!selected && data.items.length) {
        const saved = typeof window !== "undefined" ? window.localStorage.getItem("himma.admin.contentPreview.lastItem") : null;
        const initial = data.items.find((item) => item.canonical_id === saved)?.canonical_id || data.items[0].canonical_id;
        setSelected(initial);
      }
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
        if (data.items.length) {
          const saved = window.localStorage.getItem("himma.admin.contentPreview.lastItem");
          const initial = data.items.find((item) => item.canonical_id === saved)?.canonical_id || data.items[0].canonical_id;
          setSelected(initial);
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل المحتوى المعتمد");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ar");

    return (index?.items || []).filter((item) => {
      if (!scopeMatches(item, scope)) return false;
      if (!kindMatches(item, contentKind)) return false;
      if (interaction !== "all" && interactionGroup(item) !== interaction) return false;
      if (media === "audio" && !item.has_audio) return false;
      if (media === "images" && !item.has_images) return false;
      if (media === "recording" && !item.requires_recording) return false;

      if (normalized) {
        const haystack = item.search_text.toLocaleLowerCase("ar");
        if (!haystack.includes(normalized)) return false;
      }

      return true;
    });
  }, [index, scope, contentKind, interaction, media, query]);

  const effectiveSelected = filtered.some((item) => item.canonical_id === selected)
    ? selected
    : (filtered[0]?.canonical_id || "");

  useEffect(() => {
    if (!effectiveSelected) return;

    let cancelled = false;

    void fetchDetail(effectiveSelected)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل تفاصيل المحتوى");
      });

    return () => {
      cancelled = true;
    };
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
  const selectedSummary = (index?.items || []).find((item) => item.canonical_id === effectiveSelected) || null;
  const currentSectionKey = selectedSummary ? sectionKey(selectedSummary) : "";
  const currentSectionItems = selectedSummary
    ? filtered.filter((item) => sectionKey(item) === currentSectionKey)
    : [];
  const currentItemIndex = currentSectionItems.findIndex((item) => item.canonical_id === effectiveSelected);
  const currentItemPosition = currentItemIndex >= 0 ? currentItemIndex + 1 : 0;
  const currentSectionLabel = currentSectionKey ? sectionLabel(currentSectionKey) : "المحتوى";
  const advancedFilterCount = Number(contentKind !== "all") + Number(interaction !== "all") + Number(media !== "all");

  useEffect(() => {
    if (!mobileNavigatorOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileNavigatorOpen]);

  const resetAdvancedFilters = () => {
    setContentKind("all");
    setInteraction("all");
    setMedia("all");
    setSelected("");
  };

  const selectScope = (nextScope: Scope) => {
    setScope(nextScope);
    if (nextScope === "pretest" || nextScope === "posttest") setContentKind("all");
    setSelected("");
  };

  const selectItem = (canonicalId: string) => {
    setError("");
    setSelected(canonicalId);
    setActiveMobileRound(0);
    setMobileNavigatorOpen(false);

    if (typeof window !== "undefined") {
      window.localStorage.setItem("himma.admin.contentPreview.lastItem", canonicalId);
      if (window.matchMedia("(max-width: 820px)").matches) {
        setQuery("");
        window.requestAnimationFrame(() => {
          document.querySelector('[data-testid="content-detail-pane"]')?.scrollIntoView({ block: "start" });
        });
      }
    }
  };

  const openMobileNavigator = () => {
    if (selectedSummary) {
      setScope(scopeForItem(selectedSummary));
      setContentKind(contentKindForItem(selectedSummary));
    }
    setInteraction("all");
    setMedia("all");
    setQuery("");
    setShowAdvancedFilters(false);
    setMobileNavigatorOpen(true);
  };

  const moveItem = (direction: -1 | 1) => {
    if (currentItemIndex < 0) return;
    const next = currentSectionItems[currentItemIndex + direction];
    if (next) selectItem(next.canonical_id);
  };

  const selectLinkedItem = (canonicalId: string) => {
    setScope("all");
    setContentKind("all");
    setInteraction("all");
    setMedia("all");
    setQuery("");
    selectItem(canonicalId);
  };

  return <AdminPage className={styles.shell}>
    <AdminPageHeader
      eyebrow="إدارة المحتوى"
      icon={BookOpenCheck}
      title="المحتوى المعتمد"
      description="مراجعة المحتوى المنشور للقراءة فقط."
      actions={<AdminAction icon={RefreshCw} onClick={() => void loadIndex()} disabled={loading}>{loading ? "جاري التحديث..." : "تحديث"}</AdminAction>}
    />

    <div className={styles.headerMeta} aria-label="حالة المحتوى">
      <span className={styles.headerPill}>{index?.count ?? 0} عنصر</span>
      <span className={styles.headerPill}>قراءة فقط</span>
      {index?.active_release && <span
        className={`${styles.headerPill} ${styles.headerPillStrong}`}
        title={index.active_release.version}
      >
        <CheckCircle2 size={14} aria-hidden="true" />
        الإصدار النشط
      </span>}
    </div>

    {error && <div className="alert-error" role="alert">{error}</div>}

    <section className={styles.toolbar} data-testid="content-filter-toolbar" aria-label="البحث وتصفية المحتوى">
      <div className={styles.searchRow}>
        <label className={styles.searchWrap}>
          <span className="sr-only">بحث في المحتوى المعتمد</span>
          <Search size={18} className={styles.searchIcon} aria-hidden="true" />
          <input
            type="search"
            className={styles.searchInput}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setSelected("");
            }}
            placeholder="ابحث بالسؤال أو المهارة أو الرمز..."
          />
        </label>

        <button
          type="button"
          className={styles.filterToggle}
          aria-expanded={showAdvancedFilters}
          onClick={() => setShowAdvancedFilters((value) => !value)}
        >
          <Filter size={16} aria-hidden="true" />
          تصفية
          {advancedFilterCount > 0 && <span className={styles.filterCount}>{advancedFilterCount}</span>}
        </button>
      </div>

      <div className={styles.scopeRow} aria-label="مسار المحتوى">
        {SCOPE_OPTIONS.map((option) => <button
          key={option.value}
          type="button"
          aria-pressed={scope === option.value}
          className={`${styles.scopeButton} ${scope === option.value ? styles.scopeButtonActive : ""}`.trim()}
          onClick={() => selectScope(option.value)}
        >
          {option.label}
        </button>)}
      </div>

      {showAdvancedFilters && <div className={styles.advancedFilters}>
        <label className={styles.field}>
          نوع المحتوى
          <select
            className={styles.select}
            value={contentKind}
            disabled={scope === "pretest" || scope === "posttest"}
            onChange={(event) => {
              setContentKind(event.target.value as ContentKind);
              setSelected("");
            }}
          >
            <option value="all">الأنشطة والتقوية</option>
            <option value="core">الأنشطة الأساسية فقط</option>
            <option value="rein">التقوية فقط</option>
          </select>
        </label>

        <label className={styles.field}>
          نوع المهمة
          <select
            className={styles.select}
            value={interaction}
            onChange={(event) => {
              setInteraction(event.target.value);
              setSelected("");
            }}
          >
            <option value="all">كل الأنواع</option>
            <option value="choice">اختيارات</option>
            <option value="images">اختيار صور</option>
            <option value="listening">استماع</option>
            <option value="recording">تسجيل صوتي</option>
            <option value="ordering">ترتيب وتسلسل</option>
          </select>
        </label>

        <label className={styles.field}>
          الوسائط
          <select
            className={styles.select}
            value={media}
            onChange={(event) => {
              setMedia(event.target.value);
              setSelected("");
            }}
          >
            <option value="all">كل المحتوى</option>
            <option value="audio">يحتوي صوتًا</option>
            <option value="images">يحتوي صورًا</option>
            <option value="recording">يتطلب تسجيلًا</option>
          </select>
        </label>

        {advancedFilterCount > 0 && <div className={styles.filterFooter}>
          <button type="button" className={styles.clearFilters} onClick={resetAdvancedFilters}>
            <X size={15} aria-hidden="true" />
            مسح التصفية
          </button>
        </div>}
      </div>}
    </section>

    <div className={styles.workspace}>
      {mobileNavigatorOpen && <button
        type="button"
        className={styles.mobileIndexBackdrop}
        aria-label="إغلاق فهرس المحتوى"
        onClick={() => setMobileNavigatorOpen(false)}
      />}

      <aside
        className={`${styles.indexPane} ${mobileNavigatorOpen ? styles.mobileIndexOpen : styles.mobileIndexClosed}`.trim()}
        data-testid="content-index-pane"
        aria-label="فهرس المحتوى"
      >
        <div className={styles.mobileSheetHeader}>
          <div>
            <strong>اختر المحتوى</strong>
            <span>{currentSectionLabel}</span>
          </div>
          <button type="button" aria-label="إغلاق فهرس المحتوى" onClick={() => setMobileNavigatorOpen(false)}>
            <X size={19} aria-hidden="true" />
          </button>
        </div>

        <div className={styles.mobileNavigatorControls}>
          <div className={styles.scopeRow} aria-label="القسم">
            {SCOPE_OPTIONS.filter((option) => option.value !== "all").map((option) => <button
              key={option.value}
              type="button"
              aria-pressed={scope === option.value}
              className={`${styles.scopeButton} ${scope === option.value ? styles.scopeButtonActive : ""}`.trim()}
              onClick={() => {
                setScope(option.value);
                setContentKind(option.value === "pretest" || option.value === "posttest" ? "all" : "core");
                setSelected("");
              }}
            >
              {option.label}
            </button>)}
          </div>

          {scope !== "pretest" && scope !== "posttest" && scope !== "all" && <div className={styles.kindRow} aria-label="نوع المحتوى">
            <button
              type="button"
              aria-pressed={contentKind === "core"}
              className={contentKind === "core" ? styles.kindButtonActive : ""}
              onClick={() => {
                setContentKind("core");
                setSelected("");
              }}
            >
              الأنشطة
            </button>
            <button
              type="button"
              aria-pressed={contentKind === "rein"}
              className={contentKind === "rein" ? styles.kindButtonActive : ""}
              onClick={() => {
                setContentKind("rein");
                setSelected("");
              }}
            >
              التقوية
            </button>
          </div>}

          <label className={styles.searchWrap}>
            <span className="sr-only">بحث داخل القسم</span>
            <Search size={17} className={styles.searchIcon} aria-hidden="true" />
            <input
              type="search"
              className={styles.searchInput}
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setSelected("");
              }}
              placeholder="ابحث داخل هذا القسم..."
            />
          </label>
        </div>

        <div className={styles.indexHeader}>
          <div>
            <div className={styles.indexTitle}>فهرس المحتوى</div>
            <div className={styles.indexCount}>{filtered.length} من {index?.count || 0}</div>
          </div>
        </div>

        {loading ? <div className={styles.loading}><div className="spinner w-9 h-9" /></div>
          : filtered.length === 0 ? <div className={styles.empty}><div><strong>لا توجد نتائج</strong>غيّر البحث أو التصفية.</div></div>
          : <div className={styles.indexList}>
            {grouped.map((group) => <section className={styles.group} key={group.key}>
              <div className={styles.groupLabel}>{group.label}</div>
              <div className={styles.indexItems}>
                {group.items.map((item, itemIndex) => {
                  const active = item.canonical_id === effectiveSelected;

                  return <button
                    key={item.canonical_id}
                    type="button"
                    data-testid="content-index-item"
                    onClick={() => selectItem(item.canonical_id)}
                    className={`${styles.indexItem} ${active ? styles.indexItemActive : ""}`.trim()}
                    aria-current={active ? "true" : undefined}
                  >
                    <div className={styles.indexItemTop}>
                      <span className={styles.indexNumber}>{String(itemIndex + 1).padStart(2, "0")}</span>
                      <span className={styles.indexTitleText}>{item.title}</span>
                      <span className={styles.indexId}>{item.canonical_id}</span>
                    </div>
                    <div className={styles.indexMeta}>
                      <span className={styles.indexSkill}>{item.skill || KIND_LABEL[item.kind]}</span>
                      <span className={styles.indexFlags} aria-label="خصائص المحتوى">
                        {item.has_audio && <span className={styles.indexFlag} title="يحتوي صوتًا"><Volume2 size={12} aria-hidden="true" /></span>}
                        {item.has_images && <span className={styles.indexFlag} title="يحتوي صورًا"><ImageIcon size={12} aria-hidden="true" /></span>}
                        {item.requires_recording && <span className={styles.indexFlag} title="يتطلب تسجيلًا"><Mic2 size={12} aria-hidden="true" /></span>}
                      </span>
                    </div>
                  </button>;
                })}
              </div>
            </section>)}
          </div>}
      </aside>

      <main className={styles.detailPane} data-testid="content-detail-pane">
        <div className={styles.mobileNavigatorBar} data-testid="content-mobile-navigator">
          <div className={styles.mobileNavigatorContext}>
            <strong>{currentSectionLabel}</strong>
            <span>{currentItemPosition || "—"} من {currentSectionItems.length || 0}</span>
          </div>
          <button
            type="button"
            data-testid="content-open-navigator"
            aria-label="فتح فهرس المحتوى"
            onClick={openMobileNavigator}
          >
            <Menu size={18} aria-hidden="true" />
            الفهرس
          </button>
        </div>

        {effectiveSelected && !current ? <section className={styles.detailCard}><div className={styles.loading}><div className="spinner w-10 h-10" /></div></section>
          : !current ? <section className={styles.detailCard}><div className={styles.empty}><div><strong>اختر عنصر محتوى</strong>اختر سؤالًا أو نشاطًا من الفهرس لمراجعته.</div></div></section>
          : <>
            <section className={styles.detailCard}>
              <div className={styles.detailHeader}>
                <div className={styles.detailHeading}>
                  <div className={styles.kickers}>
                    <span className={`${styles.kicker} ${styles.kickerPrimary}`}>{KIND_LABEL[current.item.kind]}</span>
                    {current.item.level_id && <span className={styles.kicker}>المستوى {current.item.level_id}</span>}
                    <span className={styles.kicker}>{INTERACTION_LABEL[current.item.interaction_type] || current.item.interaction_type}</span>
                  </div>
                  <h2 className={styles.detailTitle}>{current.item.title}</h2>
                  {current.item.skill && <p className={styles.detailSkill}>{current.item.skill}</p>}
                </div>

                <div className={styles.detailSideMeta}>
                  <span className={styles.detailId}>{current.item.canonical_id}</span>
                  <span>{current.rounds.length} {current.rounds.length === 1 ? "جولة" : "جولات"}</span>
                </div>
              </div>

              {current.item.criterion && <details className={styles.inlineDisclosure}>
                <summary>معيار التقييم</summary>
                <div className={styles.inlineDisclosureBody}>{current.item.criterion}</div>
              </details>}

              {current.item.kind === "core_activity" && current.item.reinforcement_candidates.length > 0 && <div className={styles.reinforcementRow}>
                <span className={styles.reinforcementLabel}>تقوية مرتبطة:</span>
                {current.item.reinforcement_candidates.map((canonical) => {
                  const linked = index?.items.find((item) => item.canonical_id === canonical);
                  return <button
                    key={canonical}
                    type="button"
                    className={styles.reinforcementLink}
                    onClick={() => selectLinkedItem(canonical)}
                  >
                    {linked?.title || canonical}
                  </button>;
                })}
              </div>}
            </section>

            <ContextIntroReview intro={current.item.context_intro} assets={current.item.item_assets} />

            <MediaBlock
              assets={current.item.item_assets.filter((asset) => {
                const intro = current.item.context_intro;
                return asset.asset_id !== intro?.audio_asset_id && asset.asset_id !== intro?.image_asset_id;
              })}
              title="وسائط النشاط"
            />

            <section className={styles.detailCard}>
              <div className={styles.sectionHeader}>
                <h3 className={styles.sectionTitle}>الجولات والأسئلة</h3>
                <p className={styles.sectionDescription}>افتح الجولة التي تريد مراجعتها. كل معلومة تظهر مرة واحدة.</p>
              </div>
              <div className={styles.desktopRounds}>
                <div className={styles.rounds}>
                  {current.rounds.map((round) => <RoundReview key={round.id} round={round} interaction={current.item.interaction_type} />)}
                </div>
              </div>

              <div className={styles.mobileRoundViewer}>
                {current.rounds.length > 0 && (() => {
                  const roundIndex = Math.min(activeMobileRound, current.rounds.length - 1);
                  const round = current.rounds[roundIndex];
                  return <>
                    <RoundReview round={round} interaction={current.item.interaction_type} forceOpen />
                    {current.rounds.length > 1 && <div className={styles.mobileRoundNav}>
                      <button
                        type="button"
                        disabled={roundIndex === 0}
                        onClick={() => setActiveMobileRound((value) => Math.max(0, value - 1))}
                      >
                        <ArrowRight size={16} aria-hidden="true" />
                        السابقة
                      </button>
                      <span>الجولة {roundIndex + 1} من {current.rounds.length}</span>
                      <button
                        type="button"
                        disabled={roundIndex === current.rounds.length - 1}
                        onClick={() => setActiveMobileRound((value) => Math.min(current.rounds.length - 1, value + 1))}
                      >
                        التالية
                        <ArrowLeft size={16} aria-hidden="true" />
                      </button>
                    </div>}
                  </>;
                })()}
              </div>
            </section>

            <nav className={styles.mobileItemNav} aria-label="التنقل بين عناصر القسم">
              <button
                type="button"
                disabled={currentItemIndex <= 0}
                onClick={() => moveItem(-1)}
                aria-label="العنصر السابق"
              >
                <ArrowRight size={17} aria-hidden="true" />
                السابق
              </button>
              <button type="button" className={styles.mobileItemProgress} onClick={openMobileNavigator}>
                <strong>{currentItemPosition || "—"} من {currentSectionItems.length || 0}</strong>
                <span>{currentSectionLabel}</span>
              </button>
              <button
                type="button"
                disabled={currentItemIndex < 0 || currentItemIndex >= currentSectionItems.length - 1}
                onClick={() => moveItem(1)}
                aria-label="العنصر التالي"
              >
                التالي
                <ArrowLeft size={17} aria-hidden="true" />
              </button>
            </nav>
          </>}
      </main>
    </div>
  </AdminPage>;
}
