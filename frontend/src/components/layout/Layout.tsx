import { Outlet, ScrollRestoration } from "react-router";

import { CivicStripe } from "./CivicStripe";
import { Footer } from "./Footer";
import { SiteHeader } from "./SiteHeader";

export function Layout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <div className="sticky top-0 z-40">
        <SiteHeader />
        <CivicStripe />
      </div>
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <ScrollRestoration />
    </div>
  );
}
