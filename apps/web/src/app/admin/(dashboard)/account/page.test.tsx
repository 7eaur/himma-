import fs from "node:fs";
import path from "node:path";

const redirectMock = jest.fn();

jest.mock("next/navigation", () => ({
  redirect: (destination: string) => redirectMock(destination),
}));

import AccountPage from "./page";


describe("retired admin account route", () => {
  beforeEach(() => redirectMock.mockClear());

  it("redirects old bookmarks to the canonical Settings owner", () => {
    AccountPage();
    expect(redirectMock).toHaveBeenCalledTimes(1);
    expect(redirectMock).toHaveBeenCalledWith("/admin/settings");
  });

  it("has no live dashboard backlink to the retired account route", () => {
    const layoutPath = path.join(
      process.cwd(),
      "src/app/admin/(dashboard)/layout.tsx",
    );
    const layoutSource = fs.readFileSync(layoutPath, "utf8");

    expect(layoutSource).toContain('href: "/admin/settings"');
    expect(layoutSource).not.toContain('href: "/admin/account"');
  });
});
