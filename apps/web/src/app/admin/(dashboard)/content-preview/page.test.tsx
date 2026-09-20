import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ContentPreviewPage from "./page";

jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: React.ImgHTMLAttributes<HTMLImageElement>) => <img {...props} alt={props.alt ?? ""} />,
}));

const indexPayload = {
  mode: "read_only",
  purpose: "admin_content_review",
  writes_progress: false,
  count: 1,
  active_release: { version: "HIMMA-CONTENT-APPROVAL-2026-09-08", is_active: true },
  items: [{
    id: 1,
    canonical_id: "L1-CORE-01",
    stable_key: "l1-core-01",
    kind: "core_activity",
    level_id: 1,
    order_index: 1,
    interaction_type: "choose_one",
    title: "اختر الإجابة الصحيحة",
    skill: "تمييز الحرف",
    status: "published",
    round_count: 1,
    has_audio: false,
    has_images: false,
    requires_recording: false,
    reinforcement_candidates: [],
    search_text: "اختر الإجابة الصحيحة تمييز الحرف L1-CORE-01",
  }],
};

const detailPayload = {
  mode: "read_only",
  purpose: "admin_content_review",
  writes_progress: false,
  summary: indexPayload.items[0],
  item: {
    ...indexPayload.items[0],
    criterion: "اختيار الحرف الصحيح",
    context_intro: null,
    item_assets: [],
  },
  rounds: [{
    id: 10,
    order_index: 1,
    round_number: 1,
    round_total: 1,
    question_text: "أي حرف هو ب؟",
    instruction_text: "اختر الحرف الصحيح",
    encouragement: "أحسنت التركيز",
    hint: "انظر إلى النقطة",
    stimulus: {},
    stimulus_text: "",
    options: [
      { id: 1, text: "ب", order_index: 1, is_correct: true },
      { id: 2, text: "ت", order_index: 2, is_correct: false },
    ],
    assets: [],
    media_gaps: [],
    answer: { kind: "correct_options", label: "الإجابة الصحيحة", values: ["ب"], option_ids: [1] },
  }],
};

beforeEach(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches: query.includes("max-width: 820px"),
      media: query,
      onchange: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
  global.fetch = jest.fn((input: RequestInfo | URL) => {
    const url = String(input);
    return Promise.resolve({
      ok: true,
      json: async () => url.includes("L1-CORE-01") ? detailPayload : indexPayload,
    } as Response);
  }) as jest.Mock;
});

afterEach(() => {
  jest.restoreAllMocks();
});

test("keeps the library as the first mobile view and opens detail explicitly", async () => {
  render(<ContentPreviewPage />);
  expect(await screen.findByTestId("content-library")).toBeInTheDocument();
  expect(screen.queryByTestId("content-detail")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /اختر الإجابة الصحيحة/ }));
  expect(await screen.findByTestId("content-detail")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "العودة إلى المحتوى" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "العودة إلى المحتوى" }));
  await waitFor(() => expect(screen.getByTestId("content-library")).toBeInTheDocument());
});

test("does not repeat a correct choice in a second answer block", async () => {
  render(<ContentPreviewPage />);
  fireEvent.click(await screen.findByRole("button", { name: /اختر الإجابة الصحيحة/ }));
  expect(await screen.findByText("أي حرف هو ب؟")).toBeInTheDocument();
  expect(screen.getByText("إجابة صحيحة")).toBeInTheDocument();
  expect(screen.queryByText("الإجابة الصحيحة")).not.toBeInTheDocument();
});
