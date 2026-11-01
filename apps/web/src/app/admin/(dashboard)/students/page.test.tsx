import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import StudentsPage from "./page";

it("distinguishes reading review from automatic placement in the V2 student list", async () => {
  const student = {
    grade_level: 2, created_at: "2026-10-28T00:00:00Z", status: "active",
    journey: null, progress: { completed_lessons: 0, assigned_lessons: null,
      skipped_by_placement: 0, pending_review: 0, display_percent: null },
    data_status: "ready",
  };
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({
    source: "himma_v2_readmodel", total: 2, offset: 0, limit: 30,
    items: [
      { ...student, id: 1, full_name: "طالب قراءة", current_action: { action: "assessment", state: "waiting_review", label: "عرض حالة المراجعة" } },
      { ...student, id: 2, full_name: "طالب تسكين", current_action: { action: "assessment", state: "placement_pending_review", label: "عرض حالة المراجعة" } },
    ],
  }) });
  render(<StudentsPage />);
  expect(await screen.findAllByText("بانتظار مراجعة القراءة")).toHaveLength(2);
  expect(screen.getAllByText("جارٍ تحديد المستوى تلقائيًا")).toHaveLength(2);
  expect(screen.queryByText("بانتظار اعتماد التسكين")).not.toBeInTheDocument();
});

it("debounces name search instead of refetching the whole cohort for every character", async () => {
  const calls = jest.fn(async (_url: string) => ({ok:true,json:async()=>({
    source:"himma_v2_readmodel",total:0,offset:0,limit:30,items:[],
  })}));
  global.fetch = calls as unknown as typeof fetch;
  render(<StudentsPage/>);
  await waitFor(() => expect(calls).toHaveBeenCalledTimes(1));
  const input = screen.getByPlaceholderText("ابحث باسم الطالب");
  fireEvent.change(input,{target:{value:"ط"}});
  fireEvent.change(input,{target:{value:"طال"}});
  fireEvent.change(input,{target:{value:"طالب"}});
  expect(calls).toHaveBeenCalledTimes(1);
  await waitFor(() => expect(calls).toHaveBeenCalledTimes(2));
  expect(String(calls.mock.calls[1][0])).toContain("search=%D8%B7%D8%A7%D9%84%D8%A8");
});

it("offers clearing the active filters instead of suggesting a duplicate new student", async () => {
  const fetcher = jest.fn(async (url: string) => ({
    ok: true,
    json: async () => ({
      source: "himma_v2_readmodel", total: url.includes("search=") && url.includes("search=%D9%84%D8%A7") ? 0 : 1,
      offset: 0, limit: 30, items: url.includes("search=%D9%84%D8%A7") ? [] : [{
        id: 1, full_name: "طالب موجود", status: "active", grade_level: 3,
        created_at: "2026-10-30T00:00:00Z", journey: null,
        progress: { completed_lessons: 0, assigned_lessons: null,
          skipped_by_placement: 0, pending_review: 0, display_percent: null },
        current_action: { action: "assessment", label: "الاختبار القبلي" },
        data_status: "ready",
      }],
    }),
  }));
  global.fetch = fetcher as unknown as typeof fetch;
  render(<StudentsPage />);
  expect(await screen.findAllByText("طالب موجود")).toHaveLength(2);
  fireEvent.change(screen.getByPlaceholderText("ابحث باسم الطالب"), { target: { value: "لا" } });
  expect(await screen.findByText("لا يوجد طلاب يطابقون البحث")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "إضافة أول طالب" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "مسح البحث والتصفية" }));
  expect(screen.getByPlaceholderText("ابحث باسم الطالب")).toHaveValue("");
  await waitFor(() => expect(screen.queryByText("لا يوجد طلاب يطابقون البحث")).not.toBeInTheDocument());
});
