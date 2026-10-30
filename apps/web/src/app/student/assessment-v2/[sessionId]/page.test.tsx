import { render, screen } from "@testing-library/react";
import AssessmentV2Page from "./page";

jest.mock("next/navigation", () => ({
  useParams: () => ({ sessionId: "77" }),
  useRouter: () => ({ replace: jest.fn() }),
}));

const oldFetch = global.fetch;
afterEach(() => { global.fetch = oldFetch; });

it.each([
  { kind: "pretest", href: "/student/learning-v2", label: "متابعة الرحلة" },
  { kind: "posttest", href: "/student", label: "العودة إلى لوحتي" },
] as const)("completed $kind returns to the appropriate learner destination", async ({ kind, href, label }) => {
  global.fetch = jest.fn(async () => ({
    ok: true, status: 200,
    json: async () => ({
      session: { session_id: 77, kind, state: "completed", progress: { answered: 30, total: 30 } },
      interaction: null, summary: { pending_review: 0 },
      outcome: { score_percent: 80, skills: {} },
    }),
  })) as unknown as typeof fetch;
  render(<AssessmentV2Page />);
  expect(await screen.findByRole("link", { name: label })).toHaveAttribute("href", href);
});
