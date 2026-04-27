import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Set to True to run only the score analysis section.
RUN_ONLY_SCORES = True

# 1. Define the path to your Excel file
file_path = r"G:\Andre computere\My laptop\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Results\Test_resultater.xlsx"

print("Loading data...")
# Read the Excel file, skipping the very first row (header=1)
df = pd.read_excel(file_path, header=1, engine='openpyxl')

# ==========================================
# PART A: TERRAIN PREDICTIONS
# ==========================================
if not RUN_ONLY_SCORES:
    # Extract the relevant columns by POSITION (Col 3 and 4)
    terrain_data = pd.DataFrame({
        'Ground Truth': df.iloc[:, 2],
        'Predictions': df.iloc[:, 3]
    }).dropna()

    y_true_terrain = terrain_data['Ground Truth'].astype(str).str.lower().str.strip()
    y_pred_terrain = terrain_data['Predictions'].astype(str).str.lower().str.strip()

    accuracy_terrain = accuracy_score(y_true_terrain, y_pred_terrain)
    total_tiles_terrain = len(y_true_terrain)

    print("\n" + "="*40)
    print(" PART A: TERRAIN ANALYSIS")
    print("="*40)
    print(f" TOTAL TILES ANALYZED: {total_tiles_terrain}")
    print(f" OVERALL ACCURACY:     {accuracy_terrain:.2%}")
    print("\nDetailed Report (Precision, Recall, F1-Score):")
    print(classification_report(y_true_terrain, y_pred_terrain, zero_division=0))

    labels_terrain = sorted(y_true_terrain.unique())
    cm_terrain = confusion_matrix(y_true_terrain, y_pred_terrain, labels=labels_terrain)

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm_terrain, annot=True, fmt='d', cmap='Blues', xticklabels=labels_terrain, yticklabels=labels_terrain)
    plt.title(f'Terrain Type Confusion Matrix (n={total_tiles_terrain})')
    plt.xlabel('Predicted Terrain')
    plt.ylabel('Actual Terrain (Ground Truth)')
    plt.tight_layout()
    plt.show()

# ==========================================
# PART B: SCORE CALCULATIONS ANALYSIS
# ==========================================
print("\n" + "="*40)
print(" PART B: SCORE ANALYSIS")
print("="*40)

# Extract the Score columns (Position 7 and 8)
score_data = pd.DataFrame({
    'Ground Truth': df.iloc[:, 6],
    'Predictions': df.iloc[:, 7]
}).dropna()

scores_true = pd.to_numeric(score_data['Ground Truth'], errors='coerce').dropna()
scores_pred = pd.to_numeric(score_data['Predictions'], errors='coerce').dropna()

total_scores = len(scores_true)
if total_scores > 0:
    mae_score = mean_absolute_error(scores_true, scores_pred)
    rmse_score = np.sqrt(mean_squared_error(scores_true, scores_pred))
    r2_score_val = r2_score(scores_true, scores_pred)
    
    exact_matches_score = (scores_true == scores_pred).sum()
    exact_match_acc_score = exact_matches_score / total_scores

    print(f" TOTAL BOARDS SCORED:  {total_scores}")
    print(f" EXACT MATCH ACCURACY: {exact_match_acc_score:.2%} ({exact_matches_score}/{total_scores} perfect scores)")
    print(f" MEAN ABSOLUTE ERROR:  {mae_score:.2f} points off on average")
    print(f" ROOT MEAN SQ ERROR:   {rmse_score:.2f} points")
    print(f" R-SQUARED (R²):       {r2_score_val:.4f}")

    residuals = scores_pred - scores_true

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    ax1.scatter(scores_true, scores_pred, alpha=0.7, color='purple', edgecolors='k')
    max_val = max(scores_true.max(), scores_pred.max()) + 5
    ax1.plot([0, max_val], [0, max_val], 'r--', label='Perfect Prediction')
    ax1.set_title('Actual vs. Predicted Scores')
    ax1.set_xlabel('Actual Score (Ground Truth)')
    ax1.set_ylabel('Predicted Score')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)

    sns.histplot(residuals, bins=15, kde=True, color='teal', ax=ax2)
    ax2.axvline(0, color='red', linestyle='--', label='Zero Error')
    ax2.set_title('Residuals Distribution (Predicted - Actual)')
    ax2.set_xlabel('Score Difference (Residual)')
    ax2.set_ylabel('Frequency (Number of Boards)')
    ax2.legend()

    plt.tight_layout()
    plt.show()
else:
    print("No valid numeric score data found to analyze.")

# ==========================================
# PART C: CROWN DETECTION ANALYSIS
# ==========================================
if not RUN_ONLY_SCORES:
    print("\n" + "="*40)
    print(" PART C: CROWN DETECTION ANALYSIS")
    print("="*40)

    # Extract the Crown columns (Position 12 and 13)
    crown_data = pd.DataFrame({
        'Ground Truth': df.iloc[:, 11],
        'Predictions': df.iloc[:, 12]
    }).dropna()

    # Convert crowns to integers (it handles them effectively as classes but also math values)
    crowns_true = pd.to_numeric(crown_data['Ground Truth'], errors='coerce').dropna().astype(int)
    crowns_pred = pd.to_numeric(crown_data['Predictions'], errors='coerce').dropna().astype(int)

    total_crown_tiles = len(crowns_true)

    if total_crown_tiles > 0:
        # Math metrics
        mae_crowns = mean_absolute_error(crowns_true, crowns_pred)
        accuracy_crowns = accuracy_score(crowns_true, crowns_pred)

        print(f" TOTAL TILES ANALYZED: {total_crown_tiles}")
        print(f" EXACT CROWN ACCURACY: {accuracy_crowns:.2%}")
        print(f" MEAN ABSOLUTE ERROR:  {mae_crowns:.4f} crowns off on average")
        
        print("\nDetailed Report (Precision, Recall, F1-Score):")
        # zero_division=0 prevents warnings if the model completely misses a rare 2-crown or 3-crown tile
        print(classification_report(crowns_true, crowns_pred, zero_division=0))

        # Confusion Matrix for Crowns
        labels_crowns = sorted(list(set(crowns_true) | set(crowns_pred)))
        cm_crowns = confusion_matrix(crowns_true, crowns_pred, labels=labels_crowns)

        plt.figure(figsize=(6, 5))
        sns.heatmap(cm_crowns, annot=True, fmt='d', cmap='Oranges', xticklabels=labels_crowns, yticklabels=labels_crowns)
        plt.title(f'Crown Detection Confusion Matrix (n={total_crown_tiles})')
        plt.xlabel('Predicted Crowns')
        plt.ylabel('Actual Crowns (Ground Truth)')
        plt.tight_layout()
        plt.show()
    else:
        print("No valid numeric crown data found to analyze.")