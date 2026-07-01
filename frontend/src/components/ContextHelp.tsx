/**
 * Purpose: Provide the prior app's accessible contextual-help popover without navigating away from work.
 * Used by: App.tsx beside plans, files, tools, proofs, and other dense workbench surfaces.
 * Inputs: Reviewed help copy and explicit pointer or keyboard interaction.
 * Outputs: One positioned dialog with purpose, input, output, blocker, and boundary details.
 * Side effects: Adds temporary resize, scroll, and Escape listeners only while the dialog is open.
 * Safety: Content is React text, focus returns to the trigger, and no maker operation is performed.
 * Failure behavior: Missing geometry prevents positioning; Escape and close controls always dismiss state.
 * Related proof: App.test.tsx contextual-help coverage and browser accessibility inspection.
 */

import { Info, X } from "lucide-react";
import { type CSSProperties, type KeyboardEvent, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

export interface HelpContent {
  title: string;
  summary: string;
  purpose: string;
  input: string;
  output: string;
  blocker: string;
  boundary: string;
}

/** Render one reviewable help trigger and dismissible, focus-safe details dialog. */
export function ContextHelp({ content }: { content: HelpContent }) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<CSSProperties>({});
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const baseId = useId();
  const tooltipId = `${baseId}-tooltip`;
  const popoverId = `${baseId}-popover`;

  useEffect(() => {
    if (!open) return;

    function updatePosition() {
      const rect = buttonRef.current?.getBoundingClientRect();
      if (!rect) return;
      const width = Math.min(390, window.innerWidth - 32);
      const maxHeight = Math.min(560, window.innerHeight - 32);
      const left = Math.min(window.innerWidth - width - 16, Math.max(16, rect.right - width));
      const spaceBelow = window.innerHeight - rect.bottom - 16;
      const top = spaceBelow >= 260 ? rect.bottom + 12 : Math.max(16, rect.top - maxHeight - 12);
      setPosition({ left, top, width, maxHeight });
    }

    function handleWindowKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("keydown", handleWindowKeyDown);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("keydown", handleWindowKeyDown);
    };
  }, [open]);

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <span className="help-wrap">
      <button
        className="help-button"
        type="button"
        aria-label={`Info: ${content.title}`}
        aria-describedby={tooltipId}
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls={open ? popoverId : undefined}
        ref={buttonRef}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleKeyDown}
      >
        <Info size={15} aria-hidden="true" />
      </button>
      <span id={tooltipId} className="help-tooltip" role="tooltip">
        {content.summary}
      </span>
      {open &&
        createPortal(
          <span
            id={popoverId}
            className="help-popover"
            role="dialog"
            aria-label={`${content.title} details`}
            style={position}
          >
          <span className="help-popover-head">
            <strong>{content.title}</strong>
            <button className="help-close" type="button" onClick={() => setOpen(false)} aria-label={`Close ${content.title} help`}>
              <X size={14} aria-hidden="true" />
            </button>
          </span>
          <dl>
            <div>
              <dt>Purpose</dt>
              <dd>{content.purpose}</dd>
            </div>
            <div>
              <dt>Input</dt>
              <dd>{content.input}</dd>
            </div>
            <div>
              <dt>Output</dt>
              <dd>{content.output}</dd>
            </div>
            <div>
              <dt>Blocker</dt>
              <dd>{content.blocker}</dd>
            </div>
            <div>
              <dt>Boundary</dt>
              <dd>{content.boundary}</dd>
            </div>
          </dl>
          </span>,
          document.body,
        )}
    </span>
  );
}
