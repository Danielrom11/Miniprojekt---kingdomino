"""
King Domino – FastAPI backend
Endpoints:
  GET  /health   → statuskontrol
  POST /analyze  → analysér et King Domino-billede og returner score + clusters
"""

import sys
import os
import io
import tempfile

import cv2 as cv
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Sørg for at Python kan finde kingdomino.py og point_calculator.py i roden af repoet
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from kingdomino import train_model, get_tiles, build_crown_templates  # noqa: E402
from point_calculator import calculate_score  # noqa: E402

app = FastAPI(
    title="King Domino API",
    description="Analysér et King Domino-bræt og beregn din score.",
    version="1.0.0",
)

# Tillad kald fra Expo-appen under udvikling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
# Laden af model og skabeloner sker én gang ved opstart
# ──────────────────────────────────────────────────────────────────────────────
print("Indlæser model og kronskabeloner …")
_model, _feature_cols, _label_encoder = train_model()
_crown_templates = build_crown_templates()
_SEARCH_THRESH1 = 200
_SEARCH_THRESH2 = 220
print("Klar til at modtage billeder.")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Returnerer 200 OK hvis serveren kører."""
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Modtager et billede (JPEG/PNG) af et King Domino-bræt.

    Returnerer:
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
          "coordinates": [[0,0],[0,1],[1,0],[1,1]]
        }
      ],
      "crown_boxes": [[x, y, w, h], ...]
    }
    ```
    """
    # Valider filtype
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(
            status_code=415,
            detail="Kun JPEG- og PNG-billeder understøttes.",
        )

    # Læs billeddata
    raw = await file.read()
    arr = np.frombuffer(raw, np.uint8)
    image = cv.imdecode(arr, cv.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=422,
            detail="Kunne ikke afkode billedet. Tjek at filen er et gyldigt billede.",
        )

    # Kør pipeline
    try:
        tiles = get_tiles(
            image,
            _model,
            _feature_cols,
            _label_encoder,
            _crown_templates,
            _SEARCH_THRESH1,
            _SEARCH_THRESH2,
        )
        final_score, clusters = calculate_score(tiles)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysefejl: {exc}") from exc

    # Saml krone-bokse fra tiles
    crown_boxes = []
    crowns_found = 0
    for (x_coord, y_coord), tile_data in tiles.items():
        n = tile_data.get("crowns", 0)
        crowns_found += n
        if n > 0:
            # Tilføj én boks per krone (centreret i feltet)
            for _ in range(n):
                crown_boxes.append([
                    int(x_coord * 100),
                    int(y_coord * 100),
                    100,
                    100,
                ])

    return {
        "score": int(final_score),
        "crowns_found": int(crowns_found),
        "clusters_count": len(clusters),
        "clusters": [
            {
                "terrain": c["terrain"],
                "tiles_count": int(c["tiles_count"]),
                "crowns_count": int(c["crowns_count"]),
                "score": int(c["score"]),
                "coordinates": [[int(cx), int(cy)] for cx, cy in c["coordinates"]],
            }
            for c in clusters
        ],
        "crown_boxes": crown_boxes,
    }
