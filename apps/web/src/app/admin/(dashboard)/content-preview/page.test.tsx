import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import ContentBankPage from "./page";

const bank = {
  mode: "read_only", bank_total: 300, total: 1, offset: 0, next_offset: null,
  release_version: "v2-test", release_state: "candidate_not_approved",
  sections: [{ id: "L1-01", title: "الحرف وصوته", kind: "lesson", question_count: 8,
    intro: { text: "تمهيد الدرس المعتمد" }, objective: "ربط الحرف بالصوت" }],
  items: [{ section_id: "pretest", question: { question_id: "V2-PRE-Q01", role: "pretest", interaction: "choose_one",
    prompt: "اختر الحرف ج.", skill_group: "S1", stimulus: { text: null }, options: [{ id: "a", text: "ج" }] },
    answer: { correct_option_ids: ["a"] }, media: [] }],
};
it("loads the V2 bank with section intro and never requests the archive implicitly", async () => {
  const fetcher = jest.fn().mockResolvedValue({ ok: true, json: async () => bank });
  global.fetch = fetcher;
  render(<ContentBankPage />);
  expect(await screen.findByTestId("v2-bank-question")).toHaveTextContent("V2-PRE-Q01");
  expect(screen.getByRole("group", { name: "المستوى الأول" })).toBeInTheDocument();
  expect(screen.getByTestId("v2-bank-question")).toHaveAttribute("open");
  expect(screen.getByRole("combobox", { name: "اختر سؤالًا لعرض تفاصيله" })).toHaveValue("V2-PRE-Q01");
  expect(screen.getByRole("link", { name: "ملف مراجعة المحتوى Excel" })).toHaveAttribute(
    "href", "/api/v2/content/admin/review-export.xlsx"
  );
  expect(screen.getByRole("option", { name: "البنك كاملًا · 300 سؤال" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /المستوى الأول/ }));
  expect(await screen.findByText("التمهيد: تمهيد الدرس المعتمد")).toBeInTheDocument();
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => url.includes("section=L1-01"))).toBe(true));
  expect(fetcher.mock.calls.every(([url]) => url.startsWith("/api/v2/content/admin/bank?"))).toBe(true);
  expect(screen.queryByTestId("content-index-item")).not.toBeInTheDocument();
  expect(screen.queryByText("أرشيف بنك V1")).not.toBeInTheDocument();
});
it("keeps a bank source error unavailable and permits retry", async () => {
  global.fetch = jest.fn().mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({detail:"الخدمة غير متاحة"}) }).mockResolvedValueOnce({ ok: true, json: async () => bank });
  render(<ContentBankPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل بنك الأسئلة");
  expect(screen.queryByTestId("v2-bank-question")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
  expect(await screen.findByTestId("v2-bank-question")).toBeInTheDocument();
});


it("debounces consecutive Arabic bank searches instead of requesting private pages per letter", async () => {
  const fetcher = jest.fn().mockResolvedValue({ok: true, json: async () => bank});
  global.fetch = fetcher;
  render(<ContentBankPage/>);
  await screen.findByTestId("v2-bank-question");
  jest.useFakeTimers();
  try {
    const field = screen.getByRole("textbox", {name: "بحث في السؤال أو النص أو الخيارات أو المعرّف"});
    fireEvent.change(field, {target: {value: "م"}});
    fireEvent.change(field, {target: {value: "مد"}});
    fireEvent.change(field, {target: {value: "مدر"}});
    expect(fetcher).toHaveBeenCalledTimes(1);
    await act(async () => {
      jest.advanceTimersByTime(300);
      await Promise.resolve();
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(fetcher.mock.calls[1][0]).toContain("search=%D9%85%D8%AF%D8%B1");
  } finally {
    jest.useRealTimers();
  }
});

it("shows a reviewer-readable answer instead of raw private JSON payloads", async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => bank });
  render(<ContentBankPage />);
  const question = await screen.findByTestId("v2-bank-question");
  fireEvent.click(screen.getByText("الإجابة ومعيار المراجعة"));
  expect(question).toHaveTextContent("الإجابة الصحيحة: ج");
  expect(question.querySelector("pre")).toBeNull();
  expect(question).not.toHaveTextContent('"correct_option_ids"');
});

it("lets a supervisor clear an empty content search instead of displaying an unhelpful blank page", async () => {
  const fetcher = jest.fn().mockResolvedValue({ ok: true, json: async () => bank });
  global.fetch = fetcher;
  render(<ContentBankPage />);
  await screen.findByTestId("v2-bank-question");
  fireEvent.change(screen.getByRole("textbox", {name: "بحث في السؤال أو النص أو الخيارات أو المعرّف"}), {
    target: {value: "كلمة غير موجودة"},
  });
  // The reset action is only displayed when the server returns no matching items.
  fetcher.mockResolvedValue({ok: true, json: async () => ({...bank, total: 0, items: []})});
  await waitFor(() => expect(screen.getByText("لا توجد أسئلة مطابقة")).toBeInTheDocument());
  fireEvent.click(screen.getByRole("button", {name: "مسح البحث والتصفية"}));
  expect(screen.getByRole("textbox", {name: "بحث في السؤال أو النص أو الخيارات أو المعرّف"})).toHaveValue("");
});
