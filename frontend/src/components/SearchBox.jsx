export default function SearchBox({ value, onChange, placeholder = "Search by name..." }) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      aria-label="Search students by name"
      className="search-box"
    />
  );
}
