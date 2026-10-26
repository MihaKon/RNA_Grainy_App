import { useEffect, useState } from "react";

export function useScrolled(collapseAt = 64, expandAt = 16): boolean {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const update = () => {
      const scrollY = window.scrollY;

      setScrolled((wasScrolled) =>
        wasScrolled ? scrollY > expandAt : scrollY > collapseAt,
      );
    };

    update();
    window.addEventListener("scroll", update, { passive: true });

    return () => {
      window.removeEventListener("scroll", update);
    };
  }, [collapseAt, expandAt]);

  return scrolled;
}
