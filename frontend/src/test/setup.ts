import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// jsdom does not implement scrolling, which React Router's ScrollRestoration relies on.
window.scrollTo = () => undefined;

afterEach(() => {
  cleanup();
});
