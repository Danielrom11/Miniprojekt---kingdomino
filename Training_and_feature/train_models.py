from pathlib import Path
import warnings

import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC


warnings.filterwarnings("ignore")


def main():
    data_path = Path(__file__).resolve().parent.parent / "Trainingset" / "kingdomino_tiles_hsv_histogram_kopi.xlsx"
    print(f"Loading dataset from: {data_path}")

    df = pd.read_excel(data_path)
    df = df[df["Manual_Label"].notna()].copy()

    metadata_cols = ["Reference", "Image", "Tile_X", "Tile_Y", "Predicted_Terrain"]
    target_col = "Manual_Label"

    feature_cols = [
        col
        for col in df.columns
        if col not in metadata_cols + [target_col]
        and (col.startswith(("H_Bin", "S_Bin", "V_Bin")) or col in ["H_Median", "S_Median", "V_Median"])
    ]

    if not feature_cols:
        raise ValueError("No feature columns found.")

    X = df[feature_cols].fillna(df[feature_cols].median(numeric_only=True))
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df[target_col].astype(str))

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    n_classes = len(pd.unique(y))
    xgb_objective = "multi:softprob" if n_classes > 2 else "binary:logistic"
    xgb_eval_metric = "mlogloss" if n_classes > 2 else "logloss"

    models = {
        "Random Forest": (
            RandomForestClassifier(random_state=42),
            {
                "n_estimators": [100, 200, 300, 400, 500],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10],
            },
        ),
        "SVC": (
            make_pipeline(StandardScaler(), SVC()),
            {
                "svc__C": [0.5, 1.0, 2.0],
                "svc__gamma": ["scale", "auto"],
                "svc__kernel": ["rbf", "linear", "poly"],
            },
        ),
        "XGBoost": (
            xgb.XGBClassifier(
                random_state=42,
                objective=xgb_objective,
                eval_metric=xgb_eval_metric,
                n_jobs=-1,
                tree_method="hist",
            ),
            {
                "n_estimators": [100, 200, 300, 400, 500],
                "max_depth": [4, 6, 8, 10],
                "learning_rate": [0.05, 0.1, 0.15],
                "subsample": [0.8],
                "colsample_bytree": [0.8],
            },
        ),
    }

    results = []

    for name, (model, param_grid) in models.items():
        print("\n" + "=" * 70)
        print(f"TRAINING {name}")
        print("=" * 70)

        search = GridSearchCV(
            model,
            param_grid=param_grid,
            cv=3,
            scoring="accuracy",
            n_jobs=-1,
        )
        search.fit(X_train, y_train)

        best_model = search.best_estimator_
        train_pred = best_model.predict(X_train)
        test_pred = best_model.predict(X_test)

        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)

        print(f"Best params: {search.best_params_}")
        print(f"Training accuracy: {train_acc:.4f}")
        print(f"Testing accuracy: {test_acc:.4f}")
        print("\nClassification report (test set):")
        print(
            classification_report(
                y_test,
                test_pred,
                labels=list(range(len(label_encoder.classes_))),
                target_names=label_encoder.classes_,
                digits=4,
                zero_division=0,
            )
        )

        results.append((name, train_acc, test_acc))

    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)
    comparison = pd.DataFrame(results, columns=["Model", "Train Accuracy", "Test Accuracy"])
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
