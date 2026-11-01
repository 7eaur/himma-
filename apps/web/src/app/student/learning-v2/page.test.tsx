import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import V2LearningCatalogPage from "./page";

const mockRouter = { push: jest.fn(), replace: jest.fn() };
jest.mock("next/navigation", () => ({ useRouter: () => mockRouter }));

const lesson = {
  lesson_id: "L1-01", title: "الحروف والأصوات", level: "L1", state: "current",
  preview_enabled: true, session_id: null,
};
const catalog = {
  mode: "candidate_preview", test_only: true, release_version: "v2-release",
  current_action: "lesson", lessons: [
    lesson,
    { lesson_id: "L2-01", title: "تكوين الكلمات", level: "L2", state: "locked", preview_enabled: false, session_id: null },
  ],
};
const response = (body: unknown, status = 200) => ({
  ok: status >= 200 && status < 300, status, json: async () => body,
});
const originalFetch = global.fetch;
beforeEach(() => { jest.clearAllMocks(); });
afterEach(() => { global.fetch = originalFetch; });

it("renders only validated lesson rows and starts the real current lesson", async () => {
  const fetcher = jest.fn(async (url: string) => url.includes("/start")
    ? response({session:{session_id:44}})
    : response(catalog));
  global.fetch = fetcher as unknown as typeof fetch;
  render(<V2LearningCatalogPage />);
  expect(await screen.findByRole("heading", { name: "الحروف والأصوات", level: 2 })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "ابدأ الدرس" }));
  await waitFor(() => expect(mockRouter.push).toHaveBeenCalledWith("/student/learning-v2/44"));
  expect(fetcher).toHaveBeenCalledWith("/api/v2/lessons/L1-01/start", {method:"POST"});
});

it("fails closed on malformed successful catalog and recovers on retry without fake empty levels", async () => {
  const fetcher = jest.fn()
    .mockResolvedValueOnce(response({...catalog, lessons: [null]}))
    .mockResolvedValueOnce(response(catalog));
  global.fetch = fetcher;
  render(<V2LearningCatalogPage />);
  expect(await screen.findByRole("heading", {name:"تعذر عرض دروسك"})).toBeVisible();
  expect(screen.queryByText("0 دروس")).not.toBeInTheDocument();
  expect(screen.queryByText("الحروف والأصوات")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name:"إعادة المحاولة"}));
  expect(await screen.findByRole("heading", {name:"الحروف والأصوات",level:2})).toBeVisible();
  expect(fetcher).toHaveBeenCalledTimes(2);
});

it("rejects forged or empty catalogs rather than displaying a fabricated zero progress", async () => {
  global.fetch = jest.fn(async () => response({...catalog, lessons:[]})) as unknown as typeof fetch;
  render(<V2LearningCatalogPage />);
  expect(await screen.findByRole("heading",{name:"تعذر عرض دروسك"})).toBeVisible();
  expect(screen.queryByText(/0 من 0 درس/)).not.toBeInTheDocument();
});

it("does not reveal backend details on a failed list or a failed lesson start", async () => {
  const fetcher = jest.fn()
    .mockResolvedValueOnce(response(catalog))
    .mockResolvedValueOnce(response({detail:"SQL ERROR: confidential database location"},503));
  global.fetch = fetcher;
  render(<V2LearningCatalogPage />);
  await screen.findByRole("heading",{name:"الحروف والأصوات",level:2});
  fireEvent.click(screen.getByRole("button",{name:"ابدأ الدرس"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر بدء الدرس الآن");
  expect(screen.queryByText(/SQL ERROR/)).not.toBeInTheDocument();
});

it("sanitizes unexpected JavaScript or network exceptions in the student view", async () => {
  global.fetch = jest.fn(async () => { throw new Error("TypeError: internal production SQL connection failed"); }) as unknown as typeof fetch;
  render(<V2LearningCatalogPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر الاتصال بخريطة الدروس");
  expect(screen.queryByText(/production SQL/)).not.toBeInTheDocument();
});

it("does not expose technical API details when the catalog fetch fails", async () => {
  global.fetch = jest.fn(async () => response({detail:"Traceback database SQL secret"},503)) as unknown as typeof fetch;
  render(<V2LearningCatalogPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل دروسك الآن");
  expect(screen.queryByText(/Traceback/)).not.toBeInTheDocument();
});

it("redirects an expired session without showing a false lesson map", async () => {
  global.fetch = jest.fn(async () => response({detail:"expired"},401)) as unknown as typeof fetch;
  render(<V2LearningCatalogPage />);
  await waitFor(() => expect(mockRouter.replace).toHaveBeenCalledWith("/student/login"));
  expect(screen.queryByText("الحروف والأصوات")).not.toBeInTheDocument();
  expect(screen.queryByRole("heading",{name:"تعذر عرض دروسك"})).not.toBeInTheDocument();
});

it("does not follow an untrusted session id in lesson start acknowledgements", async () => {
  const fetcher = jest.fn()
    .mockResolvedValueOnce(response(catalog))
    .mockResolvedValueOnce(response({session:{session_id:"//external"}}));
  global.fetch = fetcher;
  render(<V2LearningCatalogPage />);
  await screen.findByRole("heading",{name:"الحروف والأصوات",level:2});
  fireEvent.click(screen.getByRole("button",{name:"ابدأ الدرس"}));
  expect(await screen.findByRole("alert")).toHaveTextContent("تعذر التحقق من جلسة الدرس");
  expect(mockRouter.push).not.toHaveBeenCalled();
});

it("resumes a server-confirmed existing session without creating another", async () => {
  const fetcher = jest.fn(async () => response({...catalog,lessons:[{...lesson,session_id:21}]}));
  global.fetch = fetcher as unknown as typeof fetch;
  render(<V2LearningCatalogPage />);
  expect(await screen.findByRole("button",{name:"متابعة الدرس"})).toBeVisible();
  fireEvent.click(screen.getByRole("button",{name:"متابعة الدرس"}));
  expect(mockRouter.push).toHaveBeenCalledWith("/student/learning-v2/21");
  expect(fetcher).toHaveBeenCalledTimes(1);
});
