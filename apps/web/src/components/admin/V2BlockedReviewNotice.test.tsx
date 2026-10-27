import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import V2BlockedReviewNotice from "./V2BlockedReviewNotice";

it("keeps blocked evidence visible on a failed restore and refreshes only after a successful insert", async () => {
  const restored = jest.fn().mockResolvedValue(undefined);
  const fetcher = jest.fn()
    .mockResolvedValueOnce({ ok: false, json: async () => ({ detail: "البصمة لا تطابق" }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ status: "restored" }) });
  global.fetch = fetcher;
  render(<V2BlockedReviewNotice onRestored={restored} items={[{
    response_id: 6, session_id: 1, student_id: 1, student_name: "اصطناعي",
    reason: "content_release_unavailable", detail: "نسخة غير متاحة", content_release_id: 1,
    release_version: "historical", release_checksum: "b".repeat(64), recoverable: true,
  }]} />);
  fireEvent.click(screen.getByText("جلسة #1 · إجابة #6"));
  fireEvent.click(screen.getByRole("button", { name: "استعادة النسخة الأصلية المطابقة" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("البصمة لا تطابق");
  expect(restored).not.toHaveBeenCalled();
  expect(screen.getByTestId("v2-blocked-reviews")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "استعادة النسخة الأصلية المطابقة" }));
  await waitFor(() => expect(restored).toHaveBeenCalledTimes(1));
  expect(fetcher.mock.calls.every(([url, options]) => url === "/api/v2/content/admin/releases/1/restore-original-snapshot" && options.method === "POST")).toBe(true);
});
