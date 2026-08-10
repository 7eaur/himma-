import { render, screen } from "@testing-library/react";
import ResearcherPage from "./page";

describe("Researcher page", () => {
  it("renders the researcher dashboard heading", () => {
    render(<ResearcherPage />);
    expect(screen.getByText("لوحة الباحثة")).toBeInTheDocument();
  });

  it("is a protected route (placeholder content present)", () => {
    render(<ResearcherPage />);
    expect(
      screen.getByText("مرحبًا بك في لوحة تحكم الباحثة.")
    ).toBeInTheDocument();
  });
});
