import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SearchBox from "../components/SearchBox";

describe("SearchBox", () => {
  it("renders the current value", () => {
    render(<SearchBox value="arjun" onChange={() => {}} />);
    expect(screen.getByLabelText(/search students/i)).toHaveValue("arjun");
  });

  it("calls onChange with the new text as the user types", () => {
    const onChange = vi.fn();
    render(<SearchBox value="" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/search students/i), {
      target: { value: "diya" },
    });
    expect(onChange).toHaveBeenCalledWith("diya");
  });

  it("uses the provided placeholder when given", () => {
    render(<SearchBox value="" onChange={() => {}} placeholder="Find a student" />);
    expect(screen.getByPlaceholderText("Find a student")).toBeInTheDocument();
  });
});
