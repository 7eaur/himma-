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


  it("keeps Arabic direction and exposes the actual choice text to assistive technology", () => {
    render(<InteractionPlayer sessionId={7} interaction={payload({
      options: [
        { id: "a", text: "بَابٌ", media: [] },
        { id: "b", text: "بَيْتٌ", media: [] },
      ],
    })} onLessonChange={jest.fn()}/>);
    expect(screen.getByTestId("v2-interaction-player")).toHaveAttribute("dir", "rtl");
    expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toHaveAccessibleDescription("بَابٌ");
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toHaveAccessibleDescription("بَيْتٌ");
  });

  it("describes ordered word tokens when removing them with keyboard or assistive technology", () => {
    render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction: "build_word",
      options: [{ id: "a", text: "مَ", media: [] }, { id: "b", text: "دْ", media: [] }],
    })} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 2" }));
    const remove = screen.getByRole("button", { name: "إزالة العنصر 1 من الترتيب" });
    expect(remove).toHaveAccessibleDescription("دْ");
    fireEvent.click(remove);
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeEnabled();
  });

  it("builds a word from separate repeated letters and submits tile IDs for automatic grading", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ok:true,json:async()=>({submission:{status:"graded",correct:true,retry_required:false},lesson:{session:{}}})});
    render(<InteractionPlayer sessionId={9} interaction={payload({interaction:"build_word",options:[
      {id:"b1",text:"ب",media:[]},{id:"b2",text:"ب",media:[]},{id:"a",text:"ا",media:[]},
    ]})} onLessonChange={jest.fn()} />);
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button",{name:"اختيار الخيار 1"}));
    fireEvent.click(screen.getByRole("button",{name:"اختيار الخيار 3"}));
    fireEvent.click(screen.getByRole("button",{name:"اختيار الخيار 2"}));
    expect(screen.getByLabelText("الترتيب المختار").querySelectorAll("button")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button",{name:"تحقق من الإجابة"}));
    await waitFor(()=>expect(global.fetch).toHaveBeenCalled());
    const body=JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body);
    expect(body.selected_option_ids).toEqual(["b1","a","b2"]);
    expect(body).not.toHaveProperty("text_response");
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

  it("keeps an empty ordered question fail-closed instead of submitting an empty answer", () => {
    render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction: "sequence", options: [],
    })} onLessonChange={jest.fn()}/>);
    expect(screen.getByRole("alert")).toHaveTextContent("خيارات هذا السؤال غير مكتملة");
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("shows the selected image tokens in the ordered tray and lets the learner correct their order", () => {
    const question = payload({
      interaction: "sequence",
      options: [
        { id: "a", text: null, media: [{ media_id: "IMG-A", kind: "image" }] },
        { id: "b", text: null, media: [{ media_id: "IMG-B", kind: "image" }] },
      ],
    });
    question.media = {
      ...question.media,
      "IMG-A": { asset_id: "IMG-A", kind: "image", state: "ready", url: "/a.png", test_only: true },
      "IMG-B": { asset_id: "IMG-B", kind: "image", state: "ready", url: "/b.png", test_only: true },
    };
    render(<InteractionPlayer sessionId={7} interaction={question} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 2" }));
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    const tray = screen.getByLabelText("الترتيب المختار");
    expect(tray.querySelectorAll("img")).toHaveLength(2);
    // Next/Image may normalize relative fixture URLs to an absolute jsdom origin.
    // Assert the actual image paths and ordering, not the origin serialization.
    expect(new URL(tray.querySelectorAll("img")[0].src).pathname).toBe("/b.png");
    expect(new URL(tray.querySelectorAll("img")[1].src).pathname).toBe("/a.png");
    fireEvent.click(screen.getByRole("button", { name: "إزالة العنصر 1 من الترتيب" }));
    expect(tray.querySelectorAll("img")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
  });

  it("replays the identical answer after a lost acknowledgment and locks editing until confirmation", async () => {
    const fetchMock = global.fetch as jest.Mock;
    fetchMock
      .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ detail: "تعذر الاتصال مؤقتًا" }) })
      .mockResolvedValueOnce({
        ok: true, status: 200,
        json: async () => ({
          status: "replayed",
          submission: { retry_required: false, status: "graded" },
          lesson: { session: { stage: "independent_check" } },
        }),
      });
    const onLessonChange = jest.fn();
    render(<InteractionPlayer sessionId={7} interaction={payload()} onLessonChange={onLessonChange}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "إعادة محاولة حفظ الإجابة" })).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "إعادة محاولة حفظ الإجابة" }));
    await waitFor(() => expect(onLessonChange).toHaveBeenCalledTimes(1));
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual(JSON.parse(fetchMock.mock.calls[0][1].body));
  });

  it("unlocks correction after a definite validation rejection and uses a fresh answer key", async () => {
    const fetchMock = global.fetch as jest.Mock;
    fetchMock
      .mockResolvedValueOnce({ ok: false, status: 422, json: async () => ({ detail: "إجابة غير صالحة" }) })
      .mockResolvedValueOnce({
        ok: true, status: 200,
        json: async () => ({ submission: { retry_required: false, status: "graded" }, lesson: { session: {} } }),
      });
    render(<InteractionPlayer sessionId={7} interaction={payload()} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
    await waitFor(() => expect(screen.getByText("إجابة غير صالحة")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 2" }));
    fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const first = JSON.parse(fetchMock.mock.calls[0][1].body);
    const second = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(first.submit_key).not.toBe(second.submit_key);
    expect(first.selected_option_ids).toEqual(["a"]);
    expect(second.selected_option_ids).toEqual(["b"]);
  });


  it("blocks submission when a referenced stimulus audio is missing", () => {
    render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction: "listen_choose_one",
      stimulus: { text: null, media: [{ media_id: "AUD-NOT-READY", kind: "audio" }] },
    })} onLessonChange={jest.fn()}/>);
    expect(screen.getByRole("alert")).toHaveTextContent("لن تُرسل الإجابة");
    expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("blocks incomplete image-choice questions rather than grading a guess", () => {
    const question = payload({
      interaction: "choose_image",
      options: [
        { id: "a", text: null, media: [{ media_id: "IMG-READY", kind: "image" }] },
        { id: "b", text: null, media: [{ media_id: "IMG-MISSING", kind: "image" }] },
      ],
    });
    question.media = {
      ...question.media,
      "IMG-READY": { asset_id: "IMG-READY", kind: "image", state: "ready", url: "/test-image.png", test_only: true },
    };
    render(<InteractionPlayer sessionId={7} interaction={question} onLessonChange={jest.fn()}/>);
    expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("blocks submission until images load and again if an image later fails", async () => {
    const question = payload({
      interaction: "choose_image",
      options: [
        { id: "a", text: null, media: [{ media_id: "IMG-ONE", kind: "image" }] },
        { id: "b", text: null, media: [{ media_id: "IMG-TWO", kind: "image" }] },
      ],
    });
    question.media = {
      ...question.media,
      "IMG-ONE": { asset_id: "IMG-ONE", kind: "image", state: "ready", url: "/broken-image.png", test_only: true },
      "IMG-TWO": { asset_id: "IMG-TWO", kind: "image", state: "ready", url: "/working-image.png", test_only: true },
    };
    render(<InteractionPlayer sessionId={7} interaction={question} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    await act(async () => { screen.getAllByAltText("صورة خيار").forEach((img) => fireEvent.load(img)); });
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeEnabled();
    fireEvent.error(screen.getAllByAltText("صورة خيار")[0]);
    expect(screen.getByRole("alert")).toHaveTextContent("لن تُرسل الإجابة");
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeDisabled();
    expect(global.fetch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "إعادة تحميل الصور" }));
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    await act(async () => { screen.getAllByAltText("صورة خيار").forEach((img) => fireEvent.load(img)); });
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toHaveAttribute("aria-pressed", "true");
  });

  it("ignores a replaced audio element's late rejection and error events", async () => {
    let rejectFirst: (reason: Error) => void = () => { throw new Error("uninitialized"); };
    const firstPlay = new Promise<void>((_resolve, reject) => { rejectFirst = reject; });
    const instances: Array<{ play: jest.Mock; pause: jest.Mock; onerror: null | (() => void); onended: null | (() => void); onplaying: null | (() => void); onwaiting: null | (() => void) }> = [];
    global.Audio = jest.fn().mockImplementation(() => {
      const index = instances.length;
      const instance = {
        play: jest.fn().mockImplementation(() => index === 0 ? firstPlay : Promise.resolve()),
        pause: jest.fn(),
        onerror: null, onended: null, onplaying: null, onwaiting: null,
      };
      instances.push(instance);
      return instance;
    }) as unknown as typeof Audio;
    const question = payload({
      interaction: "listen_choose_one",
      options: [
        { id: "a", text: "أ", media: [{ media_id: "LET-01", kind: "audio" }] },
        { id: "b", text: "ب", media: [{ media_id: "LET-02", kind: "audio" }] },
      ],
    });
    question.media = {
      ...question.media,
      "LET-02": { asset_id: "LET-02", kind: "audio", state: "ready", url: "/second.mp3", test_only: true },
    };
    render(<InteractionPlayer sessionId={7} interaction={question} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getAllByRole("button", { name: "تشغيل صوت هذا الخيار" })[0]);
    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "تشغيل صوت هذا الخيار" })[0]);
    });
    expect(instances).toHaveLength(2);
    expect(instances[0].pause).toHaveBeenCalledTimes(1);
    await act(async () => {
      rejectFirst(new Error("first stream aborted after replacement"));
      await firstPlay.catch(() => undefined);
      instances[0].onerror?.();
      instances[0].onended?.();
      instances[0].onplaying?.();
      instances[0].onwaiting?.();
    });
    expect(screen.queryByText("تعذر تشغيل الصوت. حاول الضغط على زر الصوت مرة أخرى.")).not.toBeInTheDocument();
    expect(screen.queryByText("تعذر تشغيل الصوت. حاول مرة أخرى.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "إيقاف الصوت" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "اختيار الخيار 2" })).toBeEnabled();
  });

  it("ignores late playback events after the student pauses the same audio", async () => {
    let resolvePlay: () => void = () => { throw new Error("uninitialized"); };
    const deferred = new Promise<void>((resolve) => { resolvePlay = resolve; });
    const instance = { play: jest.fn().mockReturnValue(deferred), pause: jest.fn(), onerror: null as null | (() => void), onended: null as null | (() => void), onplaying: null as null | (() => void), onwaiting: null as null | (() => void) };
    global.Audio = jest.fn().mockImplementation(() => instance) as unknown as typeof Audio;
    render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction: "listen_choose_one",
      stimulus: { text: null, media: [{ media_id: "LET-01", kind: "audio" }] },
    })} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "تشغيل صوت السؤال" }));
    fireEvent.click(screen.getByRole("button", { name: "إيقاف الصوت" }));
    await act(async () => {
      resolvePlay();
      await deferred;
      instance.onplaying?.();
      instance.onerror?.();
    });
    expect(screen.getByRole("button", { name: "تشغيل صوت السؤال" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "إيقاف الصوت" })).not.toBeInTheDocument();
    expect(screen.queryByText("تعذر تشغيل الصوت. حاول مرة أخرى.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toBeEnabled();
  });

  it("fails closed on an audio playback error and permits retry after playback succeeds", async () => {
    const play = jest.fn().mockRejectedValueOnce(new Error("media decode failed")).mockResolvedValueOnce(undefined);
    global.Audio = jest.fn().mockImplementation(() => ({ play, pause: jest.fn(), onended: null, onerror: null })) as unknown as typeof Audio;
    render(<InteractionPlayer sessionId={7} interaction={payload({
      interaction: "listen_choose_one",
      stimulus: { text: null, media: [{ media_id: "LET-01", kind: "audio" }] },
    })} onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeEnabled();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "تشغيل صوت السؤال" })); });
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    expect(screen.getByText(/هذا السؤال يحتاج صورة أو صوتًا غير جاهز الآن/)).toHaveTextContent("لن تُرسل الإجابة");
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "تشغيل صوت السؤال" })); });
    expect(play).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeEnabled();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("does not allow answering a question with an unsupported video stimulus", () => {
    const question = payload({
      stimulus: { text: null, media: [{ media_id: "VID-QUESTION", kind: "video" }] },
    });
    question.media = {
      ...question.media,
      "VID-QUESTION": { asset_id: "VID-QUESTION", kind: "video", state: "ready", url: "/test-video.mp4", test_only: true },
    };
    render(<InteractionPlayer sessionId={7} interaction={question} onLessonChange={jest.fn()}/>);
    expect(screen.getByRole("button", { name: "تحقق من الإجابة" })).toBeDisabled();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("does not reveal correctness or hints in pretest even if an API response includes them", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true, status: 200,
      json: async () => ({
        submission: { retry_required: true, status: "graded", correct: false, hint: "لا تكشف هذه المعلومة", message: "حاول مرة أخرى" },
        assessment: { session: { state: "answering" } },
      }),
    });
    const pretest = payload({ role: "pretest" });
    pretest.progress = { index: 1, total: 30, stage: "pretest" };
    render(<InteractionPlayer sessionId={17} interaction={pretest} endpointBase="/api/v2/assessments" onLessonChange={jest.fn()}/>);
    fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
    fireEvent.click(screen.getByRole("button", { name: "حفظ الإجابة والمتابعة" }));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    expect(screen.queryByText(/تلميح:/)).not.toBeInTheDocument();
    expect(screen.queryByText("حاول مرة أخرى")).not.toBeInTheDocument();
    expect(screen.getByTestId("v2-question-coach")).toHaveTextContent("خذ وقتك، واستمع أو اقرأ السؤال");
    expect(screen.getByTestId("v2-question-coach")).not.toHaveTextContent("لا تكشف هذه المعلومة");
  });

  it("shows the coach's hint only after an incorrect guided attempt", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({ok:true,status:200,json:async()=>({
      submission:{retry_required:true,status:"graded",correct:false,hint:"استمع إلى أول صوت في الكلمة.",message:"اقتربت! اقرأ التلميح ثم حاول مرة أخرى."},
    })});
    render(<InteractionPlayer sessionId={7} interaction={payload()} onLessonChange={jest.fn()}/>);
    const coach=screen.getByTestId("v2-question-coach");
    expect(coach).not.toHaveTextContent("استمع إلى أول صوت");
    fireEvent.click(screen.getByRole("button",{name:"اختيار الخيار 1"}));
    fireEvent.click(screen.getByRole("button",{name:"تحقق من الإجابة"}));
    await waitFor(()=>expect(coach).toHaveTextContent("تلميح: استمع إلى أول صوت في الكلمة."));
    expect(coach.querySelector('img')).toHaveAttribute('src',expect.stringContaining('try-again'));
    expect(screen.getByRole("status")).toBe(coach);
    expect(coach).toHaveTextContent("حاول مرة أخرى");
    expect(screen.queryByText("اقتربت! اقرأ التلميح ثم حاول مرة أخرى.")).not.toBeInTheDocument();
  });

  it("shows a supportive instruction without hints for a support check", () => {
    const check=payload({role:"support_check"});
    check.progress={index:1,total:2,stage:"support_check"};
    render(<InteractionPlayer sessionId={7} interaction={check} onLessonChange={jest.fn()}/>);
    expect(screen.getByTestId("v2-question-coach")).toHaveTextContent("ثم أجب بنفسك");
    expect(screen.getByTestId("v2-question-coach")).not.toHaveTextContent("فكر بهدوء");
  });


  it("stops a microphone stream granted after the learner leaves the question", async () => {
    const previousDevices = navigator.mediaDevices;
    const previousRecorder = global.MediaRecorder;
    const stop = jest.fn();
    let grant: (stream: MediaStream) => void = () => { throw new Error("permission not requested"); };
    const permission = new Promise<MediaStream>((resolve) => { grant = resolve; });
    const getUserMedia = jest.fn().mockReturnValue(permission);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
    const recorder = Object.assign(jest.fn(), { isTypeSupported: jest.fn().mockReturnValue(false) });
    global.MediaRecorder = recorder as unknown as typeof MediaRecorder;
    try {
      const { unmount } = render(<InteractionPlayer sessionId={7} interaction={payload({
        interaction: "read_aloud", options: [],
      })} onLessonChange={jest.fn()}/>);
      fireEvent.click(screen.getByRole("button", { name: "بدء التسجيل" }));
      expect(screen.getByRole("button", { name: "جاري تفعيل الميكروفون" })).toBeDisabled();
      expect(getUserMedia).toHaveBeenCalledTimes(1);
      unmount();
      await act(async () => {
        grant({ getTracks: () => [{ stop }] } as unknown as MediaStream);
        await permission;
      });
      expect(stop).toHaveBeenCalledTimes(1);
      expect(recorder).not.toHaveBeenCalled();
    } finally {
      Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: previousDevices });
      global.MediaRecorder = previousRecorder;
    }
  });

  it("pauses the recorded preview during explanation review without discarding or uploading it", async () => {
    const previousDevices = navigator.mediaDevices; const previousRecorder = global.MediaRecorder;
    const createURL = URL.createObjectURL; const revokeURL = URL.revokeObjectURL;
    const stream = {getTracks:()=>[{stop:jest.fn()}]} as unknown as MediaStream;
    Object.defineProperty(navigator,"mediaDevices",{configurable:true,value:{getUserMedia:jest.fn().mockResolvedValue(stream)}});
    URL.createObjectURL = jest.fn().mockReturnValue("blob:private-recording");
    URL.revokeObjectURL = jest.fn();
    const recorder = {state:"inactive",stream,mimeType:"audio/webm",onstop:null as null|(()=>void),ondataavailable:null as null|((event:BlobEvent)=>void),start:jest.fn(),stop:jest.fn()};
    recorder.start.mockImplementation(()=>{recorder.state="recording";});
    recorder.stop.mockImplementation(()=>{recorder.state="inactive";recorder.ondataavailable?.({data:new Blob(["recording"])} as BlobEvent);recorder.onstop?.();});
    global.MediaRecorder = Object.assign(jest.fn().mockImplementation(()=>recorder),{isTypeSupported:jest.fn().mockReturnValue(false)}) as unknown as typeof MediaRecorder;
    const interaction = payload({interaction:"read_aloud",options:[]});
    const changed = jest.fn();
    try {
      const view = render(<InteractionPlayer sessionId={7} interaction={interaction} onLessonChange={changed}/>);
      await act(async()=>{fireEvent.click(screen.getByRole("button",{name:"بدء التسجيل"}));});
      fireEvent.click(screen.getByRole("button",{name:"إيقاف التسجيل"}));
      const preview = view.container.querySelector("audio")!;
      expect(preview).toHaveAttribute("src","blob:private-recording");
      const pause = jest.spyOn(preview,"pause").mockImplementation(()=>{});
      await act(async()=>{view.rerender(<InteractionPlayer sessionId={7} interaction={interaction} suspended onLessonChange={changed}/>);});
      expect(pause).toHaveBeenCalledTimes(1);
      await act(async()=>{view.rerender(<InteractionPlayer sessionId={7} interaction={interaction} onLessonChange={changed}/>);});
      expect(view.container.querySelector("audio")).toBe(preview);
      expect(screen.getByRole("button",{name:"إرسال التسجيل للمراجعة"})).toBeEnabled();
      expect(global.fetch).not.toHaveBeenCalled();
      view.unmount();
    } finally {
      Object.defineProperty(navigator,"mediaDevices",{configurable:true,value:previousDevices});
      global.MediaRecorder=previousRecorder; URL.createObjectURL=createURL; URL.revokeObjectURL=revokeURL;
    }
  });

  it("rejects an empty reading capture and releases the microphone without uploading", async () => {
    const previousDevices = navigator.mediaDevices;
    const previousRecorder = global.MediaRecorder;
    const stopTrack = jest.fn();
    const stream = { getTracks: () => [{ stop: stopTrack }] } as unknown as MediaStream;
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true, value: { getUserMedia: jest.fn().mockResolvedValue(stream) },
    });
    const recorder = {
      state: "inactive",
      stream,
      mimeType: "audio/webm",
      onstop: null as (() => void) | null,
      ondataavailable: null as ((event: BlobEvent) => void) | null,
      start: jest.fn(),
      stop: jest.fn(),
    };
    recorder.start.mockImplementation(() => { recorder.state = "recording"; });
    recorder.stop.mockImplementation(() => { recorder.state = "inactive"; recorder.onstop?.(); });
    const constructor = Object.assign(jest.fn().mockImplementation(() => recorder), {
      isTypeSupported: jest.fn().mockReturnValue(false),
    });
    global.MediaRecorder = constructor as unknown as typeof MediaRecorder;
    try {
      render(<InteractionPlayer sessionId={7} interaction={payload({
        interaction: "read_aloud", options: [],
      })} onLessonChange={jest.fn()}/>);
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "بدء التسجيل" }));
        await Promise.resolve();
      });
      expect(screen.getByRole("button", { name: "إيقاف التسجيل" })).toBeEnabled();
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "إيقاف التسجيل" }));
      });
      expect(stopTrack).toHaveBeenCalled();
      expect(screen.getByRole("alert")).toHaveTextContent("لم يُلتقط صوت");
      expect(screen.getByRole("button", { name: "إرسال التسجيل للمراجعة" })).toBeDisabled();
      expect(global.fetch).not.toHaveBeenCalled();
    } finally {
      Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: previousDevices });
      global.MediaRecorder = previousRecorder;
    }
  });

  it("stops the microphone and rejects partial audio when the recorder fails asynchronously", async () => {
    const previousDevices = navigator.mediaDevices;
    const previousRecorder = global.MediaRecorder;
    const stopTrack = jest.fn();
    const stream = { getTracks: () => [{ stop: stopTrack }] } as unknown as MediaStream;
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true, value: { getUserMedia: jest.fn().mockResolvedValue(stream) },
    });
    const recorder = {
      state: "inactive",
      stream,
      mimeType: "audio/webm",
      onstop: null as null | (() => void),
      ondataavailable: null as null | ((event: BlobEvent) => void),
      onerror: null as null | ((event: Event) => void),
      start: jest.fn(),
      stop: jest.fn(),
    };
    recorder.start.mockImplementation(() => { recorder.state = "recording"; });
    recorder.stop.mockImplementation(() => { recorder.state = "inactive"; recorder.onstop?.(); });
    global.MediaRecorder = Object.assign(jest.fn().mockImplementation(() => recorder), {
      isTypeSupported: jest.fn().mockReturnValue(false),
    }) as unknown as typeof MediaRecorder;
    try {
      render(<InteractionPlayer sessionId={7} interaction={payload({
        interaction: "read_aloud", options: [],
      })} onLessonChange={jest.fn()}/>);
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "بدء التسجيل" }));
        await Promise.resolve();
      });
      expect(screen.getByRole("button", { name: "إيقاف التسجيل" })).toBeEnabled();
      await act(async () => { recorder.onerror?.(new Event("error")); });
      expect(stopTrack).toHaveBeenCalled();
      expect(recorder.stop).toHaveBeenCalledTimes(1);
      expect(screen.getByRole("alert")).toHaveTextContent("تعذر تسجيل الصوت");
      expect(screen.getByRole("button", { name: "بدء التسجيل" })).toBeEnabled();
      expect(screen.getByRole("button", { name: "إرسال التسجيل للمراجعة" })).toBeDisabled();
      expect(global.fetch).not.toHaveBeenCalled();
    } finally {
      Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: previousDevices });
      global.MediaRecorder = previousRecorder;
    }
  });

  it("discards partial recording if MediaRecorder.stop throws and ignores a late stop event", async () => {
    const previousDevices = navigator.mediaDevices;
    const previousRecorder = global.MediaRecorder;
    const stopTrack = jest.fn();
    const stream = { getTracks: () => [{ stop: stopTrack }] } as unknown as MediaStream;
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true, value: { getUserMedia: jest.fn().mockResolvedValue(stream) },
    });
    const recorder = {
      state: "inactive",
      stream,
      mimeType: "audio/webm",
      onstop: null as null | (() => void),
      ondataavailable: null as null | ((event: BlobEvent) => void),
      onerror: null as null | ((event: Event) => void),
      start: jest.fn(),
      stop: jest.fn(() => { throw new Error("device disconnected"); }),
    };
    recorder.start.mockImplementation(() => { recorder.state = "recording"; });
    global.MediaRecorder = Object.assign(jest.fn().mockImplementation(() => recorder), {
      isTypeSupported: jest.fn().mockReturnValue(false),
    }) as unknown as typeof MediaRecorder;
    try {
      render(<InteractionPlayer sessionId={7} interaction={payload({
        interaction: "read_aloud", options: [],
      })} onLessonChange={jest.fn()}/>);
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "بدء التسجيل" }));
        await Promise.resolve();
      });
      const lateStop = recorder.onstop;
      await act(async () => {
        recorder.ondataavailable?.({ data: new Blob(["partial"]) } as BlobEvent);
        fireEvent.click(screen.getByRole("button", { name: "إيقاف التسجيل" }));
      });
      expect(stopTrack).toHaveBeenCalled();
      expect(recorder.onstop).toBeNull();
      expect(recorder.ondataavailable).toBeNull();
      await act(async () => { lateStop?.(); });
      expect(screen.getByRole("alert")).toHaveTextContent("تعذر إنهاء التسجيل");
      expect(screen.getByRole("button", { name: "إرسال التسجيل للمراجعة" })).toBeDisabled();
      expect(screen.getByRole("button", { name: "بدء التسجيل" })).toBeEnabled();
      expect(global.fetch).not.toHaveBeenCalled();
    } finally {
      Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: previousDevices });
      global.MediaRecorder = previousRecorder;
    }
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

it("shows a worked support model on repeat failure and waits for acknowledgement before the next question", async () => {
  const nextLesson = { session: { stage: "support_check" } };
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: true, status: 200,
    json: async () => ({
      submission: {
        status: "graded", retry_required: false, correct: false, assisted_advance: true,
        help_level: 3, model_option_ids: ["b"],
        message: "راجع المثال المحلول، ثم نتابع خطوة جديدة.",
      },
      lesson: nextLesson,
    }),
  });
  const support = payload();
  support.progress.stage = "support_practice";
  const onLessonChange = jest.fn();
  render(<InteractionPlayer sessionId={7} interaction={support} onLessonChange={onLessonChange}/>);
  fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
  fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "فهمت، نكمل" })).toBeInTheDocument());
  expect(screen.getByLabelText("مثال محلول للتعلّم")).toHaveTextContent("ب");
  expect(screen.getByTestId("v2-question-coach")).toHaveTextContent("راجع المثال المحلول");
  expect(onLessonChange).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: "تحقق من الإجابة" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "اختيار الخيار 1" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "فهمت، نكمل" }));
  expect(onLessonChange).toHaveBeenCalledWith(nextLesson);
  expect(global.fetch).toHaveBeenCalledTimes(1);
});

it("does not reveal worked support examples in unaided checks even if feedback includes a model", async () => {
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true, status: 200,
    json: async () => ({
      submission: {
        status: "graded", retry_required: false, correct: false,
        help_level: 2, model_option_ids: ["b"],
      },
      lesson: { session: { stage: "outcome" } },
    }),
  });
  const check = payload({ role: "support_check" });
  check.progress.stage = "support_check";
  render(<InteractionPlayer sessionId={7} interaction={check} onLessonChange={jest.fn()}/>);
  fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
  fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
  await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
  expect(screen.queryByLabelText("مثال محلول للتعلّم")).not.toBeInTheDocument();
});

  it("shows one coach message on practice retry, with no duplicate feedback below the answers", async () => {
  (global.fetch as jest.Mock).mockResolvedValue({ok:true,status:200,json:async()=>({
    submission:{retry_required:true,status:"graded",correct:false,hint:"أنصت إلى أول حرف.",message:"حاول مرة أخرى"}
  })});
  render(<InteractionPlayer sessionId={7} interaction={payload()} onLessonChange={jest.fn()}/>);
  fireEvent.click(screen.getByRole("button", { name:"اختيار الخيار 1" }));
  fireEvent.click(screen.getByRole("button", { name:"تحقق من الإجابة" }));
  const coach = screen.getByTestId("v2-question-coach");
  await waitFor(() => expect(coach).toHaveTextContent("أنصت إلى أول حرف."));
  expect(coach).toHaveAttribute("role", "status");
  expect(screen.getAllByText(/حاول مرة أخرى/)).toHaveLength(1);
  expect(screen.queryByText("تم الحفظ")).not.toBeInTheDocument();
});
