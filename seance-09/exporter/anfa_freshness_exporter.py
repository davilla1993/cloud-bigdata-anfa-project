"""
anfa_freshness_exporter.py
───────────────────────────
Simule le pipeline Anfa et expose une métrique Prometheus :
l'horodatage du dernier traitement réussi.

En conditions réelles, cette métrique serait mise à jour par la tâche
"verifier_resultats" du DAG Airflow (S6), à chaque exécution réussie.
Ici, on simule un traitement toutes les 30 secondes.

SIMULATION DE PANNE
───────────────────
Le processus continue de tourner et d'exposer /metrics, mais si le fichier
sentinelle /tmp/anfa_en_panne existe, le "pipeline" ne réussit plus : on
ARRÊTE de mettre l'horodatage à jour. La métrique reste donc exposée mais se
fige, et la fraîcheur (time() - horodatage) grimpe sans jamais redescendre —
exactement le symptôme d'un pipeline silencieusement en panne (cf. CM, Awa).

C'est plus réaliste qu'un `docker stop` : dans la vraie vie, le processus
exportateur reste vivant ; c'est le *traitement* qui cesse de réussir. Si on
tuait le conteneur, Prometheus perdrait la cible (série absente) au lieu de
voir la fraîcheur monter.
"""

import os
import time
from prometheus_client import start_http_server, Gauge

# Gauge = un indicateur qui peut monter ou descendre (contrairement à un compteur).
# Ici : l'horodatage Unix (nombre de secondes depuis 1970) du dernier succès.
dernier_traitement = Gauge(
    "anfa_dernier_traitement_timestamp",
    "Horodatage Unix du dernier traitement Anfa réussi",
)

INTERVALLE_SECONDES = 30              # le "pipeline" simulé tourne toutes les 30 secondes
FICHIER_PANNE = "/tmp/anfa_en_panne"  # sentinelle : s'il existe, le pipeline ne réussit plus


def pipeline_en_panne() -> bool:
    """Le pipeline est 'en panne' tant que le fichier sentinelle existe."""
    return os.path.exists(FICHIER_PANNE)


def simuler_traitement_reussi():
    """Met à jour la métrique avec l'heure actuelle : 'le pipeline vient de réussir'."""
    dernier_traitement.set_to_current_time()
    print(f"[OK] Traitement Anfa simulé avec succès à {time.strftime('%H:%M:%S')}", flush=True)


if __name__ == "__main__":
    # Expose les métriques sur http://localhost:8000/metrics
    start_http_server(8000)
    print("[INFO] Exportateur démarré sur le port 8000.", flush=True)

    # Un premier succès immédiat pour que la métrique existe dès le départ.
    simuler_traitement_reussi()

    while True:
        time.sleep(INTERVALLE_SECONDES)
        if pipeline_en_panne():
            # Le processus reste vivant et continue d'exposer /metrics,
            # mais l'horodatage n'est PLUS mis à jour → la fraîcheur grimpe.
            print(f"[PANNE] Pipeline en panne à {time.strftime('%H:%M:%S')} : "
                  f"horodatage NON mis à jour.", flush=True)
            continue
        simuler_traitement_reussi()
