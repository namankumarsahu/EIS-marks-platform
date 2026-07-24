import { NavLink } from "react-router-dom";

export default function NavBar() {
  return (
    <nav className="navbar">
      <span className="brand">EIS Class 6 Marks</span>
      <NavLink to="/" end>
        Students
      </NavLink>
      <NavLink to="/summary">Summary</NavLink>
    </nav>
  );
}
