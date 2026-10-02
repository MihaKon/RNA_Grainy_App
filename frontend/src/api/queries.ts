import { queryOptions } from "@tanstack/react-query";

import { apiRequest } from "./client";
import type { AppConfig, ModelDocumentation } from "./types";

export const appConfigQueryOptions = queryOptions({
  queryKey: ["config"],
  queryFn: ({ signal }) => apiRequest<AppConfig>("/api/config", { signal }),
  staleTime: Infinity,
});

export const modelsQueryOptions = queryOptions({
  queryKey: ["models"],
  queryFn: ({ signal }) => apiRequest<ModelDocumentation[]>("/api/models", { signal }),
  staleTime: Infinity,
});
