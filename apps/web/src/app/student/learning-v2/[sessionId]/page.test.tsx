import { act, render, screen, waitFor } from "@testing-library/react";
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
