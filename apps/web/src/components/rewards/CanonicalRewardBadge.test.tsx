import { render, screen } from "@testing-library/react";
import CanonicalRewardBadge from "./CanonicalRewardBadge";

describe("CanonicalRewardBadge", () => {
  it("renders the canonical asset and label without a hardcoded badge lookup", () => {
    render(
      <CanonicalRewardBadge
        label="نجم الفهم"
        assetPath="/assets/rewards/svg/hem-bdg-06-comprehension-star.svg"
        rewardKey="level:3:core-complete"
      />,
    );

    expect(screen.getByRole("img", { name: "شارة نجم الفهم" })).toBeInTheDocument();
    expect(screen.getByText("نجم الفهم")).toBeInTheDocument();
    expect(screen.getByTestId("canonical-reward-badge")).toHaveAttribute("data-reward-key", "level:3:core-complete");
  });

  it("supports the compact Admin variant with the same canonical semantics", () => {
    render(
      <CanonicalRewardBadge
        label="مستكشف الحروف"
        assetPath="/assets/rewards/svg/hem-bdg-04-letter-explorer.svg"
        variant="admin"
      />,
    );

    expect(screen.getByRole("img", { name: "شارة مستكشف الحروف" })).toBeInTheDocument();
    expect(screen.getByText("شارة مكتسبة")).toBeInTheDocument();
  });
});
