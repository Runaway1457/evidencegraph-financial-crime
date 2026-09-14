import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("investigation workspace", () => {
  it("renders evidence grounding, governance, and review state", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Project Meridian" })).toBeInTheDocument();
    expect(screen.getByText("Evidence-backed")).toBeInTheDocument();
    expect(screen.getByText("AI hypothesis · unverified")).toBeInTheDocument();
    expect(screen.getByText(/Immutable audit log/)).toBeInTheDocument();
    expect(screen.getByText(/ZERO DIRECT AI WRITES/)).toBeInTheDocument();
  });

  it("binds the inspector to the selected graph relationship", () => {
    render(<App />);
    const relationship = screen.getByRole("button", {
      name: /Orion Trade GmbH to Wallet 0x7A…91F/i,
    });

    fireEvent.click(relationship);

    expect(relationship).toHaveClass("selected");
    expect(screen.getByRole("heading", { name: "USDT 2.31M" })).toBeInTheDocument();
    expect(screen.getByText(/invoice amount and on-chain settlement/i)).toBeInTheDocument();
    const inspector = screen.getByLabelText("Relationship evidence inspector");
    expect(within(inspector).getByText("E-027")).toBeInTheDocument();
  });

  it("supports graph depth, view, and provenance controls", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Change graph depth" }));
    expect(screen.getByText("1 hops")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    expect(screen.getByRole("button", { name: "Table" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "Provenance on" }));
    expect(screen.getByRole("button", { name: "Provenance hidden" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("opens and closes the command palette with keyboard controls", () => {
    render(<App />);

    fireEvent.keyDown(window, { ctrlKey: true, key: "k" });
    const dialog = screen.getByRole("dialog", { name: "Command palette" });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByRole("searchbox", { name: "Search commands" })).toHaveFocus();

    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Command palette" })).not.toBeInTheDocument();
  });

  it("surfaces queued investigation and timeline filtering states", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Run investigation" }));
    expect(screen.getByRole("button", { name: "Investigation queued" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "AI analysis" }));
    expect(screen.getByText("Path hypothesis proposed")).toBeInTheDocument();
    expect(screen.queryByText("Invoice ingested")).not.toBeInTheDocument();
  });

  it("switches the active case context from the priority queue", () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /EG-2026-0139 Northstar/i }));

    expect(screen.getByRole("heading", { name: "Northstar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /EG-2026-0139 Northstar/i })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });
});
