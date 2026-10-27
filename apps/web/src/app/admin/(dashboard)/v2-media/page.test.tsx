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
  fireEvent.change(screen.getByRole("textbox", {name: "بحث بمعرّف الوسيط أو الدرس"}),
    {target: {value: "MEDIA-02"}});
  expect(screen.getAllByTestId("v2-media-card")).toHaveLength(1);
  expect(screen.getByText("MEDIA-02")).toBeInTheDocument();
});
