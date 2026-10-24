import type { RouteObject } from "react-router";

import { Layout } from "@/components/layout/Layout";
import { AboutPage } from "@/pages/AboutPage";
import { DocumentationPage } from "@/pages/DocumentationPage";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { ResultPage } from "@/pages/ResultPage";

export const routes: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "documentation", element: <DocumentationPage /> },
      { path: "about", element: <AboutPage /> },
      { path: "results/:workspaceId", element: <ResultPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
