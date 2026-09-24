import { type Location, Outlet, ScrollRestoration } from "react-router";

import { CivicStripe } from "./CivicStripe";
import { Colonnade } from "./Colonnade";
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
      <Colonnade />
      <Footer />
      <ScrollRestoration getKey={getScrollKey} />
    </div>
  );
}

function getScrollKey(location: Location): string {
  return location.key === "default" ? location.pathname : location.key;
}
