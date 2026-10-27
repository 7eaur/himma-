import { fireEvent, render, screen } from "@testing-library/react";
import V2ReadingRubricEditor, { emptyReadingRubric, readingObservation, rubricValid } from "./V2ReadingRubricEditor";

test("requires valid numeric units and rejects impossible deletion plus substitution counts", () => {
  expect(rubricValid(emptyReadingRubric())).toBe(false);
  const valid = {...emptyReadingRubric(), target_units: 5, deletions: 1, substitutions: 1, insertions: 1};
  expect(rubricValid(valid)).toBe(true);
  expect(readingObservation(valid)).toBe(40);
  expect(rubricValid({...valid, deletions: 4, substitutions: 2})).toBe(false);
  expect(rubricValid({...valid, deletions: -1})).toBe(false);
});

test("keeps human verdict independent of a descriptive 100-percent observation", () => {
  const complete = {...emptyReadingRubric(), target_units: 3};
  expect(rubricValid(complete)).toBe(true);
  expect(readingObservation(complete)).toBe(100);
  const onChange = jest.fn();
  render(<V2ReadingRubricEditor value={complete} onChange={onChange} disabled={false}/>);
  expect(screen.getByText(/التقدير الرقمي الوصفي: 100%/)).toBeInTheDocument();
  expect(screen.queryByText(/ناجح تلقائيًا/)).not.toBeInTheDocument();
  fireEvent.change(screen.getByRole("spinbutton", {name: "أخطاء الحذف"}), {target: {value: "1"}});
  expect(onChange).toHaveBeenCalledWith(expect.objectContaining({deletions: 1, target_units: 3}));
});

test("prevents editing while a review decision is pending", () => {
  render(<V2ReadingRubricEditor value={emptyReadingRubric()} onChange={jest.fn()} disabled={true}/>);
  expect(screen.getByRole("group", {name: /تقدير القراءة بالأرقام/})).toBeDisabled();
});
