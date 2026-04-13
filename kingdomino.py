import os

import cv2 as cv
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Main function containing the backbone of the program
def main():
    print("+-------------------------------+")
    print("| King Domino points calculator |")
    print("+-------------------------------+")
    
    # Train the Random Forest model
    model, feature_cols, label_encoder = train_model()

    image_path = r"C:\Users\danie\Desktop\2. semester\Miniprojekt - kingdomino\Trainingset\1.jpg"
    if not os.path.isfile(image_path):
        print("Image not found")
        return

    image = cv.imread(image_path)
    tiles = get_tiles(image, model, feature_cols, label_encoder)
    print(len(tiles))
    for (x, y), tile_data in tiles.items():
        print(f"Tile ({x}, {y}):")
        print(f"  Predicted Terrain: {tile_data['terrain']}")
        # print(tile_data["terrain_features"])
        print(f"  Crown crop shape: {tile_data['crown_crop'].shape}")
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
    model = RandomForestClassifier(random_state=42, n_estimators=200, max_depth=None, min_samples_split=5)
    model.fit(X, y_encoded)

    return model, feature_cols, label_encoder

# Break a board into tiles
def get_tiles(image, model, feature_cols, label_encoder):
    tiles = {}
    for y in range(5):
        for x in range(5):
            tile = image[y * 100 : (y + 1) * 100, x * 100 : (x + 1) * 100]
            terrain_features = get_terrain(tile)
            predicted_terrain = predict_terrain(terrain_features, model, feature_cols, label_encoder)
            tiles[(x, y)] = {
                "tile": tile,
                "crown_crop": crop_tile_center(tile),
                "terrain_features": terrain_features,
                "terrain": predicted_terrain,
                "crowns": None,
            }
    return tiles

def crop_tile_center(tile, box_size=35):
    tile_height, tile_width = tile.shape[:2]
    hole_height = min(tile_height, max(1, int(box_size)))
    hole_width = min(tile_width, max(1, int(box_size)))
    start_y = (tile_height - hole_height) // 2
    start_x = (tile_width - hole_width) // 2

    masked_tile = tile.copy()
    masked_tile[start_y : start_y + hole_height, start_x : start_x + hole_width] = 0
    return masked_tile

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


if __name__ == "__main__":
    main()