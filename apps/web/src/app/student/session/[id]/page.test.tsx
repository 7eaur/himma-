import Page from "./page";
const redirect = jest.fn();
jest.mock("next/navigation", () => ({ redirect: (href: string) => redirect(href) }));

it("does not reuse a historical session ID as a current assessment", () => {
  Page();
  expect(redirect).toHaveBeenCalledWith("/student");
});
