# Romanian CAEN Codes API

REST API for Romanian CAEN Rev. 3 codes (NACE classification) built with FastAPI and SQLite.

CAEN (Clasificarea Activităților din Economia Națională) — the Romanian classification of economic activities, equivalent to the European NACE Rev. 2 standard.

Data sources:
- CAEN Rev. 3 full structure (PDF): https://www.onrc.ro/documente/anunturi/CAEN-Rev.3_structura-completa.pdf
- ONRC CAEN index: https://www.onrc.ro/index.php/ro/caen-index

---

## Project structure

```
.
├── caen_rev3_coduri_clase.csv          # Source data (651 CAEN classes)
├── caen_rev3_coduri_grupa_diviziune.csv
├── caen_rev3_ierarhic_diviziuni_grupe_clase.csv
├── init_db.py                          # Builds caen.db from CSV
├── main.py                             # FastAPI application
├── scrape_to_text.py                   # Scraper used to collect the data
├── CAEN.sql                            # Legacy PostgreSQL flat table
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Database schema

SQLite database with four related tables:

```
sectiuni  (A, B, C…)
  └── diviziuni  (01, 02…)
        └── grupe  (011, 012…)
              └── clase  (0111, 0112…)  ← CAEN 4-digit codes
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/caen/{cod}` | Exact 4-digit CAEN code lookup |
| `GET` | `/caen?q={text}` | Search by code or name (supports partial match) |
| `GET` | `/docs` | Swagger UI |

### Example responses

**GET /caen/0111**
```json
{
  "cod_caen": "0111",
  "denumire": "Cultivarea cerealelor (excluzând orezul), plantelor leguminoase şi a plantelor oleaginoase",
  "sectiune_cod": "A",
  "sectiune": "AGRICULTURĂ, SILVICULTURĂ ŞI PESCUIT",
  "diviziune_cod": "01",
  "diviziune": "Agricultură, vânătoare şi servicii anexe",
  "grupa_cod": "011",
  "grupa": "Cultivarea plantelor nepermanente"
}
```

**GET /caen?q=cereale&limit=10&offset=0**
```json
{
  "total": 2,
  "results": [...]
}
```

## Running locally

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

python init_db.py             # creates caen.db
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive API docs.

## Docker

```bash
docker compose up -d --build
```

The API will be available at http://localhost:8000.

The SQLite database is built inside the container at image build time — no external database service required.
