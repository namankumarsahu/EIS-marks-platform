import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchStudents } from "../api/client";
import SearchBox from "../components/SearchBox";
import { formatAverage } from "../utils/format";

export default function StudentsList() {
  const [search, setSearch] = useState("");
  const [students, setStudents] = useState([]);
  const [status, setStatus] = useState("idle"); // idle | loading | error

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");

    fetchStudents(search)
      .then((data) => {
        if (!cancelled) {
          setStudents(data);
          setStatus("idle");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [search]);

  return (
    <div className="page">
      <h1>Students</h1>
      <SearchBox value={search} onChange={setSearch} />

      {status === "error" && <p role="alert">Could not load students.</p>}

      <table>
        <thead>
          <tr>
            <th>Admission No</th>
            <th>Name</th>
            <th>Class</th>
            <th>Section</th>
            <th>DOB</th>
            <th>Average</th>
          </tr>
        </thead>
        <tbody>
          {students.map((student) => (
            <tr key={student.admission_no}>
              <td>
                <Link to={`/students/${student.admission_no}`}>{student.admission_no}</Link>
              </td>
              <td>{student.name}</td>
              <td>{student.student_class}</td>
              <td>{student.section}</td>
              <td>{student.date_of_birth}</td>
              <td>{formatAverage(student.average)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {status === "idle" && students.length === 0 && <p>No students match that search.</p>}
    </div>
  );
}
