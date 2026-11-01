import { fireEvent, render, screen } from "@testing-library/react";
import EducationalMediaPreview from "./EducationalMediaPreview";

it("loads audio only on demand, retries failures, and never substitutes a different asset", () => {
  const asset = { asset_id: "AUD-TEST", kind: "audio", url: "/api/v2/lessons/admin/media/AUD-TEST", test_only: true };
  render(<EducationalMediaPreview asset={asset} />);
  expect(document.querySelector("audio")).toBeNull();
  expect(screen.getByText(/ملف للمعاينة فقط/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "معاينة الصوت للوسيط AUD-TEST" }));
  const audio = document.querySelector("audio")!;
  expect(audio).toHaveAttribute("src", asset.url);
  expect(audio).toHaveAttribute("preload", "none");
  fireEvent.error(audio);
  expect(screen.getByRole("alert")).toHaveTextContent("تعذر تشغيل الملف");
  expect(document.querySelector("audio")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" }));
  const retriedAudio = document.querySelector("audio")!;
  expect(retriedAudio).toHaveAttribute("src", asset.url);
  expect(retriedAudio).not.toBe(audio);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("does not display a playback action when a media file is missing", () => {
  render(<EducationalMediaPreview asset={{ asset_id: "MISSING", kind: "video", url: null, test_only: false }} />);
  expect(screen.getByText("ملف المعاينة غير متاح.")).toBeVisible();
  expect(screen.queryByRole("button", { name: /معاينة/ })).not.toBeInTheDocument();
});
