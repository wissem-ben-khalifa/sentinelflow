<div align="center">

#  SentinelFlow

### AI-Powered Hybrid Data Observability Platform

*Production-grade pipeline monitoring combining batch ETL, real-time streaming,*
*ML-based anomaly detection, and drift monitoring to ensure data reliability at scale.*

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Airflow](https://img.shields.io/badge/Airflow-2.8-017CEE?style=flat-square&logo=apacheairflow)
![Kafka](https://img.shields.io/badge/Kafka-3.6-231F20?style=flat-square&logo=apachekafka)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B?style=flat-square&logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## Overview

SentinelFlow is a production-inspired data observability platform built to monitor
the health, quality, and reliability of data pipelines.

Modern data teams face silent failures — missing values, schema changes, distribution
shifts, and corrupted records — that traditional infrastructure monitoring completely
misses. SentinelFlow addresses this by placing an AI-powered observability layer
directly on top of the data itself.

---

##  Architecture
┌─────────────────────────────────────────────────────────┐
│                      Data Sources                        │
│           E-Commerce (Batch) + Events (Stream)           │
└───────────────────────┬─────────────────────────────────┘
│
┌───────────────┴───────────────┐
▼                               ▼
┌───────────────┐               ┌───────────────┐
│ Batch Pipeline│               │   Streaming   │
│   (Airflow)   │               │    (Kafka)    │
└───────┬───────┘               └───────┬───────┘
└───────────────┬───────────────┘
▼
┌────────────────┐
│   Data Lake    │
│  (MinIO / S3)  │
└───────┬────────┘
│
▼
┌───────────────────────┐
│   Profiling Engine    │
│  completeness · stats │
│  uniqueness · dist    │
└───────────┬───────────┘
│
▼
┌───────────────────────┐
│  Validation Engine    │
│  Great Expectations   │
└───────────┬───────────┘
│
▼
┌───────────────────────┐
│   AI Detection Layer  │
│  Isolation Forest     │
│  Autoencoder          │
│  Z-Score · IQR        │
│  PSI · KS-Test        │
└───────────┬───────────┘
│
▼
┌───────────────────────┐
│  Metadata & Lineage   │
│     (PostgreSQL)      │
└───────────┬───────────┘
│
▼
┌───────────────────────┐
│  Alerting & Dashboard │
│  FastAPI + Streamlit  │
└───────────────────────┘

---

##  Features

###  Data Quality Monitoring
- Detects missing values, duplicates, invalid formats, out-of-range values
- Schema change detection (new columns, dropped columns, type changes)
- Freshness monitoring (late data arrivals)

###  AI Anomaly Detection
- **Isolation Forest** — unsupervised detection of abnormal records
- **Autoencoder** — deep learning reconstruction error detection
- **Statistical methods** — Z-Score, IQR, Moving Average

###  Data Drift Detection
- **PSI** (Population Stability Index) — distribution shift measurement
- **KS-Test** (Kolmogorov-Smirnov) — statistical distribution comparison
- **Jensen-Shannon Divergence** — distribution similarity scoring

###  Hybrid Pipeline
- **Batch** — daily ETL via Apache Airflow
- **Streaming** — real-time event processing via Apache Kafka

### Metadata & Lineage
- Full pipeline traceability from source to dashboard
- Quality score history per dataset
- Downstream impact visibility

###  Alerting
- Email alerts for threshold breaches
- Slack notifications (optional)
- Dashboard real-time notifications

---

##  Project Structure
sentinelflow/
├── config/                  # Settings and logging configuration
├── data/                    # Raw, processed, streaming, sample data
├── ingestion/
│   ├── batch/               # Data generation and batch loading
│   └── streaming/           # Kafka producer and consumer
├── profiling/               # Data profiling engine
├── validation/              # Great Expectations validation
├── detection/
│   ├── isolation_forest/    # Isolation Forest model
│   ├── autoencoder/         # Autoencoder model
│   ├── statistical/         # Z-Score and IQR detection
│   └── drift/               # PSI, KS-Test, JS Divergence
├── metadata/                # Metadata tracking and lineage
├── alerting/                # Email and Slack alerts
├── api/                     # FastAPI REST API
├── dashboard/               # Streamlit dashboard
├── airflow/                 # Airflow DAGs
├── kafka/                   # Kafka topic configuration
├── tests/                   # Unit and integration tests
├── scripts/                 # Setup and utility scripts
├── docker/                  # Docker configuration files
├── notebooks/               # Exploratory analysis
├── .github/workflows/       # CI/CD pipeline
├── docker-compose.yml       # Full stack orchestration
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template

---

##  Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/sentinelflow.git
cd sentinelflow
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start all services
```bash
docker-compose up -d
```

### 5. Initialize the database
```bash
python scripts/setup_db.py
```

### 6. Generate sample data
```bash
python scripts/seed_data.py
```

### 7. Run the pipeline
```bash
python scripts/run_pipeline.py
```

### 8. Launch the dashboard
```bash
streamlit run dashboard/app.py
```

### 9. Launch the API
```bash
uvicorn api.main:app --reload
```

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Batch Orchestration | Apache Airflow |
| Streaming | Apache Kafka |
| Data Lake | MinIO (S3-compatible) |
| Data Validation | Great Expectations |
| Anomaly Detection | Scikit-learn, TensorFlow |
| Drift Detection | SciPy, NumPy |
| Storage | PostgreSQL |
| API | FastAPI |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker + Docker Compose |
| Language | Python 3.11 |

---

##  Dashboard Pages

| Page | Description |
|---|---|
| Overview | Pipeline health score, quality score, anomaly count, drift status |
| Data Quality | Missing values, duplicates, schema violations per dataset |
| Anomalies | Isolation Forest results, Autoencoder results, historical trends |
| Drift | PSI scores, KS-Test results, distribution comparisons |

---

##  Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=. --cov-report=html

# Specific module
pytest tests/unit/test_profiler.py -v
```

---

##  License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Built with precision by [Your Name] · Data Engineering Portfolio Project
</div>