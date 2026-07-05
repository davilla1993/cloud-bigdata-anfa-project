"""
lecture_flux_console.py
────────────────────────
Premier contact avec Spark Structured Streaming :
lit le topic Kafka et affiche les messages en console.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType
from pyspark.sql.functions import col, from_json


def creer_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("Anfa - Lecture flux Kafka (console)")
        .master("spark://spark-master:7077")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.8"
        )
        .getOrCreate()
    )


def main():
    spark = creer_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # ── Schéma attendu des messages JSON envoyés par le simulateur ──
    schema_position = (
        StructType()
        .add("bus_id", StringType())
        .add("ligne_id", StringType())
        .add("latitude", DoubleType())
        .add("longitude", DoubleType())
        .add("vitesse_kmh", IntegerType())
        .add("timestamp", StringType())
    )

    # ── Lecture du flux Kafka ──
    # Notez : readStream (pas read) — c'est la seule vraie différence avec le batch.
    flux_brut = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "kafka-1:9092,kafka-2:9092,kafka-3:9092")
        .option("subscribe", "anfa-positions-bus")
        .option("startingOffsets", "latest")   # ne lit que les nouveaux messages
        .load()
    )

    # Le champ "value" de Kafka est du binaire JSON : on le parse selon le schéma
    positions = (
        flux_brut
        .select(from_json(col("value").cast("string"), schema_position).alias("data"))
        .select("data.*")
    )

    # ── Écriture en streaming vers la console (pour validation) ──
    requete = (
        positions.writeStream
        .format("console")
        .outputMode("append")
        .option("truncate", "false")
        .trigger(processingTime="5 seconds")   # micro-batch toutes les 5 secondes
        .start()
    )

    requete.awaitTermination()


if __name__ == "__main__":
    main()
