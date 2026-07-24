/**
 * Pure display-formatting helpers. Kept free of React/DOM so they can be
 * unit tested directly. A `null` mark or average always means "the
 * student didn't sit that exam" per the assignment's absent rule, and
 * must render as "Absent" rather than 0 or a blank cell.
 */

export function formatMark(marksObtained) {
  return marksObtained === null || marksObtained === undefined ? "Absent" : String(marksObtained);
}

export function formatAverage(average) {
  if (average === null || average === undefined) {
    return "N/A";
  }
  return average.toFixed(1);
}

/**
 * Builds the querystring for the students search endpoint. Trims the
 * term and omits the param entirely when it's empty, so
 * GET /api/students/ (no filter) is what an empty search box sends.
 */
export function buildStudentsQuery(searchTerm) {
  const trimmed = (searchTerm || "").trim();
  return trimmed ? `?search=${encodeURIComponent(trimmed)}` : "";
}
