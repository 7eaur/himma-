import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import SettingsPage from "./page";

const account = { id: 1, username: "supervisor1", is_active: true, created_at: "2026-10-01T00:00:00Z" };

function defer<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(done => { resolve = done; });
  return { promise, resolve };
}

function mockSettingsFetch(mutate: (url: string, options?: RequestInit) => Promise<unknown>) {
  const fetcher = jest.fn((url: string, options?: RequestInit) => {
    if (!options?.method) {
      if (url === "/api/researcher/account") return Promise.resolve({ ok: true, json: async () => account });
      if (url === "/api/researcher/supervisors") return Promise.resolve({ ok: true, json: async () => [account] });
    }
    return mutate(url, options);
  });
  global.fetch = fetcher as unknown as typeof fetch;
  return fetcher;
}

it("creates a supervisor only once when the form is submitted twice before React renders", async () => {
  const pending = defer<unknown>();
  const fetcher = mockSettingsFetch(() => pending.promise);
  render(<SettingsPage />);
  fireEvent.click(await screen.findByRole("tab", { name: "المشرفون" }));
  fireEvent.change(screen.getByLabelText("اسم المستخدم"), { target: { value: "supervisor2" } });
  fireEvent.change(screen.getByLabelText("كلمة المرور المؤقتة"), { target: { value: "temporaryPass123" } });
  const form = screen.getByRole("button", { name: "إضافة المشرف" }).closest("form")!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(fetcher.mock.calls.filter(([url, options]) => url === "/api/researcher/supervisors" && options?.method === "POST")).toHaveLength(1);
  pending.resolve({ ok: true, json: async () => ({ ...account, id: 2, username: "supervisor2" }) });
  await waitFor(() => expect(screen.getByText("supervisor2")).toBeVisible());
  expect(screen.getByText("تم إنشاء حساب المشرف الجديد.")).toBeVisible();
});

it("does not overlap a profile update with a pending password change from another tab", async () => {
  const pending = defer<unknown>();
  const fetcher = mockSettingsFetch(() => pending.promise);
  render(<SettingsPage />);
  fireEvent.click(await screen.findByRole("tab", { name: "الأمان" }));
  fireEvent.change(screen.getByLabelText("كلمة المرور الحالية"), { target: { value: "currentPass123" } });
  fireEvent.change(screen.getByLabelText("كلمة المرور الجديدة"), { target: { value: "nextPass123" } });
  fireEvent.change(screen.getByLabelText("تأكيد كلمة المرور"), { target: { value: "nextPass123" } });
  fireEvent.submit(screen.getByRole("button", { name: "تغيير كلمة المرور" }).closest("form")!);
  fireEvent.click(screen.getByRole("tab", { name: "الحساب" }));
  fireEvent.change(screen.getByLabelText("اسم المشرف / اسم المستخدم"), { target: { value: "newSupervisorName" } });
  fireEvent.submit(screen.getByRole("button", { name: "حفظ بيانات الحساب" }).closest("form")!);
  expect(fetcher.mock.calls.filter(([url, options]) => url === "/api/researcher/account" && options?.method === "PATCH")).toHaveLength(0);
  expect(fetcher.mock.calls.filter(([url, options]) => url === "/api/researcher/account/password" && options?.method === "POST")).toHaveLength(1);
  pending.resolve({ ok: true, json: async () => ({}) });
  await waitFor(() => expect(screen.getByText("تم تغيير كلمة المرور بنجاح.")).toBeVisible());
});

it("submits a profile change only once under rapid repeat submission", async () => {
  const pending = defer<unknown>();
  const fetcher = mockSettingsFetch(() => pending.promise);
  render(<SettingsPage />);
  const name = await screen.findByLabelText("اسم المشرف / اسم المستخدم");
  await waitFor(() => expect(name).toHaveValue("supervisor1"));
  fireEvent.change(name, { target: { value: "supervisorUpdated" } });
  const form = screen.getByRole("button", { name: "حفظ بيانات الحساب" }).closest("form")!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(fetcher.mock.calls.filter(([url, options]) => url === "/api/researcher/account" && options?.method === "PATCH")).toHaveLength(1);
  pending.resolve({ ok: true, json: async () => ({ ...account, username: "supervisorUpdated" }) });
  await waitFor(() => expect(screen.getByText("تم حفظ بيانات المشرف بنجاح.")).toBeVisible());
});

it("does not present empty supervisor data as real settings after a failed read, and retries safely", async () => {
  let failed = true;
  const fetcher = jest.fn((url: string) => Promise.resolve(
    url === "/api/researcher/account"
      ? failed ? { ok: false } : { ok: true, json: async () => account }
      : { ok: true, json: async () => [account] },
  ));
  global.fetch = fetcher as unknown as typeof fetch;
  render(<SettingsPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل إعدادات الحساب");
  expect(screen.queryByText("0 مشرف")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "إضافة المشرف" })).not.toBeInTheDocument();
  failed = false;
  fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
  expect(await screen.findByRole("tab", { name: "المشرفون" })).toBeVisible();
  expect(await screen.findByDisplayValue("supervisor1")).toBeInTheDocument();
  expect(fetcher.mock.calls.filter(([url]) => url === "/api/researcher/account")).toHaveLength(2);
});
