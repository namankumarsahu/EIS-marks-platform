import { buildStudentsQuery } from "../utils/format";

const BASE_URL = "/api";

async function handleResponse(response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error("Request failed");
    error.status = response.status;
    error.payload = data;
    throw error;
  }
  return data;
}

export function fetchStudents(searchTerm) {
  return fetch(`${BASE_URL}/students/${buildStudentsQuery(searchTerm)}`).then(handleResponse);
}

export function fetchStudentDetail(admissionNo) {
  return fetch(`${BASE_URL}/students/${admissionNo}/`).then(handleResponse);
}

export function fetchSummary() {
  return fetch(`${BASE_URL}/summary/`).then(handleResponse);
}

export function postCorrection(payload) {
  return fetch(`${BASE_URL}/marks/corrections/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(handleResponse);
}
