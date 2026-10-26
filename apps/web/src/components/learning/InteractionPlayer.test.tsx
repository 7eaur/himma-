import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import InteractionPlayer, { type InteractionPayload } from "./InteractionPlayer";

const media = {
  "LET-01": { asset_id: "LET-01", kind: "audio" as const, state: "ready", url: "/fixture.mp3", test_only: true },
};

function payload(overrides: Partial<InteractionPayload["question"]> = {}): InteractionPayload {
  return {
    question: {
      question_id: "Q-1",
      role: "guided_practice",
      interaction: "choose_one",
      prompt: "اختر الإجابة.",
      stimulus: { text: "ق", media: [] },
      options: [
        { id: "a", text: "أ", media: [] },
        { id: "b", text: "ب", media: [] },
      ],
      hint: "فكر بهدوء.",
      ...overrides,
    },
    media,
    progress: { index: 1, total: 4, stage: "guided_practice" },
    attempts: 0,
    draft: null,
  };
}

describe("InteractionPlayer", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
    global.Audio = jest.fn().mockImplementation(() => ({
      play: jest.fn().mockResolvedValue(undefined),
      pause: jest.fn(),
      onended: null,
      onerror: null,
    })) as unknown as typeof Audio;
  });

  it.each([
    ["choose_one", [{ id: "a", text: "أ", media: [] }]],
    ["listen_choose_one", [{ id: "a", text: "أ", media: [{ media_id: "LET-01", kind: "audio" }] }]],
    ["choose_image", [{ id: "a", text: "صورة", media: [] }]],
    ["sequence", [{ id: "a", text: "سَ", media: [] }, { id: "b", text: "مَ", media: [] }]],
    ["build_word", [{ id: "a", text: "ب", media: [] }, { id: "b", text: "اب", media: [] }]],
    ["read_aloud", []],
    ["write_text", []],
  ] as const)("renders the shared %s interaction contract", (interaction, options) => {
    const { container } = render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction,
      options: options.map((option) => ({ ...option, media: [...option.media] })),
    })} onLessonChange={jest.fn()}/>);
    expect(container.querySelector(`[data-interaction="${interaction}"]`)).toBeInTheDocument();
  });

  it("keeps an option audio control independent from choosing the option", async () => {
    render(<InteractionPlayer sessionId={7} interaction={payload({
      options: [{ id: "a", text: null, media: [{ media_id: "LET-01", kind: "audio" }] }],
    })} onLessonChange={jest.fn()}/>);
    const option = screen.getByRole("button", { name: "اختيار الخيار 1" });
    const audio = screen.getByRole("button", { name: "تشغيل صوت هذا الخيار" });
    expect(option).toHaveAttribute("aria-pressed", "false");
    await act(async () => { fireEvent.click(audio); });
    expect(option).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(option);
    expect(option).toHaveAttribute("aria-pressed", "true");
  });

  it("builds an ordered response without duplicating tokens", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ submission: { retry_required: false, status: "graded" }, lesson: { session: {} } }),
    });
    render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction: "sequence",
      options: [{ id: "a", text: "سَ", media: [] }, { id: "b", text: "مَ", media: [] }],
    })} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 2" }));
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const request = (global.fetch as jest.Mock).mock.calls[0][1];
    expect(JSON.parse(request.body).selected_option_ids).toEqual(["b", "a"]);
  });

  it("autosaves writing as a draft before it becomes review evidence", async () => {
    jest.useFakeTimers();
    (global.fetch as jest.Mock).mockResolvedValue({ ok: true, json: async () => ({ status: "saved" }) });
    render(<InteractionPlayer sessionId={9} interaction={payload({
      interaction: "write_text", options: [], stimulus: { text: null, media: [] },
    })} onLessonChange={jest.fn()}/>);
    fireEvent.change(screen.getByLabelText("اكتب إجابتك هنا"), { target: { value: "باب" } });
    expect(screen.getByText("جاري حفظ المسودة...")).toBeInTheDocument();
    await act(async () => { jest.advanceTimersByTime(700); });
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      "/api/v2/lessons/sessions/9/draft",
      expect.objectContaining({ method: "PUT", body: JSON.stringify({ text: "باب" }) }),
    ));
    expect(screen.getByText("حُفظت المسودة")).toBeInTheDocument();
    jest.useRealTimers();
  });

  it.each([
    ["support_practice", "مساعدة مركزة"],
    ["additional_check", "تحقق قصير"],
    ["support_check", "تحقق بعد المساعدة"],
  ])("labels the %s detour as help rather than a level failure", (stage, label) => {
    const support = payload();
    support.progress.stage = stage;
    render(<InteractionPlayer sessionId={11} interaction={support} onLessonChange={jest.fn()}/>);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("uses the assessment endpoint and labels pretest without exposing feedback", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ submission: { retry_required: false, status: "graded", message: "تم حفظ إجابتك." }, assessment: { session: { state: "answering" } } }),
    });
    const pretest = payload({ role: "pretest" });
    pretest.progress = { index: 1, total: 30, stage: "pretest" };
    render(<InteractionPlayer sessionId={17} interaction={pretest} endpointBase="/api/v2/assessments" onLessonChange={jest.fn()}/>);
    expect(screen.getByText("الاختبار القبلي")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "تحقق من الإجابة" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    fireEvent.click(screen.getByRole("button", { name: "حفظ الإجابة والمتابعة" }));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      "/api/v2/assessments/sessions/17/answers",
      expect.objectContaining({ method: "POST" }),
    ));
  });
});
