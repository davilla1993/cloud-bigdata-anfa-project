"""
simulateur_flotte.py
─────────────────────
Simule 100 bus Anfa envoyant leur position GPS toutes les ~1 seconde
(accéléré pour le TP ; en réalité ce serait toutes les 10 secondes).
Chaque message est publié dans anfa-positions-bus, avec bus_id comme clé.
"""

import json
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer

random.seed(2026)

NB_BUS = 100
LIGNES = [f"L{i:02d}" for i in range(1, 13)]

# Position de référence approximative : Lomé, Togo
LAT_BASE, LON_BASE = 6.1319, 1.2228

# On assigne chaque bus à une ligne et à une position de départ
bus_flotte = []
for i in range(1, NB_BUS + 1):
    bus_flotte.append({
        "bus_id": f"B{i:03d}",
        "ligne_id": random.choice(LIGNES),
        "lat": LAT_BASE + random.uniform(-0.05, 0.05),
        "lon": LON_BASE + random.uniform(-0.05, 0.05),
    })

producer = KafkaProducer(
    bootstrap_servers=["localhost:19092", "localhost:19093", "localhost:19094"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)


def deplacer(bus):
    """Simule un petit déplacement aléatoire du bus (marche aléatoire)."""
    bus["lat"] += random.uniform(-0.001, 0.001)
    bus["lon"] += random.uniform(-0.001, 0.001)


def main():
    print(f"[INFO] Démarrage de la simulation pour {NB_BUS} bus.")
    print("[INFO] Appuyez sur Ctrl+C pour arrêter.\n")

    compteur = 0
    try:
        while True:
            for bus in bus_flotte:
                deplacer(bus)
                message = {
                    "bus_id": bus["bus_id"],
                    "ligne_id": bus["ligne_id"],
                    "latitude": round(bus["lat"], 6),
                    "longitude": round(bus["lon"], 6),
                    "vitesse_kmh": random.randint(0, 45),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                # La clé = bus_id : garantit l'ordre des positions PAR bus
                producer.send("anfa-positions-bus", key=bus["bus_id"], value=message)
                compteur += 1

            producer.flush()
            print(f"[ENVOYÉ] Vague de {NB_BUS} positions (total cumulé : {compteur})")
            time.sleep(1)   # 1 vague de 100 messages par seconde

    except KeyboardInterrupt:
        print(f"\n[OK] Simulation arrêtée. {compteur} messages envoyés au total.")
        producer.close()


if __name__ == "__main__":
    main()
