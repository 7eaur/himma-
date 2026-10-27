import { fireEvent, render, screen } from "@testing-library/react";
import EducationalMediaPreview from "./EducationalMediaPreview";

it("loads a staff audio preview only on demand and never substitutes another asset on failure", () => {
  const asset = { asset_id: "AUD-TEST", kind: "audio", url: "/api/v2/lessons/admin/media/AUD-TEST", test_only: true };
  render(<EducationalMediaPreview asset={asset} />);
  expect(document.querySelector("audio")).toBeNull();
  expect(screen.getByText(/TEST ONLY/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "معاينة AUD-TEST" }));
  const audio = document.querySelector("audio")!;
  expect(audio).toHaveAttribute("src", asset.url);
  expect(audio).toHaveAttribute("preload", "none");
  fireEvent.error(audio);
  expect(screen.getByRole("alert")).toHaveTextContent("لا يُستبدل بملف مختلف");
  expect(document.querySelector("audio")).toBeNull();
});
