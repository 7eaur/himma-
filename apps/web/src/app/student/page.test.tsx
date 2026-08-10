import { render, screen } from "@testing-library/react";
import StudentPage from "./page";

describe("Student page", () => {
  it("renders the student page heading", () => {
    render(<StudentPage />);
    expect(screen.getByText("صفحة الطالب")).toBeInTheDocument();
  });

  it("is a protected route (placeholder content present)", () => {
    render(<StudentPage />);
    expect(
      screen.getByText("مرحبًا بك في صفحتك الشخصية.")
    ).toBeInTheDocument();
  });
});
