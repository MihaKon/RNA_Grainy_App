import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "@fontsource/bebas-neue";
import "@fontsource-variable/newsreader/wght-italic.css";
import "@/styles/index.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";

import { AppProviders } from "@/app/AppProviders";
import { createQueryClient } from "@/app/queryClient";
import { routes } from "@/app/routes";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found.");
}

const router = createBrowserRouter(routes);
const queryClient = createQueryClient();

createRoot(rootElement).render(
  <StrictMode>
    <AppProviders queryClient={queryClient}>
      <RouterProvider router={router} />
    </AppProviders>
  </StrictMode>,
);
