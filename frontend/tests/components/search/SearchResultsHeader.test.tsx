import { axe } from "jest-axe";
import { render, screen } from "tests/react-utils";

import React from "react";

import SearchResultsHeader from "src/components/search/SearchResultsHeader";

jest.mock("src/components/search/SearchSortBy", () => {
  return {
    __esModule: true,
    default: () => <div>Mock SearchSortBy</div>,
  };
});

describe("SearchResultsHeader", () => {
  it("should not have basic accessibility issues", async () => {
    const { container } = render(
      <SearchResultsHeader totalFetchedResults={"100"} sortby="" />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("renders correctly and displays the number of opportunities", () => {
    render(<SearchResultsHeader sortby="" totalFetchedResults={"100"} />);

    expect(screen.getByText("100 Opportunities")).toBeInTheDocument();
    expect(screen.getByText("Mock SearchSortBy")).toBeInTheDocument();
  });
});
