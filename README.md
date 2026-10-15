# CIVIC EYE

**SEE THE ISSUE. TRIGGER THE ACTION.**

CIVIC EYE is a full-stack platform for reporting and managing local civic faults such as potholes, garbage accumulation, damaged streetlights, and waterlogging.

## Portals
- Citizen portal: report an issue with a photograph and location, then track its status.
- Municipal authority portal: review statistics, assign reports, update statuses, and view issues on a map.

## Technology
- React 18, Vite, React Router, Leaflet
- Python Flask API and SQLite
- Pillow and NumPy visual-feature classifier
- Location and perceptual-hash duplicate detection

## Run locally
Backend terminal:
```bash
cd backend
python -m pip install -r requirements.txt
python app.py
```
Frontend terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. Vite proxies `/api` requests to Flask on port 5000.

## Demo accounts
| Portal | Email | Password |
|---|---|---|
| Citizen | `citizen@civiceye.local` | `Citizen@123` |
| Authority officer | `officer@civiceye.local` | `Officer@123` |
| Authority admin | `admin@civiceye.local` | `Admin@123` |

## AI classifier
`backend/ai_classifier.py` uses visual features such as brightness, colour dominance, saturation, edges, and bright-spot ratios. It is a lightweight visual-feature classifier, not a deep neural network trained on a large labelled dataset. Officers can override a suggested category.

## Tests
```bash
cd backend
python -m pytest tests/test_api.py -q
```

Local databases, uploaded user images, environment files, and virtual environments should not be committed.