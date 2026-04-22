import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 1. Define the path to your Excel file
file_path = r"G:\Andre computere\My laptop\Desktop\2. semester\Miniprojekt - kingdomino 1\Miniprojekt - kingdomino\Results\Test_resultater.xlsx"

print("Loading data...")
# Read the Excel file, skipping the very first row (header=1) so it starts at "Billede, tile, Ground truth..."
df = pd.read_excel(file_path, header=1, engine='openpyxl')

# ==========================================
# PART A: TERRAIN PREDICTIONS
# ==========================================
# Extract the relevant columns by POSITION
terrain_data = pd.DataFrame({
    'Ground Truth': df.iloc[:, 2],
    'Predictions': df.iloc[:, 3]
}).dropna()

# Clean the data (Lowercase and strip spaces)
y_true = terrain_data['Ground Truth'].astype(str).str.lower().str.strip()
y_pred = terrain_data['Predictions'].astype(str).str.lower().str.strip()

# Calculate Basic Accuracy
accuracy = accuracy_score(y_true, y_pred)
total_tiles = len(y_true)

print("\n" + "="*40)
print(f" TERRAIN ANALYSIS")
print("="*40)
print(f" TOTAL TILES ANALYZED: {total_tiles}")
print(f" OVERALL ACCURACY:     {accuracy:.2%}")
print("\nDetailed Report (Precision, Recall, F1-Score):")
print(classification_report(y_true, y_pred, zero_division=0))

# Plot Terrain Confusion Matrix
labels = sorted(y_true.unique())
cm = confusion_matrix(y_true, y_pred, labels=labels)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.title(f'Terrain Type Confusion Matrix (n={total_tiles})')
plt.xlabel('Predicted Terrain')
plt.ylabel('Actual Terrain (Ground Truth)')
plt.tight_layout()
plt.show()

# ==========================================
# PART B: SCORE CALCULATIONS ANALYSIS
# ==========================================
print("\n" + "="*40)
print(" SCORE ANALYSIS")
print("="*40)

# Extract the Score columns (Position 6 for True, Position 7 for Pred)
score_data = pd.DataFrame({
    'Ground Truth': df.iloc[:, 6],
    'Predictions': df.iloc[:, 7]
}).dropna()

# Ensure the data is numeric (ignores any accidental text/spaces)
scores_true = pd.to_numeric(score_data['Ground Truth'], errors='coerce').dropna()
scores_pred = pd.to_numeric(score_data['Predictions'], errors='coerce').dropna()

# Calculate metrics
total_scores = len(scores_true)
if total_scores > 0:
    mae = mean_absolute_error(scores_true, scores_pred)
    rmse = np.sqrt(mean_squared_error(scores_true, scores_pred))
    r2 = r2_score(scores_true, scores_pred)
    
    # Calculate exact matches (How many games had the PERFECT score calculated)
    exact_matches = (scores_true == scores_pred).sum()
    exact_match_acc = exact_matches / total_scores

    print(f" TOTAL BOARDS SCORED:  {total_scores}")
    print(f" EXACT MATCH ACCURACY: {exact_match_acc:.2%} ({exact_matches}/{total_scores} perfect scores)")
    print(f" MEAN ABSOLUTE ERROR:  {mae:.2f} points off on average")
    print(f" ROOT MEAN SQ ERROR:   {rmse:.2f} points")
    print(f" R-SQUARED (R²):       {r2:.4f}")

    # Calculate residuals (Difference between predicted and true)
    # A positive residual means the model over-predicted the score
    # A negative residual means the model under-predicted the score
    residuals = scores_pred - scores_true

    # Plot 1: True vs Predicted Scatter & Plot 2: Residuals Histogram
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Subplot 1: Actual vs Predicted ---
    ax1.scatter(scores_true, scores_pred, alpha=0.7, color='purple', edgecolors='k')
    
    # Draw the "Perfect Prediction" diagonal line
    max_val = max(scores_true.max(), scores_pred.max()) + 5
    ax1.plot([0, max_val], [0, max_val], 'r--', label='Perfect Prediction')
    
    ax1.set_title('Actual vs. Predicted Scores')
    ax1.set_xlabel('Actual Score (Ground Truth)')
    ax1.set_ylabel('Predicted Score')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- Subplot 2: Residuals Distribution ---
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