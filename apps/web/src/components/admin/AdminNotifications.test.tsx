import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import AdminNotifications from "./AdminNotifications";
const push = jest.fn();
jest.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
const inbox = { source: "himma_v2_attention", unread_count: 1, items: [{ id: "assessment:1", type: "assessment_review", title: "قراءة اصطناعية", message: "معلقة", href: "/admin/v2-assessments", is_read: false, created_at: "2026-10-27T00:00:00Z" }] };
beforeEach(() => push.mockClear());
it("keeps the notification unread and visible when persisting read fails", async () => {
  global.fetch = jest.fn().mockImplementation((_url, options) => Promise.resolve(options?.method === "POST" ? {ok:false} : {ok:true,json:async()=>inbox}));
  render(<AdminNotifications />);
  fireEvent.click(screen.getByRole("button", {name:"الإشعارات"}));
  fireEvent.click(await screen.findByRole("button", {name:/قراءة اصطناعية/}));
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر حفظ حالة القراءة");
  expect(push).not.toHaveBeenCalled();
  expect(screen.getByRole("button", {name:/قراءة اصطناعية/})).toBeVisible();
  expect(screen.getByRole("button", {name:"تحديد الكل كمقروء"})).toBeVisible();
});
it("refreshes only the V2 inbox and keeps Escape focus recovery", async () => {
  const fetcher = jest.fn().mockImplementation(() => Promise.resolve({ok:true,json:async()=>inbox}));
  global.fetch = fetcher;
  render(<AdminNotifications />);
  fireEvent.click(screen.getByRole("button", {name:"الإشعارات"}));
  await screen.findByRole("button", {name:/قراءة اصطناعية/});
  expect(fetcher.mock.calls.every(([url]) => url.startsWith("/api/v2/notifications"))).toBe(true);
  fireEvent.click(screen.getByRole("button", {name:"تحديث"}));
  await waitFor(() => expect(fetcher.mock.calls.length).toBeGreaterThan(1));
  expect(fetcher.mock.calls.every(([url]) => url === "/api/v2/notifications?limit=24")).toBe(true);
  expect(screen.queryByText("أرشيف إشعارات V1")).not.toBeInTheDocument();
  fireEvent.keyDown(document, {key:"Escape"});
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.getByRole("button", {name:"الإشعارات"})).toHaveFocus();
});
it("navigates only after the read marker is saved and refreshes the durable inbox", async () => {
  let read = false;
  global.fetch = jest.fn().mockImplementation((_url, options) => {
    if (options?.method === "POST") { read = true; return Promise.resolve({ok:true}); }
    return Promise.resolve({ok:true,json:async()=> read ? {...inbox,unread_count:0,items:[{...inbox.items[0],is_read:true}]} : inbox});
  });
  render(<AdminNotifications />);
  fireEvent.click(screen.getByRole("button", {name:"الإشعارات"}));
  fireEvent.click(await screen.findByRole("button", {name:/قراءة اصطناعية/}));
  await waitFor(() => expect(push).toHaveBeenCalledWith("/admin/v2-assessments"));
});
it("shows unavailable instead of an empty inbox when the source fails", async () => {
  global.fetch = jest.fn().mockResolvedValue({ok:false,json:async()=>({})});
  render(<AdminNotifications />);
  fireEvent.click(screen.getByRole("button", {name:"الإشعارات"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل الإشعارات");
  expect(screen.queryByText("لا توجد إشعارات تحتاج انتباهك الآن.")).not.toBeInTheDocument();
});
