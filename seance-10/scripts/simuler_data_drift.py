"""
simuler_data_drift.py
──────────────────────
« Pour aller plus loin » du TP séance 10 : simuler le problème de Kossi (CM) —
2 nouvelles lignes ouvertes en avril, jamais vues à l'entraînement. On charge
le modèle en statut Production depuis le Model Registry, on l'évalue sur les
données d'origine (baseline) puis sur des données incluant les nouvelles
lignes (drift), et on log les deux résultats dans un run MLflow dédié pour
pouvoir les comparer dans l'UI — sans qu'aucune exception ne soit levée nulle
part : le modèle répond toujours, juste de moins en moins bien.

Usage : python scripts/simuler_data_drift.py
"""

import random

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

random.seed(2026)

LIGNES_ORIGINE = [f"L{i:02d}" for i in range(1, 13)]
LIGNES_NOUVELLES = ["L13", "L14"]  # ouvertes "en avril", absentes du jeu d'entraînement
HEURES = list(range(5, 23))
HEURES_POIDS = {
    5: 1, 6: 5, 7: 15, 8: 18, 9: 10, 10: 6, 11: 5, 12: 7,
    13: 6, 14: 5, 15: 5, 16: 8, 17: 17, 18: 18, 19: 12,
    20: 6, 21: 3, 22: 1,
}


def generer_lignes(lignes):
    rows = []
    for ligne in lignes:
        niveau_base_ligne = random.uniform(0.7, 1.4)
        for heure in HEURES:
            for _ in range(15):
                base = HEURES_POIDS[heure] * niveau_base_ligne
                bruit = random.uniform(-3, 3)
                nb_passagers = max(0, round(base * 3 + bruit))
                rows.append([ligne, heure, nb_passagers])
    return pd.DataFrame(rows, columns=["ligne_id", "heure", "nb_passagers"])


def evaluer(modele, df, label):
    X = df[["ligne_id", "heure"]]
    y = df["nb_passagers"]
    predictions = modele.predict(X)
    mae = mean_absolute_error(y, predictions)
    r2 = r2_score(y, predictions)
    print(f"[{label}] MAE={mae:.2f}  R2={r2:.3f}  (n={len(df)})")
    return mae, r2


def main():
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("anfa-prediction-affluence")

    print("[INFO] Chargement du modèle en statut Production depuis le Registry...")
    modele = mlflow.sklearn.load_model("models:/anfa-prediction-affluence/Production")

    # Baseline : mêmes 12 lignes que celles vues à l'entraînement
    df_baseline = generer_lignes(LIGNES_ORIGINE)
    mae_baseline, r2_baseline = evaluer(modele, df_baseline, "BASELINE (12 lignes connues)")

    # Drift : réseau après ouverture de 2 nouvelles lignes, jamais vues à l'entraînement
    df_drift = generer_lignes(LIGNES_ORIGINE + LIGNES_NOUVELLES)
    mae_drift, r2_drift = evaluer(modele, df_drift, "APRES OUVERTURE L13/L14 (data drift)")

    degradation_pct = (mae_drift - mae_baseline) / mae_baseline * 100

    with mlflow.start_run(run_name="monitoring-drift-ouverture-L13-L14"):
        mlflow.set_tag("type_run", "monitoring_drift")
        mlflow.set_tag("scenario", "ouverture_2_nouvelles_lignes_avril")
        mlflow.log_param("modele_evalue", "anfa-prediction-affluence/Production")
        mlflow.log_param("lignes_baseline", ",".join(LIGNES_ORIGINE))
        mlflow.log_param("lignes_nouvelles", ",".join(LIGNES_NOUVELLES))
        mlflow.log_metric("mae_baseline", mae_baseline)
        mlflow.log_metric("r2_baseline", r2_baseline)
        mlflow.log_metric("mae_apres_drift", mae_drift)
        mlflow.log_metric("r2_apres_drift", r2_drift)
        mlflow.log_metric("degradation_mae_pct", degradation_pct)

    print()
    print(f"[RESULTAT] Degradation du MAE : +{degradation_pct:.1f}% apres ouverture de "
          f"{len(LIGNES_NOUVELLES)} nouvelles lignes")
    print("[RESULTAT] Aucune exception levee : le modele repond toujours, "
          "juste de moins en moins bien (OneHotEncoder(handle_unknown='ignore') "
          "encode silencieusement L13/L14 a zero).")
    print("[OK] Run 'monitoring-drift-ouverture-L13-L14' enregistre dans MLflow.")


if __name__ == "__main__":
    main()
