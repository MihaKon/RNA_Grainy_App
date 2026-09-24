import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DropdownMenu } from "./DropdownMenu";

function renderMenu() {
  const onPdb = vi.fn();
  const onCif = vi.fn();
  render(
    <>
      <DropdownMenu
        label="Download"
        items={[
          { id: "pdb", label: "PDB", onSelect: onPdb },
          { id: "old", label: "Legacy", disabled: true, onSelect: vi.fn() },
          { id: "cif", label: "mmCIF", onSelect: onCif },
        ]}
      />
      <p>Outside</p>
    </>,
  );
  return { user: userEvent.setup(), onPdb, onCif };
}

describe("DropdownMenu", () => {
  it("opens with the keyboard, skips disabled items and selects with Enter", async () => {
    const { user, onCif } = renderMenu();

    await user.tab();
    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("menuitem", { name: "PDB" })).toHaveFocus();

    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("menuitem", { name: "mmCIF" })).toHaveFocus();

    await user.keyboard("{Enter}");
    expect(onCif).toHaveBeenCalledOnce();
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download" })).toHaveFocus();
  });

  it("closes on Escape and on outside clicks", async () => {
    const { user, onPdb } = renderMenu();
    const button = screen.getByRole("button", { name: "Download" });

    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(button).toHaveFocus();

    await user.click(button);
    await user.click(screen.getByText("Outside"));
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(onPdb).not.toHaveBeenCalled();
  });

  it("ignores clicks on disabled items", async () => {
    const { user } = renderMenu();

    await user.click(screen.getByRole("button", { name: "Download" }));
    await user.click(screen.getByRole("menuitem", { name: "Legacy" }));

    expect(screen.getByRole("menu")).toBeInTheDocument();
  });
});
