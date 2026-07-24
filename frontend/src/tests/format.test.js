import { describe, expect, it } from "vitest";

import { buildStudentsQuery, formatAverage, formatMark } from "../utils/format";

describe("formatMark", () => {
  it("shows Absent for null", () => {
    expect(formatMark(null)).toBe("Absent");
  });

  it("shows Absent for undefined", () => {
    expect(formatMark(undefined)).toBe("Absent");
  });

  it("shows the number as a string otherwise", () => {
    expect(formatMark(87)).toBe("87");
  });

  it("shows a genuine zero, not Absent", () => {
    expect(formatMark(0)).toBe("0");
  });
});

describe("formatAverage", () => {
  it("shows N/A for null", () => {
    expect(formatAverage(null)).toBe("N/A");
  });

  it("formats to exactly one decimal place", () => {
    expect(formatAverage(81)).toBe("81.0");
    expect(formatAverage(70.5)).toBe("70.5");
  });
});

describe("buildStudentsQuery", () => {
  it("returns empty string for blank search", () => {
    expect(buildStudentsQuery("")).toBe("");
    expect(buildStudentsQuery("   ")).toBe("");
    expect(buildStudentsQuery(undefined)).toBe("");
  });

  it("builds a search querystring, trimmed", () => {
    expect(buildStudentsQuery("  arjun  ")).toBe("?search=arjun");
  });

  it("URL-encodes special characters", () => {
    expect(buildStudentsQuery("a b")).toBe("?search=a%20b");
  });
});
