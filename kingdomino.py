import os
import cv2 as cv
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from point_calculator import calculate_score

def load_and_prepare_template(path):
    """
    Loads a color template, converts to HSV, and returns both the full HSV and the HSV grayscale.
    """
    img_bgr = cv.imread(path, cv.IMREAD_COLOR)
    if img_bgr is None:
        print(f"Warning: Could not load template at {path}")
        return None, None
    
    # Convert the image to HSV color space
    img_hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    
    # Create a grayscale representation of the raw HSV matrix for Canny edges
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    return img_hsv, img_hsv_gray

def build_crown_templates(features_dir, template_count=18):
    """
    Loads konge_krone_1..N templates and attaches shared thresholds used by
    template matching and Canny edge verification.
    """
    # Shared thresholds for all konge_krone templates
    template_thresh1 = 140
    template_thresh2 = 180
    match_threshold = 0.65
    edge_sim_threshold = 0.15

    crown_templates = []
    for idx in range(1, template_count + 1):
        template_path = os.path.join(features_dir, f"konge_krone_{idx}.JPG")
        if not os.path.isfile(template_path):
            # Fallback if extension casing differs on disk
            template_path = os.path.join(features_dir, f"konge_krone_{idx}.jpg")

        template_hsv, template_hsv_gray = load_and_prepare_template(template_path)
        if template_hsv is None or template_hsv_gray is None:
            continue

        crown_templates.append(
            (
                template_hsv,
                template_hsv_gray,
                template_thresh1,
                template_thresh2,
                match_threshold,
                edge_sim_threshold,
            )
        )

    print(f"Loaded {len(crown_templates)} crown templates for matching.")
    return crown_templates

# Main function containing the backbone of the program
def main():
    print("+-------------------------------+")
    print("| King Domino points calculator |")
    print("+-------------------------------+")
    
    # Train the Random Forest model
    model, feature_cols, label_encoder = train_model()

    # Pre-load all konge_krone templates (1..18) used by template matching and Canny verification
    features_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features")
    crown_templates = build_crown_templates(features_dir, template_count=18)
    if not crown_templates:
        print("No crown templates were loaded. Check the files in features/.")
        return

    # Canny edge detection thresholds for the search image
    search_thresh1 = 200
    search_thresh2 = 220

    image_path = r"C:\Users\olive\Documents\GitHub\KingdominoMiniprojekt2mandsgruppe\Miniprojekt---kingdomino\Trainingset\18.jpg"
    if not os.path.isfile(image_path):
        print("Image not found")
        return

    image = cv.imread(image_path)
    tiles = get_tiles(image, model, feature_cols, label_encoder, crown_templates, search_thresh1, search_thresh2)
    
    # Kør pointberegneren på den genererede tiles dict!
    final_score, clusters = calculate_score(tiles)
    
    # Print all results
    print_results(tiles, final_score, clusters)

def print_results(tiles, final_score, clusters):
    """Prints the final results, including tile details, total score, and cluster breakdown."""
    print("\n======== TILE DETALJER ========")
    # Sort the tiles by their (y, x) coordinates before printing
    for (x, y), tile_data in sorted(tiles.items(), key=lambda item: (item[0][1], item[0][0])):
        print(f"Tile ({x}, {y}):")
        print(f"  Predicted Terrain: {tile_data['terrain']}")
        print(f"  Crowns: {tile_data['crowns']}")
        print("=====")

    print(f"\n======== RESULTAT ========")
    print(f"Billedets samlede score: {final_score}")
    print(f"==========================\n")
    
    print("\n======== DETALJERET REGNSKAB ========")
    for i, cluster in enumerate(clusters, 1):
        print(f"Område {i}: {cluster['terrain']}")
        print(f"  Felter i alt: {cluster['tiles_count']}, Kroner i alt: {cluster['crowns_count']} => {cluster['score']} Point")
        print(f"  Består af koordinaterne: {cluster['coordinates']}")
        print("---------------------------------------")
    print("=====================================\n============================\n")

def train_model():
    # Load the training data
    training_path = r"C:\Users\olive\Documents\GitHub\KingdominoMiniprojekt2mandsgruppe\Miniprojekt---kingdomino\Trainingset\kingdomino_tiles_hsv_histogram_kopi.xlsx"
    df = pd.read_excel(training_path)
    df = df[df["Manual_Label"].notna()].copy()

    # Define feature columns
    metadata_cols = ["Reference", "Image", "Tile_X", "Tile_Y", "Predicted_Terrain"]
    target_col = "Manual_Label"
    feature_cols = [
        col for col in df.columns 
        if col not in metadata_cols + [target_col] and 
        (col.startswith(("H_Bin", "S_Bin", "V_Bin")) or col in ["H_Median", "S_Median", "V_Median"])
    ]

    # Prepare data for training
    X = df[feature_cols].fillna(df[feature_cols].median(numeric_only=True))
    y = df[target_col].astype(str)

    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # Initialize and train the model
    model = RandomForestClassifier(random_state=42, n_estimators=100, max_depth=None, min_samples_split=10)
    model.fit(X, y_encoded)

    return model, feature_cols, label_encoder

# Break a board into tiles
def get_tiles(image, model, feature_cols, label_encoder, crown_templates, search_thresh1, search_thresh2):
    tiles = {}
    
    # 1. Detect ALL crowns on the full image first to avoid boundary cut-offs
    img_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    img_hsv_gray = cv.cvtColor(img_hsv, cv.COLOR_BGR2GRAY)
    
    search_image_match = img_hsv
    search_image_edges = img_hsv_gray
    
    all_crown_rects = detect_crowns(search_image_match, search_image_edges, crown_templates, search_thresh1, search_thresh2)
    
    for y_coord in range(5):
        for x_coord in range(5):
            try:
                tile_x_start = x_coord * 100
                tile_y_start = y_coord * 100
                tile_x_end = (x_coord + 1) * 100
                tile_y_end = (y_coord + 1) * 100
                
                tile = image[tile_y_start:tile_y_end, tile_x_start:tile_x_end]
                terrain_features = get_terrain(tile)
                predicted_terrain = predict_terrain(terrain_features, model, feature_cols, label_encoder)
                
                # 2. Check which crowns belong to this specific tile based on their center coordinates
                tile_crowns_count = 0
                for (cx, cy, cw, ch) in all_crown_rects:
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
            except Exception as e:
                print(f"An unexpected error occurred processing tile ({x_coord}, {y_coord}): {e}")
    return tiles

# Determine the type of terrain in a tile
def get_terrain(tile, bin_size=10):
    hsv_tile = cv.cvtColor(tile, cv.COLOR_BGR2HSV)
    
    # Extract H, S, V channels
    h_channel = hsv_tile[:, :, 0].flatten()
    s_channel = hsv_tile[:, :, 1].flatten()
    v_channel = hsv_tile[:, :, 2].flatten()

    # Get median HSV values
    hue, saturation, value = np.median(hsv_tile, axis=(0, 1))

    # Create histogram bins
    h_bins = np.arange(0, 190, bin_size)
    s_bins = np.arange(0, 260, bin_size)
    v_bins = np.arange(0, 260, bin_size)

    h_hist, _ = np.histogram(h_channel, bins=h_bins)
    s_hist, _ = np.histogram(s_channel, bins=s_bins)
    v_hist, _ = np.histogram(v_channel, bins=v_bins)

    # Create a dictionary to store all features
    features = {
        'H_Median': round(hue, 2),
        'S_Median': round(saturation, 2),
        'V_Median': round(value, 2),
    }

    # Add H histogram bins
    for i, h_count in enumerate(h_hist):
        bin_range = i * 10
        features[f'H_Bin_{bin_range}-{bin_range+10}'] = int(h_count)

    # Add S histogram bins
    for i, s_count in enumerate(s_hist):
        bin_range = i * 10
        bin_end = bin_range + 10 if i < len(s_hist) - 1 else 255
        features[f'S_Bin_{bin_range}-{bin_end}'] = int(s_count)

    # Add V histogram bins
    for i, v_count in enumerate(v_hist):
        bin_range = i * 10
        bin_end = bin_range + 10 if i < len(v_hist) - 1 else 255
        features[f'V_Bin_{bin_range}-{bin_end}'] = int(v_count)

    return features

def predict_terrain(terrain_features, model, feature_cols, label_encoder):
    # Create a DataFrame from the features
    # Ensure the order of columns matches the training data
    features_df = pd.DataFrame([terrain_features])
    features_df = features_df[feature_cols]

    # Predict the terrain type
    prediction_encoded = model.predict(features_df)
    prediction = label_encoder.inverse_transform(prediction_encoded)
    return prediction[0]

def detect_crowns(search_image_match, search_image_edges, templates_with_thresholds, search_thresh1, search_thresh2):
    """
    Detects crowns using template matching and verifies with Canny edge comparison.
    """
    potential_matches = []

    # --- Step 1: Initial Template Matching ---
    for template_data in templates_with_thresholds:
        template_hsv, template_hsv_gray, t_thresh1, t_thresh2, match_thresh, edge_sim_thresh = template_data
        if template_hsv is None:
            continue

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
                elif angle == 270:
                    curr_t_hsv = cv.rotate(resized_t_hsv, cv.ROTATE_90_COUNTERCLOCKWISE)
                    curr_t_gray = cv.rotate(resized_t_gray, cv.ROTATE_90_COUNTERCLOCKWISE)
                
                # Match on the HSV images
                res = cv.matchTemplate(search_image_match, curr_t_hsv, cv.TM_CCOEFF_NORMED)
                loc = np.where(res >= match_thresh)
                
                h, w = curr_t_gray.shape[:2]
                for pt in zip(*loc[::-1]):
                    # Store the potential match rectangle, the *gray* template used, and its specific thresholds
                    potential_matches.append(([int(pt[0]), int(pt[1]), int(w), int(h)], curr_t_gray, t_thresh1, t_thresh2, edge_sim_thresh))

    # --- Step 2: Verification with Canny Edge Matching ---
    confirmed_rects = []

    search_edges = cv.Canny(search_image_edges, search_thresh1, search_thresh2)

    for rect, template_gray, t_thresh1, t_thresh2, edge_sim_thresh in potential_matches:
        x, y, w, h = rect
        
        # Get the region of interest (ROI) from the search image's edges
        roi_edges = search_edges[y:y+h, x:x+w]
        
        # Get the edges of the template that made the match
        template_edges = cv.Canny(template_gray, t_thresh1, t_thresh2)
        
        # Ensure template_edges is not larger than roi_edges
        if template_edges.shape[0] > roi_edges.shape[0] or template_edges.shape[1] > roi_edges.shape[1]:
            continue

        # Compare the ROI edges with the template edges
        edge_res = cv.matchTemplate(roi_edges, template_edges, cv.TM_CCOEFF_NORMED)
        
        # If the edges are a good match, confirm the detection
        if np.max(edge_res) >= edge_sim_thresh:
            confirmed_rects.append(rect)

    # Group the confirmed rectangles to merge overlapping boxes
    rects, _ = cv.groupRectangles(confirmed_rects, groupThreshold=1, eps=0.5)
    
    return rects


if __name__ == "__main__":
    main()