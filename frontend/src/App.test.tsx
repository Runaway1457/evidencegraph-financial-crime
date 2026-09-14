import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("investigation workspace", () => {
  it("renders the case, evidence grounding, and human-review warning", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Project Meridian" })).toBeInTheDocument();
    expect(screen.getByText("Evidence-backed")).toBeInTheDocument();
    expect(screen.getByText("AI suggestion — requires review")).toBeInTheDocument();
    expect(screen.getByText("Immutable audit log")).toBeInTheDocument();
  });

  it("allows selecting a graph relationship", () => {
    render(<App />);
    const relationship = screen.getByRole("button", {
      name: /Orion Trade GmbH to Wallet 0x7A…91F/i,
    });
    fireEvent.click(relationship);
    expect(relationship).toHaveClass("selected");
  });
});
