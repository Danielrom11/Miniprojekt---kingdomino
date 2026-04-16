from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2 as cv
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from point_calculator import calculate_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING_EXCEL = PROJECT_ROOT / "Trainingset" / "kingdomino_tiles_hsv_histogram_kopi.xlsx"
FEATURES_DIR = PROJECT_ROOT / "features"

# (filename, template_thresh1, template_thresh2, match_threshold, edge_similarity_threshold)
TEMPLATE_CONFIGS = [
    ("krone_blaa_baggrund_hr.JPG", 180, 210, 0.7, 0.15),
    ("krone_blaa_baggrund_lr.JPG", 130, 150, 0.7, 0.15),
    ("krone_sort_baggrund_hr.JPG", 140, 180, 0.6, 0.15),
    ("krone_sort_baggrund_lr.JPG", 80, 110, 0.6, 0.15),
    ("krone_sort_baggrund.JPG", 140, 180, 0.6, 0.15),
]


def _resolve_feature_file(filename: str) -> Path | None:
    if not FEATURES_DIR.exists():
        return None

    filename_lower = filename.lower()
    for p in FEATURES_DIR.iterdir():
        if p.is_file() and p.name.lower() == filename_lower:
            return p
    return None


def _load_and_prepare_template(path: Path) -> tuple[np.ndarray | None, np.ndarray | None]:
    img_bgr = cv.imread(str(path), cv.IMREAD_COLOR)
    if img_bgr is None:
        return None, None

    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    return img_hsv, img_hsv_gray


def _load_templates() -> list[tuple[np.ndarray, np.ndarray, int, int, float, float]]:
    templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]] = []
    for filename, t1, t2, match_t, edge_t in TEMPLATE_CONFIGS:
        template_path = _resolve_feature_file(filename)
        if template_path is None:
            continue
        template_hsv, template_hsv_gray = _load_and_prepare_template(template_path)
        if template_hsv is None or template_hsv_gray is None:
            continue
        templates.append((template_hsv, template_hsv_gray, t1, t2, match_t, edge_t))

    if not templates:
        raise FileNotFoundError("Ingen crown templates kunne indlæses fra features-mappen.")
    return templates


def _train_model() -> tuple[RandomForestClassifier, list[str], LabelEncoder]:
    if not TRAINING_EXCEL.exists():
        raise FileNotFoundError(f"Training-fil ikke fundet: {TRAINING_EXCEL}")

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


@lru_cache(maxsize=1)
def _get_context() -> tuple[RandomForestClassifier, list[str], LabelEncoder, list[tuple[np.ndarray, np.ndarray, int, int, float, float]]]:
    model, feature_cols, label_encoder = _train_model()
    templates = _load_templates()
    return model, feature_cols, label_encoder, templates


def _get_terrain(tile: np.ndarray, bin_size: int = 10) -> dict[str, float | int]:
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

    features: dict[str, float | int] = {
        "H_Median": round(float(hue), 2),
        "S_Median": round(float(saturation), 2),
        "V_Median": round(float(value), 2),
    }

    for i, h_count in enumerate(h_hist):
        bin_range = i * 10
        features[f"H_Bin_{bin_range}-{bin_range + 10}"] = int(h_count)

    for i, s_count in enumerate(s_hist):
        bin_range = i * 10
        bin_end = bin_range + 10 if i < len(s_hist) - 1 else 255
        features[f"S_Bin_{bin_range}-{bin_end}"] = int(s_count)

    for i, v_count in enumerate(v_hist):
        bin_range = i * 10
        bin_end = bin_range + 10 if i < len(v_hist) - 1 else 255
        features[f"V_Bin_{bin_range}-{bin_end}"] = int(v_count)

    return features


def _predict_terrain(terrain_features: dict[str, float | int], model: RandomForestClassifier, feature_cols: list[str], label_encoder: LabelEncoder) -> str:
    features_df = pd.DataFrame([terrain_features])
    features_df = features_df[feature_cols]
    prediction_encoded = model.predict(features_df)
    prediction = label_encoder.inverse_transform(prediction_encoded)
    return str(prediction[0])


def _detect_crowns(
    search_image_match: np.ndarray,
    search_image_edges: np.ndarray,
    templates_with_thresholds: list[tuple[np.ndarray, np.ndarray, int, int, float, float]],
    search_thresh1: int = 200,
    search_thresh2: int = 220,
) -> np.ndarray:
    potential_matches: list[tuple[list[int], np.ndarray, int, int, float]] = []

    for template_hsv, template_hsv_gray, t_thresh1, t_thresh2, match_thresh, edge_sim_thresh in templates_with_thresholds:
        for scale in np.linspace(1.15, 0.95, 5):
            resized_w = int(template_hsv.shape[1] * scale)
            resized_h = int(template_hsv.shape[0] * scale)
            if resized_w < 15 or resized_h < 15:
                continue

            resized_t_hsv = cv.resize(template_hsv, (resized_w, resized_h))
            resized_t_gray = cv.resize(template_hsv_gray, (resized_w, resized_h))

            for angle in [0, 90, 180, 270]:
                if angle == 0:
                    curr_t_hsv = resized_t_hsv
                    curr_t_gray = resized_t_gray
                elif angle == 90:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_90_CLOCKWISE)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_180)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_180)
                else:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_90_COUNTERCLOCKWISE)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_90_COUNTERCLOCKWISE)

                res = cv.matchTemplate(search_image_match, curr_t_hsv, cv.TM_CCOEFF_NORMED)
                loc = np.where(res >= match_thresh)

                h, w = curr_t_gray.shape[:2]
                for pt in zip(*loc[::-1]):
                    potential_matches.append(([int(pt[0]), int(pt[1]), int(w), int(h)], curr_t_gray, t_thresh1, t_thresh2, edge_sim_thresh))

    confirmed_rects: list[list[int]] = []
    search_edges = cv.Canny(search_image_edges, search_thresh1, search_thresh2)

    for rect, template_gray, t_thresh1, t_thresh2, edge_sim_thresh in potential_matches:
        x, y, w, h = rect
        roi_edges = search_edges[y : y + h, x : x + w]
        template_edges = cv.Canny(template_gray, t_thresh1, t_thresh2)

        if roi_edges.size == 0 or template_edges.size == 0:
            continue
        if template_edges.shape[0] > roi_edges.shape[0] or template_edges.shape[1] > roi_edges.shape[1]:
            continue

        edge_res = cv.matchTemplate(roi_edges, template_edges, cv.TM_CCOEFF_NORMED)
        if float(np.max(edge_res)) >= edge_sim_thresh:
            confirmed_rects.append(rect)

    if not confirmed_rects:
        return np.empty((0, 4), dtype=np.int32)

    rects, _ = cv.groupRectangles(confirmed_rects, groupThreshold=1, eps=0.5)
    if len(rects) == 0:
        return np.array(confirmed_rects, dtype=np.int32)
    return rects


def analyze_board(image_bgr: np.ndarray) -> dict:
    model, feature_cols, label_encoder, templates = _get_context()

    # MVP: normalize input to same board size expected by current pipeline.
    resized = cv.resize(image_bgr, (500, 500), interpolation=cv.INTER_AREA)
    image_hsv = cv.cvtColor(resized, cv.COLOR_BGR2HSV)
    image_hsv_gray = cv.cvtColor(image_hsv, cv.COLOR_BGR2GRAY)

    crown_boxes = _detect_crowns(image_hsv, image_hsv_gray, templates)

    tiles: dict[tuple[int, int], dict] = {}
    tile_summaries: list[dict] = []

    for y_coord in range(5):
        for x_coord in range(5):
            tile_x_start = x_coord * 100
            tile_y_start = y_coord * 100
            tile_x_end = (x_coord + 1) * 100
            tile_y_end = (y_coord + 1) * 100

            tile = resized[tile_y_start:tile_y_end, tile_x_start:tile_x_end]
            terrain_features = _get_terrain(tile)
            predicted_terrain = _predict_terrain(terrain_features, model, feature_cols, label_encoder)

            tile_crowns_count = 0
            for cx, cy, cw, ch in crown_boxes:
                center_x = int(cx + cw // 2)
                center_y = int(cy + ch // 2)
                if tile_x_start <= center_x < tile_x_end and tile_y_start <= center_y < tile_y_end:
                    tile_crowns_count += 1

            tile_data = {
                "terrain": predicted_terrain,
                "crowns": int(tile_crowns_count),
            }
            tiles[(x_coord, y_coord)] = tile_data
            tile_summaries.append(
                {
                    "x": x_coord,
                    "y": y_coord,
                    "terrain": predicted_terrain,
                    "crowns": int(tile_crowns_count),
                }
            )

    total_score, clusters = calculate_score(tiles)

    crown_box_list = [
        {
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
        }
        for x, y, w, h in crown_boxes
    ]

    return {
        "total_score": int(total_score),
        "tiles": tile_summaries,
        "clusters": clusters,
        "crown_boxes": crown_box_list,
        "image_size": {"width": 500, "height": 500},
    }
