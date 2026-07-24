import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchStudentDetail } from "../api/client";
import { formatAverage, formatMark } from "../utils/format";

export default function StudentDetail() {
  const { admissionNo } = useParams();
  const [student, setStudent] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | not_found | error

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");

    fetchStudentDetail(admissionNo)
      .then((data) => {
        if (!cancelled) {
          setStudent(data);
          setStatus("ready");
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus(err.status === 404 ? "not_found" : "error");
      });

    return () => {
      cancelled = true;
    };
  }, [admissionNo]);

  if (status === "loading") return <p>Loading...</p>;
  if (status === "not_found") {
    return (
      <div className="page">
        <p role="alert">No student found with admission number {admissionNo}.</p>
        <Link to="/">Back to students</Link>
      </div>
    );
  }
  if (status === "error") return <p role="alert">Could not load this student.</p>;

  return (
    <div className="page">
      <Link to="/">&larr; Back to students</Link>
      <h1>{student.name}</h1>
      <p>
        {student.admission_no} · Class {student.student_class}
        {student.section} · DOB {student.date_of_birth}
      </p>

      <table>
        <thead>
          <tr>
            <th>Subject</th>
            <th>Marks Obtained</th>
            <th>Max Marks</th>
          </tr>
        </thead>
        <tbody>
          {student.marks.map((mark) => (
            <tr key={mark.subject}>
              <td>{mark.subject}</td>
              <td>{formatMark(mark.marks_obtained)}</td>
              <td>{mark.max_marks}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p>
        <strong>Total:</strong> {student.total} &nbsp;&nbsp;
        <strong>Average:</strong> {formatAverage(student.average)}
      </p>
    </div>
  );
}
