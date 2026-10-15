export default function StatusBadge({ status, kind = "status" }) {
  if (!status) return null;
  return <span className={`badge b-${status}`}>{String(status).replaceAll("_", " ")}</span>;
}
