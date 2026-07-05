"""
premier_producer.py
────────────────────
Envoie 5 messages de test dans le topic anfa-positions-bus.
Sert à comprendre la mécanique de base d'un producer Kafka.
"""

import json
import time
from kafka import KafkaProducer

# On se connecte via les ports EXTERNES (19092, 19093, 19094)
# car ce script tourne sur la machine hôte, pas dans Docker.
producer = KafkaProducer(
    bootstrap_servers=["localhost:19092", "localhost:19093", "localhost:19094"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if k else None,
)

for i in range(5):
    message = {
        "bus_id": "B001",
        "message_numero": i,
        "contenu": f"Message de test numéro {i}",
    }
    # send() est ASYNCHRONE : il retourne immédiatement.
    # La clé "B001" détermine la partition de destination.
    producer.send("anfa-positions-bus", key="B001", value=message)
    print(f"[ENVOYÉ] {message}")
    time.sleep(0.5)

# flush() force l'envoi de tous les messages en attente avant de quitter
producer.flush()
print("\n[OK] 5 messages envoyés.")
