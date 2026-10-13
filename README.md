# Duke Activity Status Index (DASI)

### [Open the Live Application →](https://abusuraihsakhri.github.io/dasi-duke-activity-index/)

A 12-question functional-capacity calculator implementing the published Duke Activity Status Index weights. It reports a **DASI score (0–58.2)**, regression-estimated peak oxygen uptake, and estimated metabolic equivalents (METs). The source code implements the calculation; it does not perform an exercise test or calculate surgical cardiac risk.

## Browser questionnaire

The self-contained application is in [`web/index.html`](web/index.html). It requires an explicit Yes/No answer to all 12 activities, calculates locally without external JavaScript packages or servers, and can export a CSV of answers and results. No browser data is intentionally uploaded, stored, or sent to any endpoint. The same static application is deployed through GitHub Pages.

**Clinical limitation:** The 2024 AHA/ACC perioperative guideline uses **DASI ≤34** as a screening criterion for poor/uncertain functional capacity. Estimated VO₂ and METs are regression-derived, not measured values. Do not use this tool alone for perioperative clearance, stress-test decisions, diagnosis, or patient management.

## Algorithm

For each Yes response, add its item weight. No contributes zero.

| Item | Activity | Weight |
| --- | --- | ---: |
| v1 | Self-care | 2.75 |
| v2 | Walk indoors | 1.75 |
| v3 | Walk 1–2 blocks | 2.75 |
| v4 | Climb stairs or hill | 5.50 |
| v5 | Run a short distance | 8.00 |
| v6 | Light housework | 2.70 |
| v7 | Moderate housework | 3.50 |
| v8 | Heavy housework | 8.00 |
| v9 | Yardwork | 4.50 |
| v10 | Sexual relations | 5.25 |
| v11 | Moderate recreation | 6.00 |
| v12 | Strenuous sports | 7.50 |

`Estimated peak VO₂ (mL/kg/min) = 0.43 × DASI + 9.6`

`Estimated METs = Estimated peak VO₂ / 3.5`

## Python CLI

Python 3.10+ is supported. The scoring library has no third-party dependencies.

```bash
python dasi_index.py single --v1 1 --v2 1 --v3 0 --v4 1
python dasi_index.py single --dasi-score 34
python dasi_index.py batch -i sample.csv -o results.csv
```

Pass **0 or 1**, not fractional answers, for each item. For complete clinical assessments provide all 12 answers; the legacy Python CLI permits partially specified questionnaires, defaults missing items to No, and exposes `inputs_evaluated` to indicate how many were provided. A precomputed score must be between 0 and 58.2. Invalid responses are rejected rather than silently converted to zero.

The batch command preserves existing CSV fields and adds `dasi_score`, `peak_vo2_ml_kg_min`, `mets`, `classification`, and `clinical_recommendation` columns. Do not process identifiable patient data using an untrusted environment.

## Optional REST server

The FastAPI service is independent of GitHub Pages. For local hosting:

```bash
python -m pip install 'fastapi>=0.115,<1' 'uvicorn>=0.30,<1' 'pydantic>=2,<3'
python cli.py serve --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/` for the questionnaire or POST to `/api/dasi` with a JSON object containing a `responses` map of **all** `v1` through `v12` as 0 or 1. `/api/dasi` performs no audit logging.

The older `cli.py audit`, `cli.py chat`, `cli.py batch`, and `/api/audit` routes remain as **legacy demonstration components**. They use illustrative thresholds unrelated to validated DASI interpretation. The chat provider is deterministic mock output, not model-generated clinical advice. Audit and chat HTTP routes require an `AUDIT_API_KEY` header matching the separately configured environment variable; without a configured key they are disabled. The audit ledger is HMAC-signed but **in-memory only**; it is not a durable, HIPAA-compliant clinical audit system. PHI regex screening is incomplete and must not be treated as de-identification.

To run legacy audits, supply `AUDIT_SECRET_KEY` as an independently generated random value. See [`.env.example`](.env.example). For container use, create a local `.env` then run `docker compose up --build`. Docker excludes `.env` from its build context.

## Testing

```bash
python -m pip install pytest 'fastapi>=0.115,<1' 'uvicorn>=0.30,<1' 'pydantic>=2,<3'
AUDIT_SECRET_KEY=local-test-key python -m pytest -v
```

GitHub Actions tests Python 3.10–3.12; the Pages workflow publishes the dependency-free `web/` directory when GitHub Pages is configured to use **GitHub Actions**.

## References

- Hlatky MA, Boineau RE, Higginbotham MB, et al. A brief self-administered questionnaire to determine functional capacity (The Duke Activity Status Index). *Am J Cardiol.* 1989;64:651–654. [doi:10.1016/0002-9149(89)90496-7](https://doi.org/10.1016/0002-9149(89)90496-7).
- 2024 AHA/ACC multisociety guideline for perioperative cardiovascular management for noncardiac surgery. [doi:10.1161/CIR.0000000000001285](https://doi.org/10.1161/CIR.0000000000001285).

## Compatibility and license

The web app uses modern browser APIs (HTML forms, Blob, object URLs) and works in current Chrome, Firefox, Safari, and Edge; it is designed for mobile and desktop screens. JavaScript must be enabled. [MIT License](LICENSE).
