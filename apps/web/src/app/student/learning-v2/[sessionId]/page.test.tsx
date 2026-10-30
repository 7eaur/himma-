import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import V2LessonPage from "./page";

let mockSessionId = "44";
const mockRouter = { replace: jest.fn() };

jest.mock("next/navigation", () => ({
  useParams: () => ({ sessionId: mockSessionId }),
  useRouter: () => mockRouter,
}));

function lesson(sessionId: number, title: string) {
  return {
    lesson_id: sessionId === 44 ? "L1-01" : "L1-02",
    title, level: "L1",
    intro: { title, text: "تمهيد تجريبي", button: "التالي" },
    video: { asset_id: "SHARED-VIDEO", url: "/shared.mp4", test_only: true, state: "ready" },
    practice: { count: 1, first_question_id: "TEST-Q" },
    independent_check: { count: 1 },
    session: { session_id: sessionId, stage: "teaching_video", status: "in_progress", video_position_seconds: 0, video_duration_seconds: 6, version: 1 },
  };
}

function ok(data: unknown): Response {
  return { ok: true, status: 200, json: async () => data } as Response;
}

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  mockRouter.replace.mockClear();
});

beforeEach(() => {
  mockSessionId = "44";
});

it("does not expose an old lesson while a new session loads, even with the same video URL", async () => {
  const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
    const session = Number(String(input).match(/sessions\/(\d+)\/interaction/)?.[1]);
    return ok(lesson(session, session === 44 ? "الدرس الأول" : "الدرس الثاني"));
  });
  global.fetch = fetchMock as typeof fetch;

  const { rerender } = render(<V2LessonPage />);
  await screen.findByRole("heading", { name: "الدرس الأول", level: 1 });
  const previousVideo = screen.getByTestId("v2-video-player").querySelector("video");
  expect(previousVideo).toBeTruthy();

  mockSessionId = "45";
  rerender(<V2LessonPage />);
  expect(screen.queryByRole("heading", { name: "الدرس الأول", level: 1 })).not.toBeInTheDocument();
  await screen.findByRole("heading", { name: "الدرس الثاني", level: 1 });
  const nextVideo = screen.getByTestId("v2-video-player").querySelector("video");
  expect(nextVideo).not.toBe(previousVideo);
  expect(nextVideo).toHaveAttribute("src", "/shared.mp4");
});

it("ignores a late GET from the previous session instead of replacing the current lesson", async () => {
  const responses = new Map<number, (response: Response) => void>();
  global.fetch = jest.fn((input: RequestInfo | URL) => new Promise<Response>((resolve) => {
    const session = Number(String(input).match(/sessions\/(\d+)\/interaction/)?.[1]);
    responses.set(session, resolve);
  })) as typeof fetch;

  const { rerender } = render(<V2LessonPage />);
  await waitFor(() => expect(responses.has(44)).toBe(true));
  mockSessionId = "45";
  rerender(<V2LessonPage />);
  await waitFor(() => expect(responses.has(45)).toBe(true));

  await act(async () => { responses.get(45)?.(ok(lesson(45, "الدرس الثاني"))); });
  expect(screen.getByRole("heading", { name: "الدرس الثاني", level: 1 })).toBeInTheDocument();
  await act(async () => { responses.get(44)?.(ok(lesson(44, "الدرس الأول"))); });
  expect(screen.getByRole("heading", { name: "الدرس الثاني", level: 1 })).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "الدرس الأول", level: 1 })).not.toBeInTheDocument();
});

it("fails closed when a lesson GET returns a different session identifier", async () => {
  global.fetch = jest.fn(async () => ok(lesson(45, "جلسة غير مطابقة"))) as typeof fetch;
  render(<V2LessonPage />);
  await screen.findByRole("alert");
  expect(screen.getByRole("alert")).toHaveTextContent("استجابة جلسة الدرس غير متطابقة");
  expect(screen.queryByTestId("v2-video-player")).not.toBeInTheDocument();
});

it("does not redirect the current lesson when a previous route returns a late 401", async () => {
  const responses = new Map<number, (response: Response) => void>();
  global.fetch = jest.fn((input: RequestInfo | URL) => new Promise<Response>((resolve) => {
    const session = Number(String(input).match(/sessions\/(\d+)\/interaction/)?.[1]);
    responses.set(session, resolve);
  })) as typeof fetch;

  const { rerender } = render(<V2LessonPage />);
  await waitFor(() => expect(responses.has(44)).toBe(true));
  mockSessionId = "45";
  rerender(<V2LessonPage />);
  await waitFor(() => expect(responses.has(45)).toBe(true));

  await act(async () => { responses.get(45)?.(ok(lesson(45, "الدرس الثاني"))); });
  await act(async () => {
    responses.get(44)?.({ status: 401, ok: false, json: async () => ({ detail: "Expired old session" }) } as Response);
  });
  expect(screen.getByRole("heading", { name: "الدرس الثاني", level: 1 })).toBeInTheDocument();
  expect(mockRouter.replace).not.toHaveBeenCalled();
});

it("shows the lesson introduction in the learner journey before the video", async () => {
  global.fetch = jest.fn(async () => ok({
    ...lesson(44, "الحرف وصوته"),
    session: {...lesson(44, "الحرف وصوته").session, stage: "intro"},
  })) as typeof fetch;
  render(<V2LessonPage/>);
  expect(await screen.findByText("تمهيد تجريبي")).toBeVisible();
  expect(screen.getByTestId("v2-lesson-intro")).toHaveAttribute("aria-label", "تمهيد الدرس");
  expect(screen.getByAltText("شخصية هِمّة ترحب بالطالب")).toBeInTheDocument();
  expect(screen.getByRole("button", {name:/التالي/})).toBeVisible();
  expect(screen.queryByTestId("v2-video-player")).not.toBeInTheDocument();
});

it.each(["additional_check", "support_practice", "support_check"] as const)("shows %s as its own no-video support step", async (stage) => {
  const base=lesson(44, "الحرف وصوته");
  global.fetch = jest.fn(async () => ok({
    ...base,
    session: {...base.session, stage},
    adaptation: {message:"لديك مساعدة قصيرة",support:{title:"تمييز الصوت",focus:"sound_mapping",mode:"targeted_support"}},
    interaction: {question:{question_id:"SUP-Q-1",role:stage === "support_practice" ? "guided_practice" : "support_check",interaction:"choose_one",prompt:"اختر الصوت",stimulus:{text:"مَ",media:[]},options:[{id:"a",text:"مَ",media:[]},{id:"b",text:"بَ",media:[]}]},media:{},progress:{index:1,total:2,stage},attempts:0,draft:null},
  })) as typeof fetch;
  render(<V2LessonPage/>);
  expect(await screen.findByTestId("v2-support-path")).toHaveTextContent("تمييز الصوت");
  expect(screen.getByTestId("v2-interaction-player")).toBeVisible();
  expect(screen.queryByTestId("v2-video-player")).not.toBeInTheDocument();
  expect(screen.getByLabelText("مراحل الدرس").querySelector('[aria-current="step"]')).toHaveTextContent(stage === "additional_check" ? "تحقق قصير" : stage === "support_practice" ? "تدريب التقوية" : "تحقق بعد التقوية");
});


it("keeps replay reachable after video completion and preserves the practice draft while reviewing", async () => {
  const base = lesson(44, "الحرف وصوته");
  const practice = {...base, session:{...base.session,stage:"guided_practice"}, interaction:{
    question:{question_id:"DRAFT-Q",role:"guided_practice",interaction:"choose_one",prompt:"اختر الحرف",stimulus:{text:"ب",media:[]},options:[{id:"a",text:"ب",media:[]},{id:"b",text:"ت",media:[]}]},
    media:{},progress:{index:2,total:3,stage:"guided_practice"},attempts:0,
  }};
  let completed = false;
  const fetchMock = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === "POST") { completed = true; return ok(practice); }
    return ok(completed ? practice : base);
  });
  global.fetch = fetchMock as typeof fetch;
  render(<V2LessonPage/>);
  const player = await screen.findByTestId("v2-video-player");
  expect(screen.getByTestId("v2-video-guidance")).toHaveTextContent("شاهد شرح الدرس");
  expect(screen.getByAltText("شخصية هِمّة تشرح التعليمات")).toBeInTheDocument();
  const video = player.querySelector("video")!;
  Object.defineProperty(video,"duration",{configurable:true,value:6});
  Object.defineProperty(video,"currentTime",{configurable:true,value:6});
  await act(async () => { fireEvent.ended(video); });
  expect(screen.getByRole("button",{name:/شاهد مرة أخرى/})).toBeVisible();
  expect(screen.getByTestId("v2-interaction-player")).not.toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"انتقل إلى التدريب"}));
  expect(screen.getByTestId("v2-interaction-player")).toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"اختيار الخيار 1"}));
  fireEvent.click(screen.getByRole("button",{name:"مراجعة المقدمة"}));
  expect(screen.getByTestId("v2-interaction-player")).not.toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"العودة إلى موضعي المحفوظ"}));
  expect(screen.getByRole("button",{name:"اختيار الخيار 1"})).toHaveAttribute("aria-pressed","true");
  expect(fetchMock.mock.calls.filter(([,init])=>init?.method === "POST")).toHaveLength(1);
});

it("shows the approved objective in the intro exactly once", async () => {
  const base = lesson(44, "الحرف وصوته");
  global.fetch = jest.fn(async () => ok({...base, objective:"أميز صوت الحرف في بداية الكلمة",session:{...base.session,stage:"intro"}})) as typeof fetch;
  render(<V2LessonPage />);
  const intro = await screen.findByTestId("v2-lesson-intro");
  expect(intro).toHaveTextContent("ماذا سنتعلم؟");
  expect(intro).toHaveTextContent("أميز صوت الحرف في بداية الكلمة");
  expect(screen.getAllByText("أميز صوت الحرف في بداية الكلمة")).toHaveLength(1);
});

it("shows a learner-friendly level rather than internal release/lesson codes", async () => {
  global.fetch = jest.fn(async () => ok(lesson(44, "الحرف وصوته"))) as typeof fetch;
  render(<V2LessonPage />);
  await screen.findByRole("heading", { name: "الحرف وصوته", level: 1 });
  expect(screen.getByText("المستوى الأول · درس القراءة")).toBeVisible();
  expect(screen.queryByText("L1 · L1-01")).not.toBeInTheDocument();
});

it("rejects a cross-session POST acknowledgment and reloads the saved lesson via GET", async () => {
  const base = lesson(44, "الدرس الأصلي");
  const practice = {
    ...base,
    session: { ...base.session, stage: "guided_practice", version: 4 },
    interaction: {
      question: {
        question_id: "LESSON-Q-1", role: "guided_practice", interaction: "choose_one",
        prompt: "اختر الصوت المناسب", stimulus: { text: "بَ", media: [] },
        options: [{ id: "a", text: "بَ", media: [] }, { id: "b", text: "مَ", media: [] }],
      },
      media: {}, progress: { index: 1, total: 2, stage: "guided_practice" },
      attempts: 0,
    },
  };
  let gets = 0;
  const fetcher = jest.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === "POST") return ok({
      submission: { retry_required: false, accepted: true },
      lesson: { ...lesson(45, "درس من جلسة أخرى"), session: { ...base.session, session_id: 45, version: 5 } },
    });
    gets += 1;
    return ok(practice);
  });
  global.fetch = fetcher as typeof fetch;
  render(<V2LessonPage />);
  expect(await screen.findByRole("heading", { name: "الدرس الأصلي", level: 1 })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "اختيار الخيار 1" }));
  fireEvent.click(screen.getByRole("button", { name: "تحقق من الإجابة" }));
  await waitFor(() => expect(gets).toBe(2));
  expect(await screen.findByRole("heading", { name: "الدرس الأصلي", level: 1 })).toBeVisible();
  expect(screen.queryByRole("heading", { name: "درس من جلسة أخرى", level: 1 })).not.toBeInTheDocument();
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
});

it("does not celebrate a failed support check as mastered after a bounded completion", async () => {
  const base = lesson(44, "الحرف وصوته");
  global.fetch = jest.fn(async () => ok({
    ...base,
    session: { ...base.session, stage: "outcome" },
    adaptation: {
      state: "next_lesson", mastery_demonstrated: false,
      message: "أكملت المساعدة، وسنواصل تقوية هذه المهارة في دروسك القادمة.",
    },
  })) as typeof fetch;
  render(<V2LessonPage />);
  expect(await screen.findByText("أكملت محاولة التقوية")).toBeVisible();
  expect(screen.getByText(/سنواصل تقوية هذه المهارة/)).toBeVisible();
  expect(screen.queryByText("أكملت أسئلة الدرس")).not.toBeInTheDocument();
  expect(screen.getByAltText("شخصية هِمّة تشجع الطالب")).toBeInTheDocument();
});
