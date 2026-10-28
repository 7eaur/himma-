import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import V2AudioReviewQueue, { type AudioReviewItem } from "./V2AudioReviewQueue";

const item: AudioReviewItem = {
  response_id: 21, student_id: 4, student_name: "طالب اصطناعي", question_id: "Q-1",
  kind: "pretest", lesson_id: "L1-01", interaction: "read_aloud", prompt: "اقرأ الكلمة", stimulus_text: "بَاب",
  audio_url: "/api/private-audio", audio_submission_id: 31, audio_playback_completed: false,
  evidence_ready: true, submitted_at: "2026-10-28T10:00:00Z",
};
const ok = (data: unknown) => ({ok: true, json: async () => data});
let saved: boolean;
let failSave: boolean;
let fetcher: jest.Mock;
beforeEach(() => {
  saved = false; failSave = false;
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  fetcher = jest.fn(async (url: string, options?: RequestInit) => {
    if (options?.method === "POST") {
      if (url.endsWith("audio-completed")) return ok({status:"playback_completed"});
      if (failSave) return {ok:false,json:async()=>({detail:"تغير التسجيل؛ حدّث القائمة"})};
      saved = true; return ok({status:"graded"});
    }
    return ok({items:saved?[]:[item],next_offset:null});
  });
  global.fetch = fetcher;
});
async function open(kind: "assessment" | "lesson" = "assessment") {
  render(<V2AudioReviewQueue kind={kind} />);
  await screen.findByRole("table",{name:"تسجيلات تحتاج مراجعة"});
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:/مراجعة تسجيل طالب اصطناعي/}));
  return screen.getByRole("dialog");
}

it.each(["assessment", "lesson"] as const)("%s opens from a table and accepts only after listening without a lease or mandatory rubric", async kind => {
  const dialog = await open(kind);
  expect(within(dialog).getByText("بَاب")).toBeVisible();
  expect(within(dialog).queryByTestId("v2-reading-rubric")).not.toBeInTheDocument();
  const accept = within(dialog).getByRole("button",{name:"القراءة صحيحة"});
  expect(accept).toBeDisabled();
  fireEvent.ended(within(dialog).getByLabelText("استمع للتسجيل كاملًا قبل التقييم"));
  await waitFor(()=>expect(accept).toBeEnabled());
  fireEvent.click(accept);
  expect(await screen.findByText("اعتُمدت القراءة الصحيحة وحُفظ القرار.")).toBeVisible();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  const url = kind === "assessment" ? "/api/v2/assessments/admin/responses/21/review" : "/api/v2/review/lessons/21/decision";
  const body=JSON.parse(fetcher.mock.calls.find(([path])=>path===url)![1].body);
  expect(body.is_correct).toBe(true);
  expect(body.rubric).toBeUndefined();
  expect(body.note).toBe("");
  expect(fetcher.mock.calls.every(([path])=>!path.includes("claim"))).toBe(true);
});

it("requires a useful retry reason and sends a retry task rather than grading as wrong", async () => {
  const dialog = await open("lesson");
  const retryButton = within(dialog).getByRole("button",{name:"طلب إعادة التسجيل"});
  expect(retryButton).toBeDisabled();
  fireEvent.ended(within(dialog).getByLabelText("استمع للتسجيل كاملًا قبل التقييم"));
  await waitFor(() => expect(retryButton).toBeEnabled());
  fireEvent.click(retryButton);
  const send = within(dialog).getByRole("button",{name:"إرسال طلب الإعادة"});
  expect(send).toBeDisabled();
  fireEvent.change(within(dialog).getByLabelText("ماذا يحتاج الطالب أن يعيد؟"),{target:{value:"أعد قراءة الكلمة بصوت أوضح"}});
  fireEvent.click(send);
  expect(await screen.findByText("أُرسل طلب إعادة التسجيل إلى الطالب.")).toBeVisible();
  expect(fetcher).toHaveBeenCalledWith("/api/v2/retries/admin/lesson/21/request",expect.objectContaining({method:"POST",body:JSON.stringify({reason:"أعد قراءة الكلمة بصوت أوضح"})}));
  expect(fetcher.mock.calls.every(([path])=>!path.endsWith("decision"))).toBe(true);
});

it("keeps a failed save open and validates optional numeric values only when selected", async () => {
  failSave=true;
  const dialog=await open();
  fireEvent.ended(within(dialog).getByLabelText("استمع للتسجيل كاملًا قبل التقييم"));
  const accept=within(dialog).getByRole("button",{name:"القراءة صحيحة"});
  await waitFor(()=>expect(accept).toBeEnabled());
  fireEvent.click(within(dialog).getByRole("checkbox"));
  expect(accept).toBeDisabled();
  fireEvent.change(within(dialog).getByRole("spinbutton",{name:"عدد الوحدات المطلوبة"}),{target:{value:"3"}});
  fireEvent.click(accept);
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("تغير التسجيل؛ حدّث القائمة");
  expect(screen.getByRole("dialog")).toBeVisible();
  expect(JSON.parse(fetcher.mock.calls.find(([path])=>path.endsWith("/review"))![1].body).rubric.target_units).toBe(3);
});

it("closes without a decision and restores page scrolling", async () => {
  const dialog=await open();
  expect(document.body.style.overflow).toBe("hidden");
  fireEvent.click(within(dialog).getByRole("button",{name:"إغلاق المراجعة"}));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(document.body.style.overflow).not.toBe("hidden");
  expect(fetcher.mock.calls.every(([,options])=>options?.method!=="POST")).toBe(true);
});

it("mobile review cards expose a label for every value including date and action", async () => {
  render(<V2AudioReviewQueue kind="assessment" />);
  const table = await screen.findByRole("table", { name: "تسجيلات تحتاج مراجعة" });
  const labels = within(table).getAllByRole("cell").map(cell => cell.getAttribute("data-label"));
  expect(labels).toEqual(["الطالب", "النشاط", "المطلوب", "تاريخ التسجيل", "الحالة", "الإجراء"]);
});

it("shows requested rerecords as waiting for learner, not as actionable reviews", async () => {
  global.fetch = jest.fn(async () => ok({items:[{...item,retry_state:"requested"}],next_offset:null}));
  render(<V2AudioReviewQueue kind="assessment"/>);
  expect(await screen.findByText(/0 جاهز للمراجعة · 1 بانتظار إعادة الطالب/)).toBeInTheDocument();
  expect(screen.getByRole("button",{name:/مراجعة تسجيل طالب اصطناعي/})).toBeDisabled();
});
