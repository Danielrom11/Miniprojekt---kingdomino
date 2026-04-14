# Backend – King Domino API

FastAPI-backend der analyserer et King Domino-bræt og beregner scoren.

## Opsætning

```bash
cd backend
pip install -r requirements.txt
```

## Start serveren

```bash
# Fra repoets rod:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Serveren er nu tilgængelig på `http://localhost:8000`.

## Endpoints

| Metode | Sti         | Beskrivelse                                     |
|--------|-------------|-------------------------------------------------|
| GET    | `/health`   | Statuskontrol – returnerer `{"status": "ok"}`   |
| POST   | `/analyze`  | Analysér et billede og returner score + clusters |

### POST /analyze

**Request:** `multipart/form-data` med feltet `file` (JPEG eller PNG).

**Response:**
```json
{
  "score": 42,
  "crowns_found": 5,
  "clusters_count": 3,
  "clusters": [
    {
      "terrain": "Forest",
      "tiles_count": 4,
      "crowns_count": 2,
      "score": 8,
      "coordinates": [[0, 0], [0, 1], [1, 0], [1, 1]]
    }
  ],
  "crown_boxes": [[x, y, w, h], ...]
}
```

## Interaktiv dokumentation

Åbn `http://localhost:8000/docs` i en browser for at teste API'et direkte.
