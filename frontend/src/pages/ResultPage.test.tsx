import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { CoarseGrainResult } from "@/api/types";
import { jsonResponse, mockFetch } from "@/test/fetchMock";
import { coarseGrainResult } from "@/test/fixtures";
import { renderApp } from "@/test/renderApp";

vi.mock("@/features/results/ResultView", () => ({
  ResultView: ({ result }: { result: CoarseGrainResult }) => (
    <>
      <h1>{result.filename}</h1>
      <p>CG model: {result.model.name}</p>
    </>
  ),
}));

const path = `/results/${coarseGrainResult.workspace_id}`;
const metadataUrl = `/api/results/${coarseGrainResult.workspace_id}`;

describe("ResultPage", () => {
  it("loads an API-created result from a direct link without navigation state", async () => {
    const fetchMock = mockFetch({
      [`GET ${metadataUrl}`]: () => jsonResponse(coarseGrainResult),
    });

    renderApp(`${path}/`);

    expect(await screen.findByRole("heading", { name: "1EHZ" })).toBeVisible();
    expect(screen.getByText("CG model: SimRNA")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(metadataUrl);
  });

  it("uses the conversion response immediately when navigation state is available", () => {
    const fetchMock = mockFetch({});

    renderApp({ pathname: path, state: { result: coarseGrainResult } });

    expect(screen.getByRole("heading", { name: "1EHZ" })).toBeVisible();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows a loading state until metadata arrives", async () => {
    let finish!: (response: Response) => void;
    mockFetch({
      [`GET ${metadataUrl}`]: () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    });
    renderApp(path);

    expect(screen.getByRole("status")).toHaveTextContent("Loading conversion summary");
    expect(screen.queryByText("Result not available")).not.toBeInTheDocument();
    finish(jsonResponse(coarseGrainResult));

    expect(await screen.findByRole("heading", { name: "1EHZ" })).toBeVisible();
  });

  it("fetches the requested result instead of displaying a different result from state", async () => {
    const otherId = "594887c0-d7cf-4f93-98c1-9458d58a0cea";
    mockFetch({
      [`GET /api/results/${otherId}`]: () =>
        jsonResponse({
          ...coarseGrainResult,
          workspace_id: otherId,
          filename: "Another structure",
        }),
    });

    renderApp({
      pathname: `/results/${otherId}`,
      state: { result: coarseGrainResult },
    });

    expect(
      await screen.findByRole("heading", { name: "Another structure" }),
    ).toBeVisible();
    expect(screen.queryByRole("heading", { name: "1EHZ" })).not.toBeInTheDocument();
  });

  it.each([404, 422])("explains an unavailable result for HTTP %s", async (status) => {
    mockFetch({
      [`GET ${metadataUrl}`]: () =>
        jsonResponse({ detail: "Result unavailable." }, status),
    });
    renderApp(path);

    expect(
      await screen.findByRole("heading", { name: "Result not available" }),
    ).toBeVisible();
    expect(screen.getByText(/does not exist or is no longer available/)).toBeVisible();
    expect(screen.queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Process another structure/ }),
    ).toHaveAttribute("href", "/");
  });

  it.each(["network", "server"])("can retry after a %s failure", async (failure) => {
    let attempts = 0;
    mockFetch({
      [`GET ${metadataUrl}`]: () => {
        attempts += 1;
        if (attempts > 1) return jsonResponse(coarseGrainResult);
        return failure === "network"
          ? Promise.reject(new TypeError("Failed to fetch"))
          : jsonResponse({}, 503);
      },
    });
    const { user } = renderApp(path);

    expect(
      await screen.findByRole("heading", { name: "Could not load result" }),
    ).toBeVisible();
    expect(screen.getByText(/server is currently unavailable/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "1EHZ" })).toBeVisible();
    expect(attempts).toBe(2);
  });
});
