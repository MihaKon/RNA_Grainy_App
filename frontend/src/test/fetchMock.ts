import { vi } from "vitest";

export interface MockedRequest {
  url: string;
  init: RequestInit | undefined;
}

type RouteHandler = (request: MockedRequest) => Response | Promise<Response>;

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function mockFetch(routes: Record<string, RouteHandler>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url =
      typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const route = `${init?.method ?? "GET"} ${url}`;
    const handler = routes[route];
    if (!handler) {
      return Promise.reject(new Error(`Unexpected request: ${route}`));
    }
    return Promise.resolve(handler({ url, init }));
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function requestBody(
  fetchMock: ReturnType<typeof mockFetch>,
  url: string,
  method = "POST",
): FormData {
  const call = fetchMock.mock.calls.find(
    ([input, init]) => input === url && (init?.method ?? "GET") === method,
  );
  const body = call?.[1]?.body;
  if (!(body instanceof FormData)) {
    throw new Error(`Expected a ${method} ${url} request with a FormData body.`);
  }
  return body;
}
