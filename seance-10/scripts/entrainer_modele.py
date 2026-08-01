"""
entrainer_modele.py
────────────────────
Entraîne un modèle de prédiction d'affluence (nb_passagers) à partir
de (ligne_id, heure), en traçant l'expérimentation avec MLflow.

Usage : python entrainer_modele.py --n-estimators 50 --max-depth 5
"""

import argparse

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def main(n_estimators: int, max_depth: int):
    # ── MLflow : où envoyer les données de tracking ──
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("anfa-prediction-affluence")

    # ── Chargement des données ──
    df = pd.read_csv("dataset_affluence.csv")
    X = df[["ligne_id", "heure"]]
    y = df["nb_passagers"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=2026
    )

    # ── Un run MLflow = une expérimentation tracée de bout en bout ──
    with mlflow.start_run():

        # 1. On enregistre les PARAMÈTRES utilisés pour cette exécution
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("nb_lignes_dataset", len(df))

        # 2. Construction du modèle (encodage de ligne_id + RandomForest)
        preprocesseur = ColumnTransformer([
            ("ligne_encodee", OneHotEncoder(handle_unknown="ignore"), ["ligne_id"]),
        ], remainder="passthrough")

        modele = Pipeline([
            ("preprocesseur", preprocesseur),
            ("regresseur", RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=2026,
            )),
        ])

        modele.fit(X_train, y_train)

        # 3. Évaluation
        predictions = modele.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        # 4. On enregistre les MÉTRIQUES obtenues
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("r2_score", r2)

        # 5. On enregistre le MODÈLE lui-même comme artefact
        mlflow.sklearn.log_model(modele, "modele")

        print(f"[OK] Run terminé — MAE: {mae:.2f}, R²: {r2:.3f}")
        print(f"[INFO] n_estimators={n_estimators}, max_depth={max_depth}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", type=int, default=50)
    parser.add_argument("--max-depth", type=int, default=5)
    args = parser.parse_args()

    main(n_estimators=args.n_estimators, max_depth=args.max_depth)
