import { type Location, Outlet, ScrollRestoration } from "react-router";

import { CivicStripe } from "./CivicStripe";
import { Colonnade } from "./Colonnade";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export function AppShell() {
  return (
    <div className="flex min-h-dvh flex-col">
      <div className="sticky top-0 z-40">
        <SiteHeader />
        <CivicStripe />
      </div>
      <main className="flex-1">
        <Outlet />
      </main>
      <Colonnade />
      <SiteFooter />
      <ScrollRestoration getKey={getScrollKey} />
    </div>
  );
}

// Every full page load starts with the "default" key, so key it by path instead;
// otherwise one page would restore the scroll position saved for another.
function getScrollKey(location: Location): string {
  return location.key === "default" ? location.pathname : location.key;
}
