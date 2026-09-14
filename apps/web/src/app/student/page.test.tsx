import { fireEvent, render, screen } from "@testing-library/react";
import StudentPage from "./page";

const push = jest.fn();
const replace = jest.fn();
const refresh = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
}));

function response(body: unknown, ok = true) {
  return {
    ok,
    json: async () => body,
  };
}

const profile = {
  id: 1,
  full_name: "طالب تجريبي",
  grade_level: 3,
  current_level: 1,
  posttest_enabled: false,
  next_action: "pretest" as const,
  active_session: null,
};

const journey = {
  pretest_completed: false,
  starting_level: null,
  current_level: 1,
  levels: [],
  learning_journey_completed: false,
  posttest_enabled: false,
  posttest_completed: false,
  posttest_ready: false,
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Student page", () => {
  it("renders the student's first name and explicit empty reward state before placement", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(profile))
      .mockResolvedValueOnce(response(journey))
      .mockResolvedValueOnce(response([]));

    render(<StudentPage />);
    expect(await screen.findByRole("heading", { name: "مرحبًا يا طالب" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ابدأ الاختبار" })).toBeEnabled();
    expect(screen.getByRole("heading", { name: "الاختبار القبلي" })).toBeInTheDocument();
    expect(screen.getByLabelText("لديك 0 نجمة")).toBeInTheDocument();
    expect(screen.getByLabelText("لا توجد شارات مكتسبة")).toBeInTheDocument();
    expect(screen.getByText("لم تحصل على شارة بعد")).toBeInTheDocument();
    expect(screen.queryByTestId("level-journey")).not.toBeInTheDocument();
  });

  it("renders reward API failure as unavailable instead of a false zero or empty badge state", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(profile))
      .mockResolvedValueOnce(response(journey))
      .mockResolvedValueOnce(response({ detail: "temporary failure" }, false));

    render(<StudentPage />);

    expect(await screen.findByRole("heading", { name: "مرحبًا يا طالب" })).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "تعذر تحميل النجوم" })).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "تعذر تحميل الشارات" })).toBeInTheDocument();
    expect(screen.getByText("تعذر تحميل نجومك")).toBeInTheDocument();
    expect(screen.getByText("الشارات غير متاحة الآن")).toBeInTheDocument();
    expect(screen.queryByLabelText("لديك 0 نجمة")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("لا توجد شارات مكتسبة")).not.toBeInTheDocument();
  });

  it("renders canonical star total and badge asset from the reward catalog API contract", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(profile))
      .mockResolvedValueOnce(response(journey))
      .mockResolvedValueOnce(response([
        {
          id: 1,
          type: "stars",
          key: "activity:11:stars",
          stars: 2,
          label: "نجمتان",
          catalog_version: "HIMMA_REWARD_CATALOG_1.0.0",
          asset_id: "BDG-02",
          asset_path: "/assets/rewards/svg/hem-bdg-02-stars-two.svg",
        },
        {
          id: 2,
          type: "badge",
          key: "level:1:core-complete",
          stars: null,
          label: "مستكشف الحروف",
          catalog_version: "HIMMA_REWARD_CATALOG_1.0.0",
          asset_id: "BDG-04",
          asset_path: "/assets/rewards/svg/hem-bdg-04-letter-explorer.svg",
        },
      ]));

    render(<StudentPage />);

    expect(await screen.findByRole("heading", { name: "مرحبًا يا طالب" })).toBeInTheDocument();
    expect(screen.getByLabelText("لديك 2 نجمة")).toBeInTheDocument();
    expect(screen.getByText("2 ⭐")).toBeInTheDocument();
    expect(screen.getByLabelText("لديك 1 شارة")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "شارة مستكشف الحروف" })).toBeInTheDocument();
    expect(screen.getByText("مستكشف الحروف")).toBeInTheDocument();
    expect(screen.queryByText("تعذر تحميل نجومك")).not.toBeInTheDocument();
  });

  it("shows skipped, completed and active levels without claiming skipped work was completed", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({
        id: 1,
        full_name: "طالب تجريبي",
        grade_level: 3,
        current_level: 3,
        posttest_enabled: false,
        next_action: "learning",
        active_session: { id: 33, session_type: "core", status: "in_progress" },
      }))
      .mockResolvedValueOnce(response({
        available: true,
        level_id: 3,
        completed_items: 4,
        total_items: 10,
        completed: false,
        session_id: 33,
      }))
      .mockResolvedValueOnce(response({
        pretest_completed: true,
        starting_level: 2,
        current_level: 3,
        levels: [
          { level_id: 1, name: "الاستعداد للقراءة", state: "skipped", completed_items: 0, total_items: 10, session_id: null },
          { level_id: 2, name: "بناء الكلمة", state: "completed", completed_items: 10, total_items: 10, session_id: 22 },
          { level_id: 3, name: "الطلاقة والفهم", state: "active", completed_items: 4, total_items: 10, session_id: 33 },
        ],
        learning_journey_completed: false,
        posttest_enabled: false,
        posttest_completed: false,
        posttest_ready: false,
      }))
      .mockResolvedValueOnce(response([]));

    render(<StudentPage />);
    expect(await screen.findByTestId("level-journey")).toBeInTheDocument();
    expect(screen.getByText("بدأت من المستوى 2")).toBeInTheDocument();
    expect(screen.getByText("تجاوزته في الاختبار القبلي")).toBeInTheDocument();
    expect(screen.getByText("أنت هنا")).toBeInTheDocument();
    expect(screen.getByText("10 من 10 أنشطة أساسية")).toBeInTheDocument();
    expect(screen.getByText("4 من 10 أنشطة أساسية")).toBeInTheDocument();
  });

  it("shows pending audio review and never resumes the assessment", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({
        id: 1,
        full_name: "طالب تجريبي",
        grade_level: 3,
        current_level: 1,
        posttest_enabled: false,
        next_action: "resume",
        active_session: { id: 77, session_type: "pretest", status: "waiting_audio_review" },
      }))
      .mockResolvedValueOnce(response({
        pretest_completed: false,
        starting_level: null,
        current_level: 1,
        levels: [],
        learning_journey_completed: false,
        posttest_enabled: false,
        posttest_completed: false,
        posttest_ready: false,
      }))
      .mockResolvedValueOnce(response([]));

    render(<StudentPage />);

    expect(await screen.findByRole("heading", { name: "بانتظار مراجعة التسجيلات" })).toBeInTheDocument();
    expect(screen.getByText("بانتظار التقييم الصوتي")).toBeInTheDocument();
    expect(screen.getByText("اكتملت الأسئلة، والمتبقي مراجعة التسجيلات فقط.")).toBeInTheDocument();
    const action = screen.getByRole("button", { name: "تم إرسال التسجيلات للمراجعة" });
    expect(action).toBeDisabled();
    fireEvent.click(action);
    expect(push).not.toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledTimes(3);
  });
});