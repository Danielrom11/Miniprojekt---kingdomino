from __future__ import annotations

from pathlib import Path

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from point_calculator import calculate_score

BASE_DIR = Path(__file__).resolve().parent
FIGURE_DIR = BASE_DIR / "figures"
TRAINING_EXCEL = BASE_DIR / "Trainingset" / "kingdomino_tiles_hsv_histogram_kopi.xlsx"
SAMPLE_IMAGE_CANDIDATES = [
    BASE_DIR / "Trainingset" / "1.jpg",
]
TEMPLATE_CANDIDATES = [
    # filename, template_thresh1, template_thresh2, match_threshold, edge_similarity_threshold
    (BASE_DIR / "features" / "krone_blaa_baggrund_hr.JPG", 180, 210, 0.7, 0.15),
    (BASE_DIR / "features" / "krone_blaa_baggrund_lr.JPG", 130, 150, 0.7, 0.15),
    (BASE_DIR / "features" / "krone_sort_baggrund_hr.JPG", 140, 180, 0.6, 0.15),
    (BASE_DIR / "features" / "krone_sort_baggrund_lr.JPG", 80, 110, 0.6, 0.15),
    (BASE_DIR / "features" / "krone_sort_baggrund.JPG", 140, 180, 0.6, 0.15),
]


def ensure_output_dir() -> None:
    FIGURE_DIR.mkdir(exist_ok=True)


def choose_existing_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No valid file found in: {candidates}")


def load_and_prepare_template(path: Path) -> tuple[np.ndarray | None, np.ndarray | None]:
    img_bgr = cv.imread(str(path), cv.IMREAD_COLOR)
    if img_bgr is None:
        return None, None
    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    # Match kingdomino.py behavior: grayscale projection from HSV matrix
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    return img_hsv, img_hsv_gray


def load_templates() -> list[tuple[np.ndarray, np.ndarray, int, int, float, float]]:
    templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]] = []
    for template_path, t1, t2, match_t, edge_t in TEMPLATE_CANDIDATES:
        if not template_path.exists():
            continue
        template_hsv, template_hsv_gray = load_and_prepare_template(template_path)
        if template_hsv is None or template_hsv_gray is None:
            continue
        templates.append((template_hsv, template_hsv_gray, t1, t2, match_t, edge_t))
    if not templates:
        raise FileNotFoundError("No crown templates could be loaded.")
    return templates


def train_model() -> tuple[RandomForestClassifier, list[str], LabelEncoder]:
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


def get_terrain(tile: np.ndarray, bin_size: int = 10) -> dict[str, float | int]:
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

    features = {
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


def predict_terrain(terrain_features: dict[str, float | int], model: RandomForestClassifier, feature_cols: list[str], label_encoder: LabelEncoder) -> str:
    features_df = pd.DataFrame([terrain_features])
    features_df = features_df[feature_cols]
    prediction_encoded = model.predict(features_df)
    prediction = label_encoder.inverse_transform(prediction_encoded)
    return prediction[0]


def detect_crowns(search_image_match: np.ndarray, search_image_edges: np.ndarray, templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]], search_thresh1: int = 200, search_thresh2: int = 220) -> np.ndarray:
    _, confirmed_rects = detect_crowns_debug(
        search_image_match,
        search_image_edges,
        templates,
        search_thresh1,
        search_thresh2,
    )
    return confirmed_rects


def detect_crowns_debug(
    search_image_match: np.ndarray,
    search_image_edges: np.ndarray,
    templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]],
    search_thresh1: int = 200,
    search_thresh2: int = 220,
) -> tuple[np.ndarray, np.ndarray]:
    potential_matches: list[tuple[list[int], np.ndarray, int, int, float]] = []

    for template_hsv, template_hsv_gray, t_thresh1, t_thresh2, match_thresh, edge_sim_thresh in templates:
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

    if potential_matches:
        raw_rectangles = [match[0] for match in potential_matches]
        raw_grouped, _ = cv.groupRectangles(raw_rectangles, groupThreshold=1, eps=0.5)
        if len(raw_grouped) == 0:
            raw_grouped = np.array(raw_rectangles, dtype=np.int32)
    else:
        raw_grouped = np.empty((0, 4), dtype=np.int32)

    if not confirmed_rects:
        return raw_grouped, np.empty((0, 4), dtype=np.int32)

    verified_grouped, _ = cv.groupRectangles(confirmed_rects, groupThreshold=1, eps=0.5)
    if len(verified_grouped) == 0:
        verified_grouped = np.array(confirmed_rects, dtype=np.int32)
    return raw_grouped, verified_grouped


def build_tiles(image: np.ndarray, model: RandomForestClassifier, feature_cols: list[str], label_encoder: LabelEncoder, templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]]) -> dict[tuple[int, int], dict]:
    tiles = {}

    # Match kingdomino.py: detect crowns on full image first, then assign to tiles via center point
    image_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    image_hsv_gray = cv.cvtColor(image_hsv, cv.COLOR_BGR2GRAY)
    all_crown_rects = detect_crowns(image_hsv, image_hsv_gray, templates)

    for y_coord in range(5):
        for x_coord in range(5):
            tile = image[y_coord * 100 : (y_coord + 1) * 100, x_coord * 100 : (x_coord + 1) * 100]
            terrain_features = get_terrain(tile)
            predicted_terrain = predict_terrain(terrain_features, model, feature_cols, label_encoder)

            tile_x_start = x_coord * 100
            tile_y_start = y_coord * 100
            tile_x_end = (x_coord + 1) * 100
            tile_y_end = (y_coord + 1) * 100
            tile_crowns_count = 0
            for cx, cy, cw, ch in all_crown_rects:
                center_x = cx + cw // 2
                center_y = cy + ch // 2
                if tile_x_start <= center_x < tile_x_end and tile_y_start <= center_y < tile_y_end:
                    tile_crowns_count += 1

            tiles[(x_coord, y_coord)] = {
                "tile": tile,
                "terrain_features": terrain_features,
                "terrain": predicted_terrain,
                "crowns": tile_crowns_count,
            }
    return tiles


def draw_architecture_diagram() -> None:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis("off")

    boxes = [
        (0.6, 1.3, 2.2, 1.2, "Råt billede\n(Trainingset/Testset)"),
        (3.2, 1.3, 2.2, 1.2, "Grid-opdeling\n5x5 tiles"),
        (5.8, 1.3, 2.2, 1.2, "HSV-features\n+ Random Forest"),
        (8.4, 1.3, 2.2, 1.2, "HSV-baseret\nTemplate + Canny"),
        (11.0, 1.3, 2.2, 1.2, "Flood fill\n+ clusters"),
    ]
    for x, y, w, h, label in boxes:
        rect = plt.Rectangle((x, y), w, h, fill=True, color="#eef4ff", ec="#2f4b7c", lw=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11)

    for idx in range(len(boxes) - 1):
        x, y, w, h, _ = boxes[idx]
        nx, ny, _, _, _ = boxes[idx + 1]
        ax.annotate(
            "",
            xy=(nx, y + h / 2),
            xytext=(x + w, y + h / 2),
            arrowprops=dict(arrowstyle="->", lw=2, color="#444444"),
        )

    ax.text(7, 3.4, "Overordnet systemarkitektur for King Domino pointberegneren", ha="center", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "systemarkitektur.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def draw_feature_visualization(sample_image: np.ndarray, model: RandomForestClassifier, feature_cols: list[str], label_encoder: LabelEncoder) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    axes[0].imshow(cv.cvtColor(sample_image, cv.COLOR_BGR2RGB))
    axes[0].set_title("Spilleplade opdelt i 5x5 grid")
    axes[0].axis("off")
    for i in range(6):
        axes[0].axhline(i * 100, color="white", lw=1)
        axes[0].axvline(i * 100, color="white", lw=1)
    for y in range(5):
        for x in range(5):
            axes[0].text(x * 100 + 5, y * 100 + 15, f"({x},{y})", color="white", fontsize=8, bbox=dict(facecolor="black", alpha=0.3, pad=1))

    # Samme felt vises i både HSV- og Canny-visualisering
    tile_x, tile_y = 2, 2
    tile = sample_image[tile_y * 100 : (tile_y + 1) * 100, tile_x * 100 : (tile_x + 1) * 100]
    hsv_tile = cv.cvtColor(tile, cv.COLOR_BGR2HSV)
    h_channel = hsv_tile[:, :, 0].flatten()
    s_channel = hsv_tile[:, :, 1].flatten()
    v_channel = hsv_tile[:, :, 2].flatten()

    axes[1].hist(h_channel, bins=18, alpha=0.7, label="H", color="#2ca02c")
    axes[1].hist(s_channel, bins=26, alpha=0.5, label="S", color="#1f77b4")
    axes[1].hist(v_channel, bins=26, alpha=0.5, label="V", color="#ff7f0e")
    axes[1].set_title(f"HSV-features fra felt ({tile_x},{tile_y})")
    axes[1].set_xlabel("Pixelværdi")
    axes[1].set_ylabel("Antal pixels")
    axes[1].legend()

    hsv_gray = cv.cvtColor(hsv_tile, cv.COLOR_BGR2GRAY)
    hsv_edges = cv.Canny(hsv_gray, 200, 220)
    axes[2].imshow(hsv_gray, cmap="gray")
    axes[2].imshow(hsv_edges, cmap="autumn", alpha=0.45)
    axes[2].set_title("HSV-gray + Canny\n(brugt til krone-detektion)")
    axes[2].axis("off")

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "grid_feature_visualization.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def draw_crown_visualization(sample_image: np.ndarray, templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]]) -> dict[tuple[int, int], dict]:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(cv.cvtColor(sample_image, cv.COLOR_BGR2RGB))
    ax.set_title("Lokalisering af kroner via HSV-Template Matching")
    ax.axis("off")

    image_hsv = cv.cvtColor(sample_image, cv.COLOR_BGR2HSV)
    image_hsv_gray = cv.cvtColor(image_hsv, cv.COLOR_BGR2GRAY)
    rects = detect_crowns(image_hsv, image_hsv_gray, templates)
    detected_total = len(rects)
    for rect in rects:
        x, y, w, h = rect
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=False, ec="yellow", lw=2))

    for i in range(6):
        ax.axhline(i * 100, color="white", lw=1, alpha=0.7)
        ax.axvline(i * 100, color="white", lw=1, alpha=0.7)

    ax.text(
        10,
        20,
        f"Detekterede kroner i alt: {detected_total}",
        color="white",
        fontsize=10,
        bbox=dict(facecolor="black", alpha=0.55, pad=3),
    )

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "template_matching.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {}


def draw_template_debug_comparison(sample_image: np.ndarray, templates: list[tuple[np.ndarray, np.ndarray, int, int, float, float]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    for ax in axes:
        ax.imshow(cv.cvtColor(sample_image, cv.COLOR_BGR2RGB))
        ax.axis("off")
        for i in range(6):
            ax.axhline(i * 100, color="white", lw=1, alpha=0.6)
            ax.axvline(i * 100, color="white", lw=1, alpha=0.6)

    image_hsv = cv.cvtColor(sample_image, cv.COLOR_BGR2HSV)
    image_hsv_gray = cv.cvtColor(image_hsv, cv.COLOR_BGR2GRAY)
    raw_rects, verified_rects = detect_crowns_debug(image_hsv, image_hsv_gray, templates)

    for rect in raw_rects:
        x, y, w, h = rect
        axes[0].add_patch(
            plt.Rectangle((x, y), w, h, fill=False, ec="#ff4d4d", lw=1.2)
        )
    for rect in verified_rects:
        x, y, w, h = rect
        axes[1].add_patch(
            plt.Rectangle((x, y), w, h, fill=False, ec="#00ff84", lw=1.8)
        )

    raw_count = len(raw_rects)
    verified_count = len(verified_rects)

    axes[0].set_title(f"Rå template matches (efter gruppering): {raw_count}")
    axes[1].set_title(f"Efter Canny-verifikation: {verified_count}")

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "template_matching_debug.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_cluster_visualization(tiles: dict[tuple[int, int], dict], clusters: list[dict]) -> None:
    color_map = plt.get_cmap("tab20", max(1, len(clusters)))
    cluster_lookup = {}
    for idx, cluster in enumerate(clusters):
        for coord in cluster["coordinates"]:
            cluster_lookup[tuple(coord)] = idx

    fig, ax = plt.subplots(figsize=(8, 8))
    for y in range(5):
        for x in range(5):
            cluster_idx = cluster_lookup.get((x, y), None)
            facecolor = "#f0f0f0" if cluster_idx is None else color_map(cluster_idx)
            ax.add_patch(plt.Rectangle((x, 4 - y), 1, 1, facecolor=facecolor, edgecolor="black", lw=1))
            tile = tiles.get((x, y), {})
            terrain = tile.get("terrain", "")
            crowns = tile.get("crowns", 0)
            ax.text(x + 0.5, 4 - y + 0.6, terrain, ha="center", va="center", fontsize=8)
            ax.text(x + 0.5, 4 - y + 0.28, f"K:{crowns}", ha="center", va="center", fontsize=8)

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Visualisering af clusters og samlet pointscore")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "floodfill_resultat.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ensure_output_dir()
    model, feature_cols, label_encoder = train_model()
    templates = load_templates()
    sample_image_path = choose_existing_path(SAMPLE_IMAGE_CANDIDATES)
    sample_image = cv.imread(str(sample_image_path))
    if sample_image is None:
        raise FileNotFoundError(f"Could not read sample image: {sample_image_path}")

    draw_architecture_diagram()
    draw_feature_visualization(sample_image, model, feature_cols, label_encoder)
    tiles = build_tiles(sample_image, model, feature_cols, label_encoder, templates)
    draw_crown_visualization(sample_image, templates)
    draw_template_debug_comparison(sample_image, templates)
    total_score, clusters = calculate_score(tiles)
    draw_cluster_visualization(tiles, clusters)
    print(f"Saved figures to {FIGURE_DIR}")
    print(f"Sample image: {sample_image_path.name}")
    print(f"Calculated score for figure sample: {total_score}")


if __name__ == "__main__":
    main()
