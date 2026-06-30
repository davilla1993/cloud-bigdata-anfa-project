# Bonus — Spark sur Kubernetes (Partie 6)

## Objectif

Reprendre le job `heures_de_pointe.py` (exécuté sur Spark standalone en Partie 4) et le soumettre
à un cluster Kubernetes via **Spark Operator** en réutilisant le cluster Kind `anfa` de la séance 3.

---

## Architecture cible

```
┌─────────────────────────────────────────────────────────┐
│  Kind cluster "anfa"  (namespace: spark)                │
│                                                         │
│  ┌─────────────────┐    ┌───────────────────────────┐  │
│  │  Spark Operator  │    │  SparkApplication CRD     │  │
│  │  (controller)    │───▶│  anfa-heures-de-pointe    │  │
│  └─────────────────┘    └───────────────────────────┘  │
│                                  │                      │
│                    ┌─────────────┴──────────┐           │
│                    ▼                        ▼           │
│           ┌──────────────┐       ┌──────────────────┐  │
│           │ Driver Pod   │       │ Executor Pods x2 │  │
│           │ (1 core/1Go) │       │ (1 core/1Go each)│  │
│           └──────────────┘       └──────────────────┘  │
│                    │                        │           │
│                    └────────────┬───────────┘           │
│                                 ▼                      │
│                    ┌─────────────────────┐             │
│                    │ MinIO (namespace:   │             │
│                    │ default, port 9000) │             │
│                    └─────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 6.1 Préparer le cluster Kind

Le cluster Kind de la séance 3 a été supprimé. On le recrée :

```bash
kind create cluster --name anfa
kubectl create namespace spark
```

Vérifier que le cluster répond :

```bash
kubectl cluster-info --context kind-anfa
kubectl get nodes
```

---

## 6.2 Installer Spark Operator via Helm

```bash
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update

helm install spark-operator spark-operator/spark-operator \
    --namespace spark \
    --create-namespace \
    --set webhook.enable=true
```

Attendre que le controller soit prêt :

```bash
kubectl wait --namespace spark \
  --for=condition=Ready pod \
  --selector=app.kubernetes.io/name=spark-operator \
  --timeout=90s
```

---

## 6.3 Créer le ServiceAccount Spark

Le driver Spark a besoin de droits pour créer les pods executors :

```bash
kubectl create serviceaccount spark -n spark

kubectl create clusterrolebinding spark-role \
    --clusterrole=edit \
    --serviceaccount=spark:spark \
    --namespace=spark
```

---

## 6.4 Déployer MinIO sur Kubernetes

On réutilise le manifeste MinIO de la séance 3 pour que les pods Spark
puissent accéder au stockage objet depuis l'intérieur du cluster :

```yaml
# minio-k8s.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: spark
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
        - name: minio
          image: minio/minio:latest
          args: ["server", "/data", "--console-address", ":9001"]
          env:
            - name: MINIO_ROOT_USER
              value: anfa-admin
            - name: MINIO_ROOT_PASSWORD
              value: anfa-password-2026
          ports:
            - containerPort: 9000
            - containerPort: 9001
---
apiVersion: v1
kind: Service
metadata:
  name: minio-service
  namespace: spark
spec:
  selector:
    app: minio
  ports:
    - name: api
      port: 9000
      targetPort: 9000
    - name: console
      port: 9001
      targetPort: 9001
```

```bash
kubectl apply -f minio-k8s.yaml

# Recréer les buckets et uploader le référentiel via le pod MinIO
kubectl exec -n spark deploy/minio -- sh -c "
  mc alias set local http://localhost:9000 anfa-admin anfa-password-2026 &&
  mc mb local/anfa-raw &&
  mc mb local/anfa-processed &&
  mc admin user svcacct add local anfa-admin \
      --access-key anfa-app-key \
      --secret-key anfa-app-secret-2026
"
```

---

## 6.5 Construire une image Docker embarquant le job

Le job Python doit être accessible à l'intérieur des pods Spark. La méthode la plus propre est de
construire une image qui étend l'image officielle Spark et copie les fichiers jobs :

```dockerfile
# Dockerfile.spark-job
FROM apache/spark:3.5.8-python3
COPY jobs/ /opt/jobs/
```

Construire et charger l'image dans Kind (sans registry externe) :

```bash
docker build -t anfa-spark-job:latest -f Dockerfile.spark-job .
kind load docker-image anfa-spark-job:latest --name anfa
```

---

## 6.6 Manifest SparkApplication

```yaml
# spark-heures-de-pointe.yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: anfa-heures-de-pointe
  namespace: spark
spec:
  type: Python
  mode: cluster
  image: anfa-spark-job:latest
  imagePullPolicy: Never          # image chargée localement dans Kind
  mainApplicationFile: local:///opt/jobs/heures_de_pointe.py
  sparkVersion: "3.5.8"
  restartPolicy:
    type: Never
  sparkConf:
    spark.hadoop.fs.s3a.endpoint: "http://minio-service:9000"
    spark.hadoop.fs.s3a.access.key: "anfa-app-key"
    spark.hadoop.fs.s3a.secret.key: "anfa-app-secret-2026"
    spark.hadoop.fs.s3a.path.style.access: "true"
    spark.hadoop.fs.s3a.impl: "org.apache.hadoop.fs.s3a.S3AFileSystem"
    spark.hadoop.fs.s3a.connection.ssl.enabled: "false"
    spark.jars.packages: "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262"
    spark.jars.ivy: "/tmp/.ivy2"
  driver:
    cores: 1
    memory: "1024m"
    serviceAccount: spark
    labels:
      version: "3.5.8"
  executor:
    cores: 1
    instances: 2
    memory: "1024m"
    labels:
      version: "3.5.8"
```

---

## 6.7 Soumettre et monitorer

```bash
# Soumettre le job
kubectl apply -f spark-heures-de-pointe.yaml

# Suivre l'état du SparkApplication
kubectl get sparkapplication -n spark -w

# Voir les pods créés (driver + executors)
kubectl get pods -n spark

# Logs du driver (résultats et erreurs)
kubectl logs -n spark anfa-heures-de-pointe-driver
```

Le cycle de vie attendu dans `kubectl get sparkapplication` :

```
NAME                       STATUS      ATTEMPTS   START                  FINISH
anfa-heures-de-pointe      SUBMITTED   1          2026-01-01T10:00:00Z   <none>
anfa-heures-de-pointe      RUNNING     1          2026-01-01T10:00:05Z   <none>
anfa-heures-de-pointe      COMPLETED   1          2026-01-01T10:00:05Z   2026-01-01T10:02:30Z
```

---

## 6.8 Différences clés : Spark standalone vs Spark sur Kubernetes

| Aspect | Spark standalone (Compose) | Spark sur Kubernetes |
|--------|---------------------------|----------------------|
| Orchestrateur | Docker Compose | Kubernetes (Kind) |
| Soumission | `spark-submit --master spark://` | `kubectl apply -f SparkApplication.yaml` |
| Scalabilité | Manuelle (ajouter des workers) | Dynamique (Kubernetes gère les pods) |
| Réseau MinIO | `http://minio:9000` (DNS Compose) | `http://minio-service:9000` (DNS K8s) |
| Tolérance aux pannes | Limitée | Native (K8s recrée les pods) |
| Observabilité | UI Spark Master (port 8080) | `kubectl logs` + Spark Operator UI |
| Complexité de setup | Faible | Élevée (Helm, RBAC, CRD, image custom) |

---

## Observations

- **Complexité** : le setup Kubernetes est nettement plus lourd qu'un `docker compose up`. Helm,
  les ServiceAccounts, les CRDs Spark Operator et la gestion de l'image dans Kind représentent
  plusieurs étapes préalables avant de pouvoir soumettre le moindre job.

- **Valeur ajoutée** : une fois l'infrastructure en place, la soumission de jobs via un manifeste
  YAML déclaratif est plus reproductible et versionnable qu'une commande `spark-submit`.

- **Réseau** : le point le plus délicat est la connectivité entre les pods Spark et MinIO. Sur
  Docker Compose, le DNS interne est automatique. Sur Kubernetes, il faut explicitement déployer
  MinIO dans le même namespace et exposer un Service.

- **Production** : Spark sur Kubernetes est l'architecture de référence pour les déploiements cloud
  modernes (EKS, GKE, AKS). Les clusters Spark standalone (Compose) restent utiles pour le
  développement local rapide.
