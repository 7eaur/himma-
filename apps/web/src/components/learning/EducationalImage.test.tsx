import { act, fireEvent, render, screen } from "@testing-library/react";
import EducationalImage from "./EducationalImage";

describe("EducationalImage", () => {
  it("reserves the image and replaces its neutral placeholder only after loading", async () => {
    const loaded = jest.fn();
    render(<EducationalImage src="/question.webp?v=1" alt="صورة السؤال" width={300} height={220} onLoad={loaded} onError={jest.fn()}/>);
    expect(screen.getByRole("status", { name: "جاري تحميل الصورة" })).toBeInTheDocument();
    const img = screen.getByAltText("صورة السؤال");
    expect(img).toHaveAttribute("loading", "eager");
    expect(img).toHaveStyle({ opacity: "0" });
    await act(async () => { fireEvent.load(img); });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(img).toHaveStyle({ opacity: "1" });
    expect(loaded).toHaveBeenCalledTimes(1);
  });

  it("reports failed images without claiming they loaded", () => {
    const failed = jest.fn(); const loaded = jest.fn();
    render(<EducationalImage src="/broken.webp" alt="صورة خيار" width={300} height={220} onLoad={loaded} onError={failed}/>);
    fireEvent.error(screen.getByAltText("صورة خيار"));
    expect(failed).toHaveBeenCalledTimes(1);
    expect(loaded).not.toHaveBeenCalled();
  });
});
