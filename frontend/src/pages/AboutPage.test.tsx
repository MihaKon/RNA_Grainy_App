import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { renderApp } from "@/test/renderApp";

describe("AboutPage", () => {
  it("lists the authors with their roles and affiliations", () => {
    renderApp("/about");

    const authors = within(screen.getByRole("region", { name: "Authors" }));
    expect(authors.getByRole("link", { name: /Marta Szachniuk/ })).toHaveAttribute(
      "href",
      "https://www.cs.put.poznan.pl/mszachniuk/site/",
    );
    expect(authors.getAllByText("Development")).toHaveLength(2);
    expect(authors.getByText("Scientific supervision")).toBeInTheDocument();
    expect(
      authors.getByText(
        /Institute of Bioorganic Chemistry, Polish Academy of Sciences/,
      ),
    ).toBeInTheDocument();
  });
});
