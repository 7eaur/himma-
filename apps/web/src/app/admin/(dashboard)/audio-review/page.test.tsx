import Page from "./page";
const redirect = jest.fn();
jest.mock("next/navigation", () => ({ redirect: (href: string) => redirect(href) }));

it("sends old review bookmarks to the current assessment queue", () => {
  Page();
  expect(redirect).toHaveBeenCalledWith("/admin/v2-assessments");
});
