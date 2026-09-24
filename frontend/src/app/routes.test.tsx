import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { appConfig, models } from "@/test/fixtures";
import { jsonResponse, mockFetch } from "@/test/fetchMock";
import { renderApp } from "@/test/renderApp";

describe("routes", () => {
  beforeEach(() => {
    mockFetch({
      "GET /api/config": () => jsonResponse(appConfig),
      "GET /api/models": () => jsonResponse(models),
    });
  });

  it("renders the home page inside the app shell", () => {
    renderApp("/");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Coarse-grain RNA 3D structure",
    );
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("navigates between pages and marks the active link", async () => {
    const { user } = renderApp("/");

    const mainNav = screen.getAllByRole("navigation", { name: "Main" })[0];
    if (!mainNav) throw new Error("Main navigation not rendered.");

    const documentationLink = within(mainNav).getByRole("link", {
      name: "Documentation",
    });
    await user.click(documentationLink);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Coarse-grained models",
    );
    expect(documentationLink).toHaveAttribute("aria-current", "page");
  });

  it("explains that a result is unavailable without its data", () => {
    renderApp("/results/unknown-workspace");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Result not available",
    );
  });

  it("renders the not found page for unknown paths", () => {
    renderApp("/does-not-exist");

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Page not found",
    );
  });
});
