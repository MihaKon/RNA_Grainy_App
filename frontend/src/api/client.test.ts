import { describe, expect, it } from "vitest";

import { jsonResponse, mockFetch } from "@/test/fetchMock";

import { ApiError, apiRequest, getErrorMessage } from "./client";

describe("apiRequest", () => {
  it("returns the parsed JSON body", async () => {
    const fetchMock = mockFetch({
      "GET /api/config": () => jsonResponse({ ok: true }),
    });

    await expect(apiRequest("/api/config")).resolves.toEqual({ ok: true });
    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Accept")).toBe("application/json");
  });

  it("throws an ApiError with the server detail", async () => {
    mockFetch({
      "GET /api/config": () => jsonResponse({ detail: "Invalid example ID." }, 422),
    });

    await expect(apiRequest("/api/config")).rejects.toEqual(
      new ApiError("Invalid example ID.", 422),
    );
  });

  it("falls back to a generic message for non-JSON errors", async () => {
    mockFetch({
      "GET /api/config": () => new Response("Internal error", { status: 500 }),
    });

    const error: unknown = await apiRequest("/api/config").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(getErrorMessage(error)).toBe("Something went wrong. Please try again.");
  });

  it("reports an unreachable backend behind the proxy", async () => {
    mockFetch({ "GET /api/config": () => new Response("", { status: 502 }) });

    await expect(apiRequest("/api/config")).rejects.toEqual(
      new ApiError(
        "The server is currently unavailable. Please try again in a moment.",
        502,
      ),
    );
  });

  it("reports network failures", async () => {
    mockFetch({});

    await expect(apiRequest("/api/config")).rejects.toEqual(
      new ApiError(
        "The server is currently unavailable. Please try again in a moment.",
        0,
      ),
    );
  });
});
