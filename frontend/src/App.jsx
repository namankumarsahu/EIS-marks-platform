import { Route, Routes } from "react-router-dom";

import NavBar from "./components/NavBar";
import StudentDetail from "./pages/StudentDetail";
import StudentsList from "./pages/StudentsList";
import Summary from "./pages/Summary";

export default function App() {
  return (
    <div>
      <NavBar />
      <Routes>
        <Route path="/" element={<StudentsList />} />
        <Route path="/students/:admissionNo" element={<StudentDetail />} />
        <Route path="/summary" element={<Summary />} />
      </Routes>
    </div>
  );
}
