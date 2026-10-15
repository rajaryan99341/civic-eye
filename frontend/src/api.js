const API = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export async function api(path, { method = "GET", body, token, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(`${API}${path}`, { method, headers, body: payload });
  } catch {
    throw new Error("Cannot reach the CIVIC EYE server. Check that the Flask API is running.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

export function imageUrl(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/api/")) return `${API}${path}`;
  return `${API}/api/uploads/${path}`;
}
