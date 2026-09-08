import { act, fireEvent, render, screen } from "@testing-library/react";
import StudentActivityPage from "./page";

const push = jest.fn();
const playbackToggle = jest.fn();
const playbackStop = jest.fn();
let queueEnded: (() => void) | undefined;

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "42" }),
  useRouter: () => ({ push }),
}));

jest.mock("@/hooks/useAudioQueue", () => ({
  useAudioQueue: (_onError?: (message: string) => void, onEnded?: () => void) => {
    queueEnded = onEnded;
    return {
      state: "idle",
      isPlaying: false,
      isPaused: false,
      toggle: playbackToggle,
      stop: playbackStop,
    };
  },
}));

function response(body: unknown) {
  return { ok: true, json: async () => body };
}

beforeEach(() => {
  jest.clearAllMocks();
  queueEnded = undefined;
  window.sessionStorage.clear();
});

describe("Student activity page", () => {
  it("keeps reinforcement context without exposing internal task-design labels", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({ id: 99, stable_key: "reinforcement-test" }))
      .mockResolvedValueOnce(response({
        version: "HIMMA-STUDENT-EXPERIENCE-2.0",
        session_id: 42,
        level_id: 2,
        item_id: 99,
        stable_key: "reinforcement-test",
        kind: "reinforcement_activity",
        interaction_type: "choose_one",
        round: {
          round_number: 1,
          round_total: 5,
          skill: "الشدة",
          encouragement: "أنت تتقدم بشكل رائع.",
          hint: "ركّز على الحرف المشدد.",
          question_text: "أي كلمة تحتوي على شدة؟",
          instruction_text: "اختر الكلمة التي تحتوي على شدة",
          stimulus_text: "",
        },
        retry: false,
        attempts_used: 0,
        max_attempts: 2,
        step: {
          id: 7,
          order_index: 1,
          expected_reading_text: null,
          required_selection_count: 1,
          options: [
            { id: 1, text: "مُعَلِّم", order_index: 1 },
            { id: 2, text: "كتاب", order_index: 2 },
          ],
          assets: [],
          media_gaps: [],
        },
        assets: [],
      }))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "in_progress",
        level_id: 2,
        completed_items: 5,
        total_items: 10,
        elapsed_seconds: 30,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByTestId("student-task-instruction")).toHaveTextContent("اختر الكلمة التي تحتوي على شدة");
    expect(screen.getByTestId("reinforcement-intro")).toHaveTextContent("بعد إتقانها تعود إلى نشاطك الأساسي");
    expect(screen.queryByText("مهمة واحدة في كل مرة", { exact: true })).not.toBeInTheDocument();
    expect(screen.queryByTestId("reinforcement-badge")).not.toBeInTheDocument();
    expect(screen.getByTestId("activity-session")).toHaveAttribute("data-activity-kind", "reinforcement");
  });

  it("requires the approved audio story to finish before opening its questions", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({ id: 90, stable_key: "l1-core-09" }))
      .mockResolvedValueOnce(response({
        version: "HIMMA-STUDENT-EXPERIENCE-2.0",
        session_id: 42,
        level_id: 1,
        item_id: 90,
        stable_key: "l1-core-09",
        kind: "core_activity",
        interaction_type: "choose_one",
        round: {
          round_number: 1,
          round_total: 5,
          skill: "الفهم السمعي المباشر",
          encouragement: "استمع بتركيز.",
          hint: "تذكّر أحداث القصة.",
          question_text: "إلى أين ذهبت ليان؟",
          instruction_text: "اختر الإجابة الصحيحة اعتمادًا على ما فهمته من القصة.",
          stimulus_text: "",
        },
        retry: false,
        attempts_used: 0,
        context_intro: {
          kind: "audio_story",
          title: "استمع إلى قصة ليان",
          instruction: "استمع إلى القصة كاملة، ثم ابدأ الأسئلة.",
          audio_asset_id: "INS-01",
          asset: {
            asset_id: "INS-01",
            asset_type: "audio",
            usage: "context",
            semantic_text: "قصة ليان",
            url: "/api/media/INS-01",
          },
        },
        step: {
          id: 70,
          order_index: 1,
          expected_reading_text: null,
          required_selection_count: 1,
          options: [
            { id: 11, text: "إلى المزرعة", order_index: 1 },
            { id: 12, text: "إلى المدرسة", order_index: 2 },
            { id: 13, text: "إلى السوق", order_index: 3 },
            { id: 14, text: "إلى الحديقة", order_index: 4 },
          ],
          assets: [],
          media_gaps: [],
        },
        assets: [],
      }))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "in_progress",
        level_id: 1,
        completed_items: 8,
        total_items: 10,
      }));

    render(<StudentActivityPage />);

    const gate = await screen.findByRole("button", { name: "استمع إلى القصة أولًا" });
    expect(gate).toBeDisabled();
    expect(screen.getByTestId("activity-session")).toHaveAttribute("data-phase", "context-intro");

    fireEvent.click(screen.getByTestId("context-audio-control"));
    expect(playbackToggle).toHaveBeenCalledWith(["/api/media/INS-01"]);
    expect(gate).toBeDisabled();

    act(() => queueEnded?.());

    const start = screen.getByRole("button", { name: "ابدأ الأسئلة" });
    expect(start).toBeEnabled();
    fireEvent.click(start);
    expect(window.sessionStorage.getItem("himma:context-intro:42:90")).toBe("seen");
    expect(screen.getByRole("heading", { name: "إلى أين ذهبت ليان؟" })).toBeInTheDocument();
  });

  it("points an L2 completion to L3 instead of advertising the posttest too early", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(null))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "completed",
        level_id: 2,
        completed_items: 10,
        total_items: 10,
        elapsed_seconds: 180,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByRole("heading", { name: "أحسنت، أكملت بناء الكلمة" })).toBeInTheDocument();
    expect(screen.getByText(/خطوتك التالية هي الطلاقة والفهم/)).toBeInTheDocument();
    expect(screen.queryByText((content, element) => element?.tagName === "P" && content.includes("البعدي"))).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "الانتقال إلى خطوتي التالية" })).toBeEnabled();
  });

  it("mentions the posttest only after completing L3", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(null))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "completed",
        level_id: 3,
        completed_items: 10,
        total_items: 10,
        elapsed_seconds: 220,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByRole("heading", { name: "أحسنت، أكملت المستوى الثالث" })).toBeInTheDocument();
    expect(screen.getByText((content, element) => element?.tagName === "P" && content.includes("البعدي"))).toBeInTheDocument();
  });
});
