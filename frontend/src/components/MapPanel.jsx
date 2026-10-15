import { useEffect, useRef } from "react";
import L from "leaflet";

const icon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export default function MapPanel({ points = [], center, onPick }) {
  const ref = useRef(null);
  const mapRef = useRef(null);
  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const start = center ? [center.latitude, center.longitude] : points[0] ? [points[0].latitude, points[0].longitude] : [12.9716, 77.5946];
    const map = L.map(ref.current).setView(start, 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "&copy; OpenStreetMap" }).addTo(map);
    if (onPick) map.on("click", (e) => onPick({ latitude: e.latlng.lat, longitude: e.latlng.lng }));
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.eachLayer((layer) => { if (layer instanceof L.Marker) map.removeLayer(layer); });
    points.forEach((p) => {
      if (p.latitude == null || p.longitude == null) return;
      const m = L.marker([p.latitude, p.longitude], { icon }).addTo(map);
      if (p.title) m.bindPopup(`<strong>${p.public_id || ""}</strong><br/>${p.title}<br/>${p.status || ""}`);
    });
    if (center) map.setView([center.latitude, center.longitude], 15);
  }, [points, center]);
  return <div className="map" ref={ref} />;
}
