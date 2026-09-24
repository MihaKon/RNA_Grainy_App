import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { models } from "@/test/fixtures";
import { jsonResponse, mockFetch } from "@/test/fetchMock";
import { renderApp } from "@/test/renderApp";

describe("DocumentationPage", () => {
  it("lists every model with its documentation", async () => {
    mockFetch({ "GET /api/models": () => jsonResponse(models) });
    renderApp("/documentation");

    const nav = await screen.findByRole("navigation", { name: "Models" });
    expect(within(nav).getByRole("link", { name: /SimRNA/ })).toHaveAttribute(
      "href",
      "#SimModel",
    );

    const section = screen.getByRole("region", { name: "SimRNA" });
    expect(within(section).getByText("5 beads per residue")).toBeInTheDocument();
    expect(within(section).getByRole("link", { name: "[1]" })).toHaveAttribute(
      "href",
      "https://doi.org/10.1093/nar/gkv1479",
    );
    expect(within(section).getByRole("img")).toHaveAttribute(
      "src",
      "/static/images/simmodel.png",
    );
    expect(within(section).getByText("Phosphate P atom")).toBeInTheDocument();
  });

  it("offers a retry when the models cannot be loaded", async () => {
    mockFetch({ "GET /api/models": () => jsonResponse({ detail: "Boom" }, 500) });
    renderApp("/documentation");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not load the model documentation.",
    );
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
