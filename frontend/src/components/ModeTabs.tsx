/**
 * Purpose: Render keyboard-operable Work Flow, Plans, and Dev tabs from caller-owned content.
 * Used by: App.tsx as the stable mode switcher in the central command surface.
 * Inputs: Tab definitions, active tab identity, and an onChange callback.
 * Outputs: ARIA-linked tab and tabpanel elements with one visible panel.
 * Side effects: Calls onChange after explicit click or supported arrow, Home, and End keys.
 * Safety: Switching tabs changes presentation state only and performs no backend action.
 * Failure behavior: Unknown active identities fall back to the first tab for keyboard movement.
 * Related proof: App.test.tsx mode-switching coverage.
 */

import { type KeyboardEvent, type ReactNode, useId } from "react";

interface TabDefinition {
  id: string;
  label: string;
  content: ReactNode;
}

interface ModeTabsProps {
  tabs: TabDefinition[];
  active: string;
  onChange: (id: string) => void;
}

/** Render one ARIA tablist and delegate explicit tab selection to its owner. */
export function ModeTabs({ tabs, active, onChange }: ModeTabsProps) {
  const baseId = useId();
  const activeIndex = Math.max(
    0,
    tabs.findIndex((tab) => tab.id === active),
  );

  function move(delta: number) {
    const next = (activeIndex + delta + tabs.length) % tabs.length;
    onChange(tabs[next].id);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      move(1);
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      move(-1);
    }
    if (event.key === "Home") {
      event.preventDefault();
      onChange(tabs[0].id);
    }
    if (event.key === "End") {
      event.preventDefault();
      onChange(tabs[tabs.length - 1].id);
    }
  }

  return (
    <section className="mode-panel" aria-labelledby={`${baseId}-label`}>
      <h2 id={`${baseId}-label`} className="sr-only">
        Panel Modes
      </h2>
      <div className="tabs" role="tablist" aria-label="Panel modes" onKeyDown={handleKeyDown}>
        {tabs.map((tab) => {
          const selected = tab.id === active;
          return (
            <button
              key={tab.id}
              id={`${baseId}-${tab.id}-tab`}
              className="tab-button"
              role="tab"
              aria-selected={selected}
              aria-controls={`${baseId}-${tab.id}-panel`}
              tabIndex={selected ? 0 : -1}
              type="button"
              onClick={() => onChange(tab.id)}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          id={`${baseId}-${tab.id}-panel`}
          className="tab-panel"
          role="tabpanel"
          aria-labelledby={`${baseId}-${tab.id}-tab`}
          hidden={tab.id !== active}
          tabIndex={0}
        >
          {tab.content}
        </div>
      ))}
    </section>
  );
}
