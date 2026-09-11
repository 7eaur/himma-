import { useCallback, useRef, useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { useAccessibleDialog } from "./useAccessibleDialog";

function Harness() {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const close = useCallback(() => setOpen(false), []);
  useAccessibleDialog({ open, dialogRef, returnFocusRef: triggerRef, onClose: close });

  return <>
    <button ref={triggerRef} onClick={() => setOpen(true)}>open</button>
    {open && <div ref={dialogRef} role="dialog" tabIndex={-1}>
      <button>first</button>
      <button>last</button>
    </div>}
  </>;
}

describe("useAccessibleDialog", () => {
  it("moves focus in, traps Tab, closes on Escape and returns focus", () => {
    render(<Harness />);
    const trigger = screen.getByText("open");
    trigger.focus();
    fireEvent.click(trigger);

    const first = screen.getByText("first");
    const last = screen.getByText("last");
    expect(first).toHaveFocus();

    last.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(first).toHaveFocus();

    first.focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(last).toHaveFocus();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });
});
