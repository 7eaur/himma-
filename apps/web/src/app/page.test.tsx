import { render, screen } from "@testing-library/react";
import Home from "./page";

describe("Home page", () => {
  it("renders the approved welcome heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /نتعلّم بهدوء/ })).toBeInTheDocument();
  });

  it("offers student login", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: /دخول الطالب/ })).toHaveAttribute("href", "/student/login");
  });
});
