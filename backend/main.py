from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2 as cv
import numpy as np

from backend.engine import analyze_board

app = FastAPI(title="KingDomino API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload en billedfil.")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Tom fil modtaget.")

    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv.imdecode(arr, cv.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Kunne ikke læse billedet.")

    try:
        result = analyze_board(image)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analyse fejlede: {exc}") from exc
