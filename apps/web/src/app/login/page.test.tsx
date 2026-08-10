import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "./page";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

beforeEach(() => {
  mockFetch.mockReset();
  mockPush.mockReset();
});

describe("Login page", () => {
  it("renders the login heading", () => {
    render(<LoginPage />);
    expect(screen.getByText("تسجيل الدخول")).toBeInTheDocument();
  });

  it("shows researcher form by default", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText("اسم المستخدم")).toBeInTheDocument();
    expect(screen.getByLabelText("كلمة المرور")).toBeInTheDocument();
  });

  it("switches to student form when tab clicked", () => {
    render(<LoginPage />);
    fireEvent.click(screen.getByTestId("tab-student"));
    expect(screen.getByLabelText("رمز الدخول")).toBeInTheDocument();
  });

  it("shows error on invalid researcher credentials", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText("اسم المستخدم"), {
      target: { value: "bad" },
    });
    fireEvent.change(screen.getByLabelText("كلمة المرور"), {
      target: { value: "wrong" },
    });
    fireEvent.click(screen.getByTestId("login-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("error-message")).toHaveTextContent(
        "بيانات الدخول غير صحيحة"
      );
    });
  });

  it("redirects researcher on successful login", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText("اسم المستخدم"), {
      target: { value: "admin" },
    });
    fireEvent.change(screen.getByLabelText("كلمة المرور"), {
      target: { value: "pass" },
    });
    fireEvent.click(screen.getByTestId("login-submit"));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/researcher");
    });
  });

  it("shows error on invalid student code", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    render(<LoginPage />);
    fireEvent.click(screen.getByTestId("tab-student"));
    fireEvent.change(screen.getByLabelText("رمز الدخول"), {
      target: { value: "INVALID" },
    });
    fireEvent.click(screen.getByTestId("login-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("error-message")).toHaveTextContent(
        "رمز الدخول غير صحيح"
      );
    });
  });

  it("redirects student on successful login", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    render(<LoginPage />);
    fireEvent.click(screen.getByTestId("tab-student"));
    fireEvent.change(screen.getByLabelText("رمز الدخول"), {
      target: { value: "STU001" },
    });
    fireEvent.click(screen.getByTestId("login-submit"));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/student");
    });
  });
});
