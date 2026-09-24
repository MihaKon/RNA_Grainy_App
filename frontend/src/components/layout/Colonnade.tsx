import colonnadeUrl from "@/assets/brand/colonnade.svg";

import { CivicStripe } from "./CivicStripe";

export function Colonnade() {
  return (
    <div aria-hidden="true" className="mt-8">
      <img
        src={colonnadeUrl}
        alt=""
        width={1099}
        height={147}
        className="mx-auto block w-72 lg:w-[26rem]"
      />
      <CivicStripe />
    </div>
  );
}
