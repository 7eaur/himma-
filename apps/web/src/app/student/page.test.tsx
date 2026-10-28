import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import StudentPage from "./page";
import type { StudentV2Home } from "./V2StudentDashboard";

const push = jest.fn();
const replace = jest.fn();
const refresh = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
}));

function response(body: unknown, status = 200) {
  return { status, ok: status >= 200 && status < 300, json: async () => body };
}

const firstTime: StudentV2Home = {
  mode: "v2", test_only: true,
  student: { id: 1, full_name: "طالب تجريبي", grade_level: 3 },
  current_action: { action: "start_pretest", href: null, label: "ابدأ الاختبار القبلي" },
  journey: null,
  progress: { completed_lessons: 0, assigned_lessons: null, skipped_by_placement: 0, pending_review: 0, display_percent: null },
  assessments: { pretest: null, posttest: null },
  rewards: { state: "ready", source: "himma_v2_reward_ledger", policy_version: "himma-v2-effort/1", total_stars: 0, badges: [], lessons: [] },
  data_status: "ready",
};

function mockV2(home: StudentV2Home = firstTime) {
  const fetcher = jest.fn(async (url: string) => {
    if (url === "/api/v2/student/home") return response(home);
    if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [], next_offset: null });
    return response({ detail: "Unexpected legacy API call" }, 503);
  });
  global.fetch = fetcher as unknown as typeof fetch;
  return fetcher;
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Student page V2-only learner boundary", () => {
  it("shows first-time V2 pretest without inventing historical rewards or a score", async () => {
    const fetcher = mockV2();
    render(<StudentPage />);
    expect(await screen.findByRole("heading", { name: "مرحبًا يا طالب" })).toBeInTheDocument();
    expect(screen.getByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
    expect(screen.getByRole("button", { name: "ابدأ الاختبار القبلي" })).toBeEnabled();
    expect(screen.getByText("يظهر تقدم الدروس بعد تحديد مستواك.")).toBeInTheDocument();
    expect(screen.queryByText("تجاوزتها بالتسكين")).not.toBeInTheDocument();
    expect(screen.queryByText("بانتظار المراجعة")).not.toBeInTheDocument();
    expect(screen.getByText("سنحدد مستواك تلقائيًا بعد الاختبار القبلي ومراجعة القراءة.")).toBeInTheDocument();
    expect(screen.queryByText(/قيد التجربة/)).not.toBeInTheDocument();
    expect(screen.queryByTestId("student-badges")).not.toBeInTheDocument();
    expect(fetcher.mock.calls.some(([url]) => ["/api/profile", "/api/journey", "/api/rewards"].includes(url))).toBe(false);
  });

  it("fails closed when V2 is unavailable and never falls back to /api/profile", async () => {
    const fetcher = jest.fn().mockResolvedValue(response({ detail: "service unavailable" }, 503));
    global.fetch = fetcher;
    render(<StudentPage />);
    expect(await screen.findByText(/رحلة هِمّة غير متاحة الآن/)).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith("/api/v2/student/home", { cache: "no-store" });
    expect(screen.queryByTestId("student-home")).not.toBeInTheDocument();
  });

  it("redirects expired student session instead of loading any V1 endpoint", async () => {
    const fetcher = jest.fn().mockResolvedValue(response({ detail: "unauthorized" }, 401));
    global.fetch = fetcher;
    render(<StudentPage />);
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/student/login"));
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("blocks a historical account until the supervisor reviews its migration", async () => {
    const fetcher = mockV2({
      ...firstTime,
      current_action: { action: "migration_review", href: null, label: "بانتظار مراجعة المشرف" },
    });
    render(<StudentPage />);
    expect(await screen.findByRole("heading", { name: "رحلتك جاهزة للمراجعة" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "بانتظار مراجعة المشرف" })).toBeDisabled();
    expect(screen.queryByText("ابدأ الاختبار القبلي")).not.toBeInTheDocument();
    expect(fetcher.mock.calls.some(([url]) => url === "/api/profile")).toBe(false);
  });

  it("shows assigned V2 lesson progress separately from placement skips, not V1 stars", async () => {
    const fetcher = mockV2({
      ...firstTime,
      journey: { current_level: 2, placement_state: "placed", current_lesson_id: "L2-01", content_release_version: "candidate" },
      current_action: { action: "lesson_catalog", href: "/student/learning-v2", label: "متابعة الرحلة التعليمية" },
      progress: { completed_lessons: 3, assigned_lessons: 14, skipped_by_placement: 5, pending_review: 0, display_percent: 21.4 },
    });
    render(<StudentPage />);
    expect(await screen.findByText("أكملت 3 من 14 درسًا مخصصًا لك.")).toBeInTheDocument();
    expect(screen.getByTestId("student-journey-status")).toHaveTextContent("الحركات والكلمات");
    expect(screen.getByTestId("student-v2-progress")).toHaveTextContent("21.4%");
    expect(screen.queryByText("تجاوزتها بالتسكين")).not.toBeInTheDocument();
    expect(screen.getByTestId("v2-star-total")).toHaveTextContent("0 نجمة");
    fireEvent.click(screen.getByRole("button", { name: "متابعة الرحلة التعليمية" }));
    expect(push).toHaveBeenCalledWith("/student/learning-v2");
    expect(fetcher.mock.calls.some(([url]) => url === "/api/rewards")).toBe(false);
  });

  it.each([
    17,
    { path: "/student/learning-v2" },
    ["/student/learning-v2"],
    true,
    "",
    "   ",
    "javascript:alert(1)",
    "//external.invalid/student",
    "https://external.invalid/student",
    "/student/../admin",
    "/admin",
    "/student\\\\external",
  ].map(href => ({ href })))("refuses unsafe V2 action navigation ($href) without leaving the learner surface", async ({ href }) => {
    mockV2({
      ...firstTime,
      // Deliberately model unvalidated response.json(), including non-string JSON.
      current_action: { action: "lesson_catalog", href: href as string, label: "متابعة الرحلة التعليمية" },
    });
    render(<StudentPage />);
    fireEvent.click(await screen.findByRole("button", { name: "متابعة الرحلة التعليمية" }));
    expect(push).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("تعذر التحقق من رابط الرحلة");
    expect(screen.getByTestId("student-identity")).toBeInTheDocument();
  });

  it("keeps pending human reading review free of fictitious official grades", async () => {
    mockV2({
      ...firstTime,
      current_action: {
        action: "assessment", kind: "pretest", state: "waiting_review",
        href: "/student/assessment-v2/77", label: "عرض حالة المراجعة",
      },
      assessments: { pretest: { state: "waiting_review", session_id: 77, official: false, score_percent: null }, posttest: null },
    });
    render(<StudentPage />);
    expect(await screen.findByRole("heading", { name: "بانتظار مراجعة القراءة" })).toBeInTheDocument();
    expect(screen.getByText(/تم حفظ إجاباتك، وستكمل رحلتك بعد مراجعة المشرف/)).toBeInTheDocument();
    expect(screen.queryByText("0%", { exact: true })).not.toBeInTheDocument();
    expect(screen.queryByTestId("student-badges")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "عرض حالة المراجعة" }));
    expect(push).toHaveBeenCalledWith("/student/assessment-v2/77");
  });

  it("uses the real V2 pretest start endpoint for new students", async () => {
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/v2/assessments/pretest/start") return response({ session: { session_id: 101 } });
      return response({ detail: "Unexpected legacy API call" }, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    fireEvent.click(await screen.findByRole("button", { name: "ابدأ الاختبار القبلي" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/student/assessment-v2/101"));
    expect(fetcher).toHaveBeenCalledWith("/api/v2/assessments/pretest/start", { method: "POST" });
    expect(fetcher.mock.calls.some(([url]) => url === "/api/assessment/start")).toBe(false);
  });

  it("rejects an unexpected legacy mode instead of showing historical learner UI", async () => {
    const fetcher = mockV2({ ...firstTime, mode: "legacy" });
    render(<StudentPage />);
    expect(await screen.findByText(/تعذر التحقق من رحلة هِمّة/)).toBeInTheDocument();
    expect(screen.queryByTestId("student-home")).not.toBeInTheDocument();
    expect(fetcher.mock.calls.some(([url]) => url === "/api/profile")).toBe(false);
  });

  it("can retry a temporarily unavailable V2 source without fetching any V1 endpoint", async () => {
    const fetcher = jest.fn()
      .mockResolvedValueOnce(response({ detail: "temporary failure" }, 503))
      .mockResolvedValueOnce(response(firstTime))
      .mockResolvedValue(response({ items: [], next_offset: null }));
    global.fetch = fetcher;
    render(<StudentPage />);
    fireEvent.click(await screen.findByRole("button", { name: "إعادة المحاولة" }));
    expect(await screen.findByTestId("student-home")).toHaveAttribute("data-learning-version", "v2");
    expect(fetcher.mock.calls.some(([url]) => url === "/api/profile")).toBe(false);
  });

  it("hides the previous student's identity while logout is pending", async () => {
    let finishLogout!: (value: ReturnType<typeof response>) => void;
    const pendingLogout = new Promise<ReturnType<typeof response>>(resolve => { finishLogout = resolve; });
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/auth/logout") return pendingLogout;
      return response({}, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    expect(await screen.findByTestId("student-identity")).toHaveTextContent("طالب");
    fireEvent.click(screen.getByRole("button", { name: /خروج/ }));
    expect(screen.queryByTestId("student-identity")).not.toBeInTheDocument();
    expect(screen.queryByTestId("student-home")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("جاري تسجيل الخروج");
    expect(replace).not.toHaveBeenCalledWith("/");
    finishLogout(response({}));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/"));
  });

  it("keeps student data hidden on failed logout and retries before redirecting", async () => {
    let logoutCalls = 0;
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/auth/logout") return response({}, ++logoutCalls === 1 ? 503 : 200);
      return response({}, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    fireEvent.click(await screen.findByRole("button", { name: /خروج/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تأكيد تسجيل الخروج");
    expect(screen.queryByTestId("student-identity")).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalledWith("/");
    fireEvent.click(screen.getByRole("button", { name: "إعادة محاولة تسجيل الخروج" }));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/"));
    expect(logoutCalls).toBe(2);
  });

  it("coalesces rapid logout taps and allows one explicit retry after a failed response", async () => {
    let finishLogout!: (value: ReturnType<typeof response>) => void;
    const pendingLogout = new Promise<ReturnType<typeof response>>(resolve => { finishLogout = resolve; });
    let logoutCalls = 0;
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/auth/logout") return ++logoutCalls === 1 ? pendingLogout : response({});
      return response({}, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    const button = await screen.findByRole("button", { name: /خروج/ });
    // Both events run before React commits the pending state.
    act(() => {
      fireEvent.click(button);
      fireEvent.click(button);
    });
    expect(logoutCalls).toBe(1);
    expect(screen.queryByTestId("student-identity")).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalledWith("/");
    finishLogout(response({}, 503));
    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تأكيد تسجيل الخروج");
    fireEvent.click(screen.getByRole("button", { name: "إعادة محاولة تسجيل الخروج" }));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/"));
    expect(logoutCalls).toBe(2);
    expect(screen.queryByTestId("student-identity")).not.toBeInTheDocument();
  });

  it("ignores a late pretest start acknowledgement after logout", async () => {
    let finishStart!: (value: ReturnType<typeof response>) => void;
    const pendingStart = new Promise<ReturnType<typeof response>>(resolve => { finishStart = resolve; });
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/v2/assessments/pretest/start") return pendingStart;
      if (url === "/api/auth/logout") return response({});
      return response({}, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    fireEvent.click(await screen.findByRole("button", { name: "ابدأ الاختبار القبلي" }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledWith("/api/v2/assessments/pretest/start", { method: "POST" }));
    fireEvent.click(screen.getByRole("button", { name: /خروج/ }));
    expect(screen.queryByTestId("student-identity")).not.toBeInTheDocument();
    finishStart(response({ session: { session_id: 101 } }));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/"));
    expect(push).not.toHaveBeenCalledWith("/student/assessment-v2/101");
  });

  it.each([0, -1, Number.MAX_SAFE_INTEGER + 1])(
    "rejects an invalid pretest session id (%s) instead of navigating", async sessionId => {
      const fetcher = jest.fn(async (url: string) => {
        if (url === "/api/v2/student/home") return response(firstTime);
        if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
        if (url === "/api/v2/assessments/pretest/start") return response({ session: { session_id: sessionId } });
        return response({}, 503);
      });
      global.fetch = fetcher as unknown as typeof fetch;
      render(<StudentPage />);
      fireEvent.click(await screen.findByRole("button", { name: "ابدأ الاختبار القبلي" }));
      expect(await screen.findByRole("alert")).toHaveTextContent("تعذر التحقق من جلسة الاختبار");
      expect(push).not.toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "ابدأ الاختبار القبلي" })).toBeEnabled();
      expect(fetcher.mock.calls.filter(([url]) => url === "/api/v2/assessments/pretest/start")).toHaveLength(1);
    },
  );

  it("does not send a second pretest start while the first acknowledgement is pending", async () => {
    let finishStart!: (value: ReturnType<typeof response>) => void;
    const pendingStart = new Promise<ReturnType<typeof response>>(resolve => { finishStart = resolve; });
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/v2/assessments/pretest/start") return pendingStart;
      return response({}, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    const button = await screen.findByRole("button", { name: "ابدأ الاختبار القبلي" });
    fireEvent.click(button);
    fireEvent.click(button);
    expect(fetcher.mock.calls.filter(([url]) => url === "/api/v2/assessments/pretest/start")).toHaveLength(1);
    finishStart(response({ session: { session_id: 101 } }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/student/assessment-v2/101"));
  });

  it.each([401, 403])(
    "hides learner identity and returns to login when pretest start is denied (%s)",
    async status => {
      const fetcher = jest.fn(async (url: string) => {
        if (url === "/api/v2/student/home") return response(firstTime);
        if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
        if (url === "/api/v2/assessments/pretest/start") return response({ detail: "denied" }, status);
        return response({}, 503);
      });
      global.fetch = fetcher as unknown as typeof fetch;
      render(<StudentPage />);
      fireEvent.click(await screen.findByRole("button", { name: "ابدأ الاختبار القبلي" }));
      await waitFor(() => expect(replace).toHaveBeenCalledWith("/student/login"));
      expect(screen.queryByTestId("student-identity")).not.toBeInTheDocument();
      expect(screen.queryByTestId("student-home")).not.toBeInTheDocument();
      expect(screen.getByRole("alert")).toHaveTextContent("تعذر التحقق من صلاحية الدخول");
      expect(push).not.toHaveBeenCalled();
      expect(fetcher.mock.calls.filter(([url]) => url === "/api/v2/assessments/pretest/start")).toHaveLength(1);
    },
  );

  it.each([
    { status: 409, message: "لا يمكن بدء اختبار جديد الآن" },
    { status: 503, message: "الاختبار غير متاح حاليًا" },
  ])("preserves the V2 start action after a $status failure for explicit retry", async ({ status, message }) => {
    let starts = 0;
    const fetcher = jest.fn(async (url: string) => {
      if (url === "/api/v2/student/home") return response(firstTime);
      if (url.startsWith("/api/v2/retries/student/tasks")) return response({ items: [] });
      if (url === "/api/v2/assessments/pretest/start") {
        starts += 1;
        return starts === 1 ? response({ detail: "temporary" }, status) : response({ session: { session_id: 101 } });
      }
      return response({}, 503);
    });
    global.fetch = fetcher as unknown as typeof fetch;
    render(<StudentPage />);
    fireEvent.click(await screen.findByRole("button", { name: "ابدأ الاختبار القبلي" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("button", { name: "ابدأ الاختبار القبلي" })).toBeEnabled();
    expect(starts).toBe(1);
    expect(push).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "ابدأ الاختبار القبلي" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/student/assessment-v2/101"));
    expect(starts).toBe(2);
    expect(fetcher.mock.calls.some(([url]) => url === "/api/profile")).toBe(false);
  });

});

// A supervisor rerecord task must open its own focused learner page,
// not hide below a long dashboard or recreate a complete assessment.
it("opens the specific rerecord request from the main learner action", async () => {
  push.mockClear();
  mockV2({...firstTime,current_action:{
    action:"rerecord_required",kind:"lesson",state:"requested",task_id:23,session_id:10,
    href:"/student/retry/23",label:"أعد تسجيل القراءة",
  }});
  render(<StudentPage/>);
  const button=await screen.findByTestId("student-primary-action");
  fireEvent.click(button);
  expect(push).toHaveBeenCalledWith("/student/retry/23");
});

// Waiting assessment evidence must never be depicted as an invented zero.
it("keeps assessment review as a clear action without false dashboard counts", async () => {
  mockV2({...firstTime,current_action:{action:"assessment",kind:"pretest",state:"waiting_review",href:"/student/assessment-v2/42",label:"عرض حالة المراجعة"}});
  render(<StudentPage/>);
  expect(await screen.findByRole("heading",{name:"بانتظار مراجعة القراءة"})).toBeInTheDocument();
  expect(screen.getByTestId("student-v2-progress")).not.toHaveTextContent("بانتظار المراجعة");
  expect(screen.queryByText("TEST ONLY")).not.toBeInTheDocument();
});
