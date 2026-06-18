"""
FastAPI backend for the King Domino points calculator.

Endpoints:
  GET  /health   – liveness check
  POST /analyze  – upload a 500×500 game-board image; returns terrain, crowns and score
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import cv2 as cv
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Path setup – the heavy lifting is in the modules at the project root
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # repo root
sys.path.insert(0, str(BASE_DIR))

from point_calculator import calculate_score  # noqa: E402

# ---------------------------------------------------------------------------
# Paths to static assets (training data + crown templates)
# ---------------------------------------------------------------------------
TRAINING_EXCEL = BASE_DIR / "Trainingset" / "kingdomino_tiles_hsv_histogram_kopi.xlsx"
TEMPLATE_CANDIDATES = [
    (BASE_DIR / "features" / "krone_blaa_baggrund_hr.JPG", 180, 210, 0.7, 0.15),
    (BASE_DIR / "features" / "krone_blaa_baggrund_lr.JPG", 130, 150, 0.7, 0.15),
    (BASE_DIR / "features" / "krone_sort_baggrund_hr.JPG", 140, 180, 0.6, 0.15),
    (BASE_DIR / "features" / "krone_sort_baggrund_lr.JPG",  80, 110, 0.6, 0.15),
    (BASE_DIR / "features" / "krone_sort_baggrund.JPG",    140, 180, 0.6, 0.15),
]

# ---------------------------------------------------------------------------
# Model + template loading at startup (expensive – do it once)
# ---------------------------------------------------------------------------
_model: RandomForestClassifier | None = None
_feature_cols: list[str] | None = None
_label_encoder: LabelEncoder | None = None
_templates: list[tuple] | None = None


def _load_model() -> tuple[RandomForestClassifier, list[str], LabelEncoder]:
    df = pd.read_excel(TRAINING_EXCEL)
    df = df[df["Manual_Label"].notna()].copy()

    metadata_cols = ["Reference", "Image", "Tile_X", "Tile_Y", "Predicted_Terrain"]
    target_col = "Manual_Label"
    feature_cols = [
        col
        for col in df.columns
        if col not in metadata_cols + [target_col]
        and (col.startswith(("H_Bin", "S_Bin", "V_Bin")) or col in ["H_Median", "S_Median", "V_Median"])
    ]

    X = df[feature_cols].fillna(df[feature_cols].median(numeric_only=True))
    y = df[target_col].astype(str)

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    model = RandomForestClassifier(
        random_state=42,
        n_estimators=100,
        max_depth=None,
        min_samples_split=10,
    )
    model.fit(X, y_encoded)
    return model, feature_cols, label_encoder


def _load_template(path: Path) -> tuple[np.ndarray | None, np.ndarray | None]:
    img_bgr = cv.imread(str(path), cv.IMREAD_COLOR)
    if img_bgr is None:
        return None, None
    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    return img_hsv, img_hsv_gray


def _load_templates() -> list[tuple]:
    templates = []
    for template_path, t1, t2, match_t, edge_t in TEMPLATE_CANDIDATES:
        if not template_path.exists():
            continue
        hsv, hsv_gray = _load_template(template_path)
        if hsv is None or hsv_gray is None:
            continue
        templates.append((hsv, hsv_gray, t1, t2, match_t, edge_t))
    return templates


@asynccontextmanager
async def _lifespan(application: FastAPI):
    global _model, _feature_cols, _label_encoder, _templates
    if TRAINING_EXCEL.exists():
        _model, _feature_cols, _label_encoder = _load_model()
    _templates = _load_templates()
    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="King Domino Analyzer",
    description="Analyzes a King Domino game-board image and returns the calculated score.",
    version="1.0.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Image analysis helpers
# ---------------------------------------------------------------------------

def _get_terrain(tile: np.ndarray, bin_size: int = 10) -> dict:
    hsv_tile = cv.cvtColor(tile, cv.COLOR_BGR2HSV)
    h_channel = hsv_tile[:, :, 0].flatten()
    s_channel = hsv_tile[:, :, 1].flatten()
    v_channel = hsv_tile[:, :, 2].flatten()
    hue, saturation, value = np.median(hsv_tile, axis=(0, 1))

    h_bins = np.arange(0, 190, bin_size)
    s_bins = np.arange(0, 260, bin_size)
    v_bins = np.arange(0, 260, bin_size)

    h_hist, _ = np.histogram(h_channel, bins=h_bins)
    s_hist, _ = np.histogram(s_channel, bins=s_bins)
    v_hist, _ = np.histogram(v_channel, bins=v_bins)

    features: dict = {
        "H_Median": round(float(hue), 2),
        "S_Median": round(float(saturation), 2),
        "V_Median": round(float(value), 2),
    }
    for i, cnt in enumerate(h_hist):
        br = i * 10
        features[f"H_Bin_{br}-{br + 10}"] = int(cnt)
    for i, cnt in enumerate(s_hist):
        br = i * 10
        be = br + 10 if i < len(s_hist) - 1 else 255
        features[f"S_Bin_{br}-{be}"] = int(cnt)
    for i, cnt in enumerate(v_hist):
        br = i * 10
        be = br + 10 if i < len(v_hist) - 1 else 255
        features[f"V_Bin_{br}-{be}"] = int(cnt)
    return features


def _predict_terrain(features: dict, model: RandomForestClassifier, feature_cols: list[str], label_encoder: LabelEncoder) -> str:
    df = pd.DataFrame([features])[feature_cols]
    encoded = model.predict(df)
    return label_encoder.inverse_transform(encoded)[0]


def _detect_crowns(
    search_match: np.ndarray,
    search_edges_gray: np.ndarray,
    templates: list[tuple],
    search_thresh1: int = 200,
    search_thresh2: int = 220,
) -> np.ndarray:
    potential: list[tuple] = []
    for template_hsv, template_hsv_gray, t1, t2, match_thresh, edge_thresh in templates:
        for scale in np.linspace(1.15, 0.95, 5):
            rw = int(template_hsv.shape[1] * scale)
            rh = int(template_hsv.shape[0] * scale)
            if rw < 15 or rh < 15:
                continue
            rt_hsv = cv.resize(template_hsv, (rw, rh))
            rt_gray = cv.resize(template_hsv_gray, (rw, rh))
            for angle in [0, 90, 180, 270]:
                if angle == 0:
                    ct_hsv, ct_gray = rt_hsv, rt_gray
                elif angle == 90:
                    ct_hsv = cv.rotate(rt_hsv, cv.ROTATE_90_CLOCKWISE)
                    ct_gray = cv.rotate(rt_gray, cv.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    ct_hsv = cv.rotate(rt_hsv, cv.ROTATE_180)
                    ct_gray = cv.rotate(rt_gray, cv.ROTATE_180)
                else:
                    ct_hsv = cv.rotate(rt_hsv, cv.ROTATE_90_COUNTERCLOCKWISE)
                    ct_gray = cv.rotate(rt_gray, cv.ROTATE_90_COUNTERCLOCKWISE)

                res = cv.matchTemplate(search_match, ct_hsv, cv.TM_CCOEFF_NORMED)
                loc = np.where(res >= match_thresh)
                h, w = ct_gray.shape[:2]
                for pt in zip(*loc[::-1]):
                    potential.append(([int(pt[0]), int(pt[1]), int(w), int(h)], ct_gray, t1, t2, edge_thresh))

    confirmed: list[list[int]] = []
    search_edges = cv.Canny(search_edges_gray, search_thresh1, search_thresh2)

    for rect, tgray, t1, t2, edge_thresh in potential:
        x, y, w, h = rect
        roi = search_edges[y: y + h, x: x + w]
        tedges = cv.Canny(tgray, t1, t2)
        if roi.size == 0 or tedges.size == 0:
            continue
        if tedges.shape[0] > roi.shape[0] or tedges.shape[1] > roi.shape[1]:
            continue
        er = cv.matchTemplate(roi, tedges, cv.TM_CCOEFF_NORMED)
        if float(np.max(er)) >= edge_thresh:
            confirmed.append(rect)

    if not confirmed:
        return np.empty((0, 4), dtype=np.int32)
    grouped, _ = cv.groupRectangles(confirmed, groupThreshold=1, eps=0.5)
    if len(grouped) == 0:
        grouped = np.array(confirmed, dtype=np.int32)
    return grouped


def _analyze_image(image: np.ndarray) -> dict:
    if _model is None or _feature_cols is None or _label_encoder is None:
        raise RuntimeError("Model not loaded – training data missing.")
    if not _templates:
        raise RuntimeError("No crown templates loaded.")

    img_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    crown_rects = _detect_crowns(img_hsv, img_hsv_gray, _templates)

    tiles: dict = {}
    for y_coord in range(5):
        for x_coord in range(5):
            tile = image[y_coord * 100: (y_coord + 1) * 100, x_coord * 100: (x_coord + 1) * 100]
            terrain_features = _get_terrain(tile)
            terrain = _predict_terrain(terrain_features, _model, _feature_cols, _label_encoder)

            x0, y0 = x_coord * 100, y_coord * 100
            x1, y1 = x0 + 100, y0 + 100
            crowns = sum(
                1 for cx, cy, cw, ch in crown_rects
                if x0 <= cx + cw // 2 < x1 and y0 <= cy + ch // 2 < y1
            )
            tiles[(x_coord, y_coord)] = {"terrain": terrain, "crowns": crowns}

    total_score, clusters = calculate_score(tiles)
    return {"tiles": tiles, "total_score": total_score, "clusters": clusters}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check")
def health() -> dict:
    """Returns OK when the server is running."""
    model_ready = _model is not None
    templates_ready = bool(_templates)
    return {
        "status": "ok",
        "model_ready": model_ready,
        "templates_loaded": len(_templates) if _templates else 0,
        "ready": model_ready and templates_ready,
    }


@app.post("/analyze", summary="Analyze a King Domino board image")
async def analyze(file: UploadFile = File(...)) -> dict:
    """
    Upload a 500×500 JPEG/PNG image of a completed King Domino board.

    Returns the detected terrain type and crown count for each of the 25 tiles,
    as well as the total score and a breakdown of scoring clusters.
    """
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are accepted.")

    raw = await file.read()
    arr = np.frombuffer(raw, np.uint8)
    image = cv.imdecode(arr, cv.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    # Resize to 500×500 if necessary
    if image.shape[:2] != (500, 500):
        image = cv.resize(image, (500, 500))

    try:
        result = _analyze_image(image)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Convert tuple keys to strings for JSON serialisation
    tiles_json = {
        f"{x},{y}": {"terrain": data["terrain"], "crowns": data["crowns"]}
        for (x, y), data in result["tiles"].items()
    }
    clusters_json = [
        {
            "terrain": c["terrain"],
            "tiles_count": c["tiles_count"],
            "crowns_count": c["crowns_count"],
            "score": c["score"],
            "coordinates": [[coord[0], coord[1]] for coord in c["coordinates"]],
        }
        for c in result["clusters"]
    ]

    return {
        "total_score": result["total_score"],
        "tiles": tiles_json,
        "clusters": clusters_json,
    }
