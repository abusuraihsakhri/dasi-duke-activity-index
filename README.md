# DASI Duke Activity Index

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Duke Activity Status Index (DASI) is a validated 12-item questionnaire used to assess functional capacity in cardiovascular patients. This implementation:

- Calculates DASI score from questionnaire responses (0-48.7)
- Estimates peak VO2 (mL/kg/min) using the Hlatky formula
- Converts to METs (Metabolic Equivalents)
- Classifies functional capacity (Poor/Moderate/Good) per ACC/AHA guidelines

**Reference:** Hlatky MA, et al. "A brief self-administered questionnaire to determine functional capacity." Am J Cardiol. 1989.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`**: Core DASI algorithm - computes score, peak VO2, METs, and classification
- **`calculate_dasi_score()`**: Computes DASI score from 12 questionnaire items
- **`estimate_peak_vo2()`**: Estimates peak VO2 using Hlatky formula: `(DASI × 0.43) + 9.6`
- **`calculate_mets()`**: Converts peak VO2 to METs: `VO2 / 3.5`
- **`classify_functional_capacity()`**: Classifies per ACC/AHA guidelines
- **`process_single()`**: Evaluate a single case
- **`process_batch()`**: Process batch CSV with multiple cases

---

## 📐 DASI Questionnaire Items

| Item | Weight | Activity |
|:-----|:-------|:---------|
| v1   | 1.75   | Take care of yourself (eating, dressing, bathing) |
| v2   | 1.75   | Walk indoors around the house |
| v3   | 2.75   | Walk 1-2 blocks on level ground |
| v4   | 3.50   | Climb a flight of stairs or walk up a hill |
| v5   | 4.50   | Run a short distance |
| v6   | 2.70   | Light work around the house |
| v7   | 3.50   | Moderate work around the house |
| v8   | 5.50   | Heavy work around the house |
| v9   | 4.00   | Rake leaves, weed, or garden |
| v10  | 5.25   | Sexual relations |
| v11  | 6.00   | Moderate recreational activities |
| v12  | 7.50   | Strenuous sports |

**Maximum Score:** 48.7

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/dasi-duke-activity-index.git
cd dasi-duke-activity-index

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set up environment
cp .env.example .env
# Edit .env and set AUDIT_SECRET_KEY
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
# Using individual DASI items (0 = cannot do, 1 = can do)
python dasi_index.py single --v1 1 --v2 1 --v3 1 --v4 1 --v5 0 --v6 1 --v7 1 --v8 0 --v9 1 --v10 1 --v11 0 --v12 0

# Using pre-computed DASI score
python dasi_index.py single --dasi-score 35.0
```

### 2. Batch CSV Processing
```bash
python dasi_index.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (with audit trail)
```bash
# Set required environment variable
export AUDIT_SECRET_KEY="your-secure-key"

# Run audit
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail
python cli.py verify-audit

# Start API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` - `v12` | DASI questionnaire responses (0 or 1) | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
* **Secure Key Management:** Audit signing key loaded from `AUDIT_SECRET_KEY` environment variable (no hardcoded secrets)
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational metrics (`/metrics`)

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Set test key (or add to .env)
export AUDIT_SECRET_KEY="test-secret-key-for-pytest-only"

# Run all tests
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Create .env file with required variables
echo "AUDIT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env

# Build and run with Docker Compose
docker-compose up --build

# Or use Docker directly
docker build -t dasi-duke-activity-index .
docker run -p 8000:8000 --env-file .env dasi-duke-activity-index
```

---

## 📊 Functional Capacity Classification

| Classification | METs | DASI Score | Recommendation |
|:---------------||:-----|:-----------|:---------------|
| Poor           | < 4  | < ~10.2    | Consider preoperative cardiac testing; high surgical risk |
| Moderate       | 4-7  | ~10.2-34.7 | Moderate surgical risk; clinical judgment for further testing |
| Good           | > 7  | > ~34.7    | Low surgical risk; proceed without additional cardiac testing |
