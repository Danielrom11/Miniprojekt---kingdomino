# King Domino – Backend (FastAPI)

This FastAPI service analyses a King Domino game-board image and returns the calculated score.

## Requirements

- Python ≥ 3.10
- The training data and crown templates from the project root must be present.

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Running

```bash
# From the project root (so that point_calculator.py and Trainingset/ are on the path)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or from inside the `backend/` directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

| Method | Path       | Description                                        |
|--------|------------|----------------------------------------------------|
| GET    | `/health`  | Liveness check – returns model/template status     |
| POST   | `/analyze` | Upload a 500×500 JPEG/PNG; returns score + details |

### Example – health check

```bash
curl http://localhost:8000/health
```

### Example – analyze a board

```bash
curl -X POST http://localhost:8000/analyze \
     -F "file=@Trainingset/1.jpg" | python3 -m json.tool
```

## Response format (`/analyze`)

```json
{
  "total_score": 42,
  "tiles": {
    "0,0": { "terrain": "Forest", "crowns": 1 },
    "1,0": { "terrain": "blank",  "crowns": 0 }
  },
  "clusters": [
    {
      "terrain": "Forest",
      "tiles_count": 7,
      "crowns_count": 3,
      "score": 21,
      "coordinates": [[0,0],[0,1]]
    }
  ]
}
```
