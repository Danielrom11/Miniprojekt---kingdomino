import os
import cv2 as cv
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from point_calculator import calculate_score

# Main function containing the backbone of the program
def main():
    print("+-------------------------------+")
    print("| King Domino points calculator |")
    print("+-------------------------------+")
    
    # Train the Random Forest model
    model, feature_cols, label_encoder = train_model()

    # Pre-load crown templates
    template_paths = [
        r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\kongekrone_nord.jpg",
        r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\features\kongekrone_syd.png"
    ]
    crown_templates = [cv.imread(path, cv.IMREAD_GRAYSCALE) for path in template_paths]

    # Canny edge detection thresholds
    search_thresh1 = 150
    search_thresh2 = 180
    template_thresh1 = 185
    template_thresh2 = 200

    image_path = r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Trainingset\7.jpg"
    if not os.path.isfile(image_path):
        print("Image not found")
        return

    image = cv.imread(image_path)
    tiles = get_tiles(image, model, feature_cols, label_encoder, crown_templates, search_thresh1, search_thresh2, template_thresh1, template_thresh2)
    print(len(tiles))
    # Sort the tiles by their (y, x) coordinates before printing
    for (x, y), tile_data in sorted(tiles.items(), key=lambda item: (item[0][1], item[0][0])):
        print(f"Tile ({x}, {y}):")
        print(f"  Predicted Terrain: {tile_data['terrain']}")
        print(f"  Crowns: {tile_data['crowns']}")
        print("=====")

     # Kør pointberegneren på den genererede tiles dict!
    final_score, clusters = calculate_score(tiles)
    print(f"\n======== RESULTAT ========")
    print(f"Billedets samlede score: {final_score}")
    print(f"==========================\n")
    
    print("\n======== DETALJERET REGNSKAB ========")
    for i, cluster in enumerate(clusters, 1):
        print(f"Område {i}: {cluster['terrain']}")
        print(f"  Felter i alt: {cluster['tiles_count']}, Kroner i alt: {cluster['crowns_count']} => {cluster['score']} Point")
        print(f"  Består af koordinaterne: {cluster['coordinates']}")
        print("---------------------------------------")
    print("=====================================\n")
    
    # Sort the tiles by their (y, x) coordinates before printing
    for (x, y), tile_data in sorted(tiles.items(), key=lambda item: (item[0][1], item[0][0])):
        print(f"Tile ({x}, {y}):")
        print(f"  Predicted Terrain: {tile_data['terrain']}")
        print(f"  Crowns: {tile_data['crowns']}")
        print("=====")

def train_model():
    # Load the training data
    training_path = r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Trainingset\kingdomino_tiles_hsv_histogram_kopi.xlsx"
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
def get_tiles(image, model, feature_cols, label_encoder, crown_templates, search_thresh1, search_thresh2, template_thresh1, template_thresh2):
    tiles = {}
    for y_coord in range(5):
        for x_coord in range(5):
            try:
                tile = image[y_coord * 100 : (y_coord + 1) * 100, x_coord * 100 : (x_coord + 1) * 100]
                terrain_features = get_terrain(tile)
                predicted_terrain = predict_terrain(terrain_features, model, feature_cols, label_encoder)
                
                crown_crop_img = crop_tile_center(tile)
                num_crowns = detect_crowns(crown_crop_img, crown_templates, search_thresh1, search_thresh2, template_thresh1, template_thresh2)

                tiles[(x_coord, y_coord)] = {
                    "tile": tile,
                    "crown_crop": crown_crop_img,
                    "terrain_features": terrain_features,
                    "terrain": predicted_terrain,
                    "crowns": num_crowns,
                }
            except Exception as e:
                print(f"An unexpected error occurred processing tile ({x_coord}, {y_coord}): {e}")
    return tiles

def crop_tile_center(tile, box_size=30):
    tile_height, tile_width = tile.shape[:2]
    hole_height = min(tile_height, max(1, int(box_size)))
    hole_width = min(tile_width, max(1, int(box_size)))
    start_y = (tile_height - hole_height) // 2
    start_x = (tile_width - hole_width) // 2

    masked_tile = tile.copy()
    masked_tile[start_y : start_y + hole_height, start_x : start_x + hole_width] = 0
    
    # Return only the blue channel of the masked tile
    return cv.split(masked_tile)[0]

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

def detect_crowns(search_image, templates, search_thresh1, search_thresh2, template_thresh1, template_thresh2):
    """
    Detects crowns using template matching and verifies with Canny edge comparison.
    """
    potential_matches = []
    template_matching_threshold = 0.7  # Initial threshold for finding potential crowns

    # --- Step 1: Initial Template Matching ---
    for original_template in templates:
        if original_template is None:
            continue

        for scale in np.linspace(0.8, 0.2, 25):
            resized_w = int(original_template.shape[1] * scale)
            resized_h = int(original_template.shape[0] * scale)
            if resized_w < 15 or resized_h < 15:
                continue
            
            resized_t = cv.resize(original_template, (resized_w, resized_h))
            
            for angle in [0, 90, 180, 270]:
                if angle == 0:
                    curr_t = resized_t
                elif angle == 90:
                    curr_t = cv.rotate(resized_t, cv.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    curr_t = cv.rotate(resized_t, cv.ROTATE_180)
                elif angle == 270:
                    curr_t = cv.rotate(resized_t, cv.ROTATE_90_COUNTERCLOCKWISE)
                
                # Match on the original grayscale images
                res = cv.matchTemplate(search_image, curr_t, cv.TM_CCOEFF_NORMED)
                loc = np.where(res >= template_matching_threshold)
                
                h, w = curr_t.shape
                for pt in zip(*loc[::-1]):
                    # Store the potential match rectangle and the template used
                    potential_matches.append(([int(pt[0]), int(pt[1]), int(w), int(h)], curr_t))

    # --- Step 2: Verification with Canny Edge Matching ---
    confirmed_rects = []
    edge_similarity_threshold = 0.15  # Threshold for the edge comparison step

    search_edges = cv.Canny(search_image, search_thresh1, search_thresh2)

    for rect, template in potential_matches:
        x, y, w, h = rect
        
        # Get the region of interest (ROI) from the search image's edges
        roi_edges = search_edges[y:y+h, x:x+w]
        
        # Get the edges of the template that made the match
        template_edges = cv.Canny(template, template_thresh1, template_thresh2)
        
        # Ensure template_edges is not larger than roi_edges
        if template_edges.shape[0] > roi_edges.shape[0] or template_edges.shape[1] > roi_edges.shape[1]:
            continue

        # Compare the ROI edges with the template edges
        edge_res = cv.matchTemplate(roi_edges, template_edges, cv.TM_CCOEFF_NORMED)
        
        # If the edges are a good match, confirm the detection
        if np.max(edge_res) >= edge_similarity_threshold:
            confirmed_rects.append(rect)

    # Group the confirmed rectangles to merge overlapping boxes
    rects, _ = cv.groupRectangles(confirmed_rects, groupThreshold=1, eps=0.5)
    
    return len(rects)


if __name__ == "__main__":
    main()