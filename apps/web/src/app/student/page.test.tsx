import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  rewards: { state: "not_implemented_v2" },
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
    expect(screen.getByText("يظهر تقدم الدروس بعد اعتماد التسكين.")).toBeInTheDocument();
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
    expect(await screen.findByRole("heading", { name: "رحلتك تحتاج مراجعة المشرف" })).toBeInTheDocument();
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
    expect(screen.getByText(/لا نعرض نجومًا قبل اعتماد نظام مكافآت V2/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "متابعة الرحلة التعليمية" }));
    expect(push).toHaveBeenCalledWith("/student/learning-v2");
    expect(fetcher.mock.calls.some(([url]) => url === "/api/rewards")).toBe(false);
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
});
