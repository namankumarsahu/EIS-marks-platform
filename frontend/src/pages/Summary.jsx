import { useEffect, useState } from "react";

import { fetchSummary } from "../api/client";
import { formatAverage } from "../utils/format";

export default function Summary() {
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    let cancelled = false;
    fetchSummary()
      .then((data) => {
        if (!cancelled) {
          setSummary(data);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") return <p>Loading...</p>;
  if (status === "error") return <p role="alert">Could not load the summary.</p>;

  const subjectNames = Object.keys(summary.subject_averages);

  return (
    <div className="page">
      <h1>Class Summary</h1>

      <h2>Subject Averages</h2>
      <table>
        <thead>
          <tr>
            <th>Subject</th>
            <th>Class Average</th>
          </tr>
        </thead>
        <tbody>
          {subjectNames.map((subject) => (
            <tr key={subject}>
              <td>{subject}</td>
              <td>{formatAverage(summary.subject_averages[subject])}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Top Student</h2>
      {summary.top_student ? (
        <p>
          <strong>{summary.top_student.name}</strong> ({summary.top_student.admission_no}) — total{" "}
          {summary.top_student.total}
        </p>
      ) : (
        <p>No students on record.</p>
      )}
    </div>
  );
}
