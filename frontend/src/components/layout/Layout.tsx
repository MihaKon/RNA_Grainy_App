import { type Location, Outlet, ScrollRestoration } from "react-router";

import { CivicStripe } from "./CivicStripe";
import { Footer } from "./Footer";
import { Header } from "./Header";

export function Layout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <div className="sticky top-0 z-40">
        <Header />
        <CivicStripe />
      </div>
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <ScrollRestoration getKey={getScrollKey} />
    </div>
  );
}

// Every full page load starts with the "default" key, so key it by path instead;
// otherwise one page would restore the scroll position saved for another.
function getScrollKey(location: Location): string {
  return location.key === "default" ? location.pathname : location.key;
}
