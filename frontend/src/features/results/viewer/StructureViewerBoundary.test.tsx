import { render, screen } from "@testing-library/react";
import { lazy, Suspense } from "react";
import { expect, it, vi } from "vitest";

import { StructureViewerBoundary } from "./StructureViewerBoundary";

it("contains a rejected viewer import and offers a page reload", async () => {
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  const FailedViewer = lazy(() =>
    Promise.reject(new TypeError("Failed to fetch dynamically imported module")),
  );

  render(
    <StructureViewerBoundary>
      <Suspense fallback={<p>Loading viewer</p>}>
        <FailedViewer />
      </Suspense>
    </StructureViewerBoundary>,
  );

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("The structure viewer could not be loaded.");
  expect(alert).toHaveTextContent("You can still download the CG model above.");
  expect(screen.getByRole("button", { name: "Reload page" })).toBeEnabled();
  expect(
    screen.queryByText("Failed to fetch dynamically imported module"),
  ).not.toBeInTheDocument();
});
