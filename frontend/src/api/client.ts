export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const FALLBACK_ERROR_MESSAGE = "Something went wrong. Please try again.";
const SERVER_UNAVAILABLE_MESSAGE =
  "The server is currently unavailable. Please try again in a moment.";
const SERVER_UNAVAILABLE_STATUSES = new Set([502, 503, 504]);

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");

  let response: Response;
  try {
    response = await fetch(path, { ...init, headers });
  } catch {
    throw new ApiError(SERVER_UNAVAILABLE_MESSAGE, 0);
  }

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response), response.status);
  }

  return (await response.json()) as T;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof body.detail === "string"
    ) {
      return body.detail;
    }
  } catch {
    // Non-JSON error bodies (e.g. proxy errors) fall through to the generic messages.
  }
  return SERVER_UNAVAILABLE_STATUSES.has(response.status)
    ? SERVER_UNAVAILABLE_MESSAGE
    : FALLBACK_ERROR_MESSAGE;
}

export function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : FALLBACK_ERROR_MESSAGE;
}
