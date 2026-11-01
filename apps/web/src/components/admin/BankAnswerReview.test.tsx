import { fireEvent, render, screen } from "@testing-library/react";
import BankAnswerReview from "./BankAnswerReview";

it("renders correct assembly order and all accepted alternatives in readable Arabic", () => {
  render(<BankAnswerReview
    options={[{id: "t1", text: "كـ"}, {id: "t2", text: "ـتـ"}, {id: "t3", text: "ـب"}]}
    answer={{correct_option_ids: ["t1", "t2", "t3"], accepted_option_orders: [["t1", "t3", "t2"]]}}
    readingReference={null}
  />);
  fireEvent.click(screen.getByText("الإجابة ومعيار المراجعة"));
  expect(screen.getByTestId("v2-bank-answer")).toHaveTextContent("كـ ← ـتـ ← ـب");
  expect(screen.getByText("ترتيبات أخرى مقبولة:")).toBeInTheDocument();
  expect(screen.getByTestId("v2-bank-answer")).toHaveTextContent("كـ ← ـب ← ـتـ");
  expect(screen.getByTestId("v2-bank-answer").querySelector("pre")).toBeNull();
});

it("shows supervised reading rubrics without exposing raw JSON or technical field names", () => {
  render(<BankAnswerReview options={[]} answer={{correct_option_ids: [], rubric: {target_text: "قِصَه", expected_pronunciation: "قِصَه"}}}
    readingReference={{reading_unit: "كلمة", accepted_variants: ["قِصَه", "قِصَّة"]}} hint="اقرأ بوضوح" />);
  fireEvent.click(screen.getByText("الإجابة ومعيار المراجعة"));
  const details = screen.getByTestId("v2-bank-answer");
  expect(details).toHaveTextContent("معيار التقييم");
  expect(details).toHaveTextContent("النطق المطلوب");
  expect(details).toHaveTextContent("قِصَه");
  expect(details).toHaveTextContent("تلميح التدريب");
  expect(details).not.toHaveTextContent("expected_pronunciation");
  expect(details).not.toHaveTextContent('"rubric"');
});
