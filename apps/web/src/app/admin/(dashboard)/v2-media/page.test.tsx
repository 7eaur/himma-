import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import V2MediaInventoryPage from "./page";

jest.mock("@/components/admin/EducationalMediaPreview", () =>
  function MockMedia() { return <div aria-label="معاينة اختبارية"/>; });

const items = Array.from({length: 25}, (_, index) => ({
  asset_id: `MEDIA-${String(index + 1).padStart(2, "0")}`, kind: "image",
  state: "ready", runtime_state: "ready", test_only: false, temporary: false,
  source_status: "ready", candidate_present: true,
  preview_url: null, preview_kind: "image", publication_blocker: false,
  uses: [{owner_id: "L1-01", role: "example"}],
}));
const inventory = {
  mode: "read_only", release_state: "candidate", items,
  counts: {ready: 25, pending: 0, missing: 0, test_only: 0, temporary: 0},
  candidate_files_present: 25, published_assets: 25, required_assets: 25, publishable: true,
};

test("paginates media on mobile-friendly 12-card pages without dropping V2 source metadata", async () => {
  global.fetch = jest.fn().mockResolvedValue({ok: true, json: async () => inventory});
  render(<V2MediaInventoryPage />);
  await waitFor(() => expect(screen.getAllByTestId("v2-media-card")).toHaveLength(12));
  expect(screen.getByText("MEDIA-01")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name: "التالي"}));
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(12);
  expect(screen.getByText("MEDIA-13")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name: "التالي"}));
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(1);
  expect(screen.getByText("MEDIA-25")).toBeInTheDocument();
  expect(screen.getByText(/الأصول المطلوبة المتاحة لهذا الإصدار: 25 من 25/)).toBeInTheDocument();
  fireEvent.change(screen.getByRole("textbox", {name: "بحث عن وسيط أو درس أو نوع الملف"}),
    {target: {value: "MEDIA-02"}});
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(1);
  expect(screen.getByText("MEDIA-02")).toBeInTheDocument();
});

test("keeps owner-approved shared lesson videos visible and filterable", async () => {
  global.fetch = jest.fn().mockResolvedValue({ok: true, json: async () => ({
    ...inventory, counts: {...inventory.counts, temporary: 1},
    items: [{...items[0], kind: "video", temporary: true, asset_id: "VID-L1-01"}, items[1]],
    published_assets: 2, required_assets: 2,
  })});
  render(<V2MediaInventoryPage />);
  await waitFor(() => expect(screen.getByText("VID-L1-01")).toBeInTheDocument());
  expect(screen.getByText(/منها 1 فيديو مشترك مُدرج للإصدار الأولي/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name: "الفيديو المشترك"}));
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(1);
  expect(screen.getByText(/فيديو مشترك بين الدروس في الإصدار الأولي/)).toBeInTheDocument();
});

test("offers a clear reset for empty filters rather than suggesting missing content", async () => {
  global.fetch = jest.fn().mockResolvedValue({ok: true, json: async () => inventory});
  render(<V2MediaInventoryPage />);
  await waitFor(() => expect(screen.getAllByTestId("v2-media-card")).toHaveLength(12));
  fireEvent.change(screen.getByRole("textbox", {name: "بحث عن وسيط أو درس أو نوع الملف"}), {target: {value: "لا يوجد ملف بهذا الاسم"}});
  expect(screen.getByText("لا توجد وسائط مطابقة للبحث")).toBeVisible();
  fireEvent.click(screen.getByRole("button", {name: "مسح البحث والتصفية"}));
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(12);
  expect(screen.getByRole("textbox", {name: "بحث عن وسيط أو درس أو نوع الملف"})).toHaveValue("");
});

test("searches by friendly media type while preserving the file identifier for staff", async () => {
  global.fetch = jest.fn().mockResolvedValue({ok: true, json: async () => ({
    ...inventory, items: [
      {...items[0], kind: "audio", asset_id: "AUDIO-1"},
      {...items[1], kind: "image", asset_id: "IMAGE-2"},
    ],
  })});
  render(<V2MediaInventoryPage />);
  await waitFor(() => expect(screen.getAllByTestId("v2-media-card")).toHaveLength(2));
  fireEvent.change(screen.getByRole("textbox", {name: "بحث عن وسيط أو درس أو نوع الملف"}), {target: {value: "صوت"}});
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(1);
  expect(screen.getByRole("heading", {name: "مقطع صوتي"})).toBeVisible();
  expect(screen.getByText("AUDIO-1")).toBeInTheDocument();
});
