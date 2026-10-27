import Page from "./page";
const redirect = jest.fn();
jest.mock("next/navigation", () => ({ redirect: (href: string) => redirect(href) }));

it("sends old activity bookmarks to the student's current journey", () => {
  Page();
  expect(redirect).toHaveBeenCalledWith("/student");
});
