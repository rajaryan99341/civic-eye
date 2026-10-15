from math import asin, cos, radians, sin, sqrt
from ai_classifier import hash_distance
from config import Config

def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    r = 6371000
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*r*asin(sqrt(a))

def find_duplicate(conn, *, category, latitude, longitude, image_hash, exclude_id=None):
    rows = conn.execute("""SELECT id, public_id, category, latitude, longitude, image_hash, status
        FROM complaints WHERE category = ? AND status != 'rejected'""", (category,)).fetchall()
    best, best_score = None, None
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id: continue
        distance = haversine_meters(latitude, longitude, row["latitude"], row["longitude"])
        if distance > Config.DUPLICATE_RADIUS_METERS: continue
        hdist = hash_distance(image_hash, row["image_hash"])
        if hdist > Config.DUPLICATE_HASH_THRESHOLD and distance > 25: continue
        score = distance + hdist*4
        if best_score is None or score < best_score:
            best = {"id":row["id"],"public_id":row["public_id"],"distance_meters":round(distance,1),"hash_distance":hdist}
            best_score = score
    return best
