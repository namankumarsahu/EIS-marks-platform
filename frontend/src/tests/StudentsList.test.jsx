import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import StudentsList from "../pages/StudentsList";

const SAMPLE_STUDENTS = [
  {
    admission_no: "EIS-1008",
    name: "Arjun Sharma",
    student_class: "6",
    section: "B",
    date_of_birth: "2014-05-26",
    average: 70.0,
  },
];

describe("StudentsList", () => {
  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(SAMPLE_STUDENTS),
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches and renders the students list", async () => {
    render(
      <MemoryRouter>
        <StudentsList />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("Arjun Sharma")).toBeInTheDocument());
    expect(screen.getByText("70.0")).toBeInTheDocument();
  });

  it("hits the API with no search param on initial load", async () => {
    render(
      <MemoryRouter>
        <StudentsList />
      </MemoryRouter>
    );

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith("/api/students/"));
  });
});
