import { render, screen } from "@testing-library/react";
import Home from "./page";

describe("Home page", () => {
  it("renders the welcome heading", () => {
    render(<Home />);
    expect(
      screen.getByText("مرحباً بكم في منصة هِمّة التعليمية")
    ).toBeInTheDocument();
  });

  it("renders the subtitle", () => {
    render(<Home />);
    expect(
      screen.getByText("النسخة الإنتاجية - النواة والأمن")
    ).toBeInTheDocument();
  });
});
