import { render, screen } from "@testing-library/react";
import StudentPage from "./page";

const push = jest.fn();
const replace = jest.fn();
const refresh = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
}));

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 1,
        full_name: "طالب تجريبي",
        grade_level: 3,
        current_level: 1,
        posttest_enabled: false,
        next_action: "pretest",
        active_session: null,
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });
});

describe("Student page", () => {
  it("renders the student's first name", async () => {
    render(<StudentPage />);
    expect(await screen.findByRole("heading", { name: "مرحبًا يا طالب" })).toBeInTheDocument();
  });

  it("offers the pretest when there is no active session", async () => {
    render(<StudentPage />);
    expect(await screen.findByRole("button", { name: "ابدأ الاختبار" })).toBeEnabled();
    expect(screen.getByRole("heading", { name: "الاختبار القبلي" })).toBeInTheDocument();
  });
});
