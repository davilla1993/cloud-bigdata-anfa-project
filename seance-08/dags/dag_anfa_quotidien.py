"""
dag_anfa_quotidien.py
─────────────────────
DAG Airflow : orchestration du pipeline Anfa.
La logique métier vit dans anfa_logic.py (testée séparément en CI).
"""

import os
from datetime import datetime, timedelta

import boto3
from airflow import DAG
from airflow.operators.python import PythonOperator

from anfa_logic import verifier_liste_fichiers, construire_message_notification


def verifier_resultats():
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        region_name="us-east-1",
    )
    reponse = s3.list_objects_v2(Bucket="anfa-processed", Prefix="heures_de_pointe/")
    objets = reponse.get("Contents", [])

    resume = verifier_liste_fichiers(objets)   # ← logique testée
    print(f"[OK] {resume['nb_fichiers']} fichiers, {resume['taille_totale_ko']} Ko")


def notifier():
    resume = {"nb_fichiers": 4, "taille_totale_ko": 128.5}   # exemple pour ce TP
    print(construire_message_notification(resume))            # ← logique testée


default_args = {"owner": "anfa-data-team", "retries": 2, "retry_delay": timedelta(seconds=30)}

with DAG(
    dag_id="anfa_pipeline_quotidien",
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
) as dag:
    t_verifier = PythonOperator(task_id="verifier_resultats", python_callable=verifier_resultats)
    t_notifier = PythonOperator(task_id="notifier", python_callable=notifier)
    t_verifier >> t_notifier
