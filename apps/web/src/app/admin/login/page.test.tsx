import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import AdminLogin from "./page";

const mockReplace = jest.fn();
const mockRefresh = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace, refresh: mockRefresh }),
}));

beforeEach(() => {
  mockReplace.mockClear();
  mockRefresh.mockClear();
});

it("allows a valid supervisor to log in only after server acknowledgement", async () => {
  const fetcher = jest.fn(async (url: string) => ({
    ok: true,
    json: async () => url === "/api/auth/me" ? {role: "student"} : {role: "researcher"},
  }));
  global.fetch = fetcher as unknown as typeof fetch;
  render(<AdminLogin />);
  fireEvent.change(screen.getByLabelText("اسم المستخدم"), {target:{value:"staff"}});
  fireEvent.change(screen.getByLabelText("كلمة المرور"), {target:{value:"test-pass"}});
  fireEvent.click(screen.getByRole("button",{name:"دخول لوحة المشرف"}));
  await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/admin"));
  expect(fetcher.mock.calls.some(([url]) => url === "/api/auth/login")).toBe(true);
  expect(mockRefresh).toHaveBeenCalled();
});

it("prevents duplicate login requests on immediate double submission", async () => {
  let resolveLogin!: (value: unknown) => void;
  const pending = new Promise(resolve => {resolveLogin = resolve;});
  const fetcher = jest.fn((url: string) => url === "/api/auth/me"
    ? Promise.resolve({ok: true, json: async()=>({role:"student"})})
    : pending);
  global.fetch = fetcher as unknown as typeof fetch;
  render(<AdminLogin />);
  fireEvent.change(screen.getByLabelText("اسم المستخدم"), {target:{value:"staff"}});
  fireEvent.change(screen.getByLabelText("كلمة المرور"), {target:{value:"test-pass"}});
  const form = screen.getByRole("button",{name:"دخول لوحة المشرف"}).closest("form")!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(fetcher.mock.calls.filter(([url])=>url === "/api/auth/login")).toHaveLength(1);
  resolveLogin({ok: true, json: async()=>({role:"researcher"})});
  await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/admin"));
});

it("shows a safe Arabic message when the server returns a validation object", async () => {
  const fetcher = jest.fn(async (url: string) => url === "/api/auth/me"
    ? {ok:false,json:async()=>null}
    : {ok:false,json:async()=>({detail:[{loc:["body","username"], msg:"required"}]})});
  global.fetch = fetcher as unknown as typeof fetch;
  render(<AdminLogin />);
  fireEvent.change(screen.getByLabelText("اسم المستخدم"), {target:{value:"staff"}});
  fireEvent.change(screen.getByLabelText("كلمة المرور"), {target:{value:"not-right"}});
  fireEvent.click(screen.getByRole("button",{name:"دخول لوحة المشرف"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تسجيل الدخول");
  expect(mockReplace).not.toHaveBeenCalled();
});

it("explains invalid supervisor credentials without exposing backend diagnostic text", async () => {
  const fetcher = jest.fn(async (url:string) => url === "/api/auth/me"
    ? {ok:false,status:401,json:async()=>null}
    : {ok:false,status:401,json:async()=>({detail:"Database Error: credentials invalid"})});
  global.fetch = fetcher as unknown as typeof fetch;
  render(<AdminLogin />);
  fireEvent.change(screen.getByLabelText("اسم المستخدم"), {target:{value:"staff"}});
  fireEvent.change(screen.getByLabelText("كلمة المرور"), {target:{value:"wrong"}});
  fireEvent.click(screen.getByRole("button", {name:"دخول لوحة المشرف"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("اسم المستخدم أو كلمة المرور غير صحيحة.");
  expect(screen.queryByText(/Database Error/)).not.toBeInTheDocument();
  expect(mockReplace).not.toHaveBeenCalled();
});
