"""
generer_dataset_affluence.py
─────────────────────────────
Génère un petit jeu de données synthétique : pour chaque (ligne, heure),
le nombre de passagers observé. Sert à entraîner un modèle de prédiction
d'affluence par ligne et par heure — la situation-problème du CM (Kossi).
"""

import csv
import random

random.seed(2026)

LIGNES = [f"L{i:02d}" for i in range(1, 13)]
HEURES = list(range(5, 23))

# Poids réalistes (mêmes heures de pointe que les séances précédentes)
HEURES_POIDS = {
    5: 1, 6: 5, 7: 15, 8: 18, 9: 10, 10: 6, 11: 5, 12: 7,
    13: 6, 14: 5, 15: 5, 16: 8, 17: 17, 18: 18, 19: 12,
    20: 6, 21: 3, 22: 1,
}


def main():
    with open("dataset_affluence.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ligne_id", "heure", "nb_passagers"])

        for ligne in LIGNES:
            # Chaque ligne a un "niveau de base" différent (certaines lignes
            # sont structurellement plus fréquentées que d'autres)
            niveau_base_ligne = random.uniform(0.7, 1.4)

            for heure in HEURES:
                # On génère plusieurs observations par (ligne, heure) pour avoir
                # un jeu de données de taille raisonnable
                for _ in range(15):
                    base = HEURES_POIDS[heure] * niveau_base_ligne
                    bruit = random.uniform(-3, 3)
                    nb_passagers = max(0, round(base * 3 + bruit))
                    writer.writerow([ligne, heure, nb_passagers])

    print("[OK] dataset_affluence.csv généré.")


if __name__ == "__main__":
    main()
