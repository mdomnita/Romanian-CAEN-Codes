"""
API Romanian CAEN Codes – FastAPI + SQLite
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = os.getenv("DB_PATH", "caen.db")

app = FastAPI(
    title="Romanian CAEN Codes API",
    description="Cautare coduri CAEN Rev. 3 dupa cod sau denumire.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


_QUERY_BASE = """
    SELECT
        c.cod            AS cod_caen,
        c.denumire       AS denumire,
        s.cod            AS sectiune_cod,
        s.denumire       AS sectiune,
        d.cod            AS diviziune_cod,
        d.denumire       AS diviziune,
        g.cod            AS grupa_cod,
        g.denumire       AS grupa
    FROM   clase c
    JOIN   grupe      g ON c.grupa_cod     = g.cod
    JOIN   diviziuni  d ON g.diviziune_cod = d.cod
    JOIN   sectiuni   s ON d.sectiune_cod  = s.cod
"""


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CAENEntry(BaseModel):
    cod_caen: str
    denumire: str
    sectiune_cod: str
    sectiune: str
    diviziune_cod: str
    diviziune: str
    grupa_cod: str
    grupa: str


class SearchResponse(BaseModel):
    total: int
    results: list[CAENEntry]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/caen/{cod}",
    response_model=CAENEntry,
    summary="Cauta dupa cod CAEN exact (4 cifre)",
)
def get_by_code(cod: str):
    """
    Returneaza detalii complete (denumire, sectiune, diviziune, grupa)
    pentru un cod CAEN de 4 cifre.
    """
    with get_db() as conn:
        row = conn.execute(
            _QUERY_BASE + " WHERE c.cod = ?", (cod.strip(),)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Codul CAEN '{cod}' nu a fost gasit.")

    return dict(row)


@app.get(
    "/caen",
    response_model=SearchResponse,
    summary="Cauta coduri CAEN dupa cod sau denumire",
)
def search(
    q: str = Query(..., min_length=1, description="Text de cautare (cod sau parte din denumire)"),
    limit: int = Query(50, ge=1, le=200, description="Numar maxim de rezultate"),
    offset: int = Query(0, ge=0, description="Paginare – pozitia de start"),
):
    """
    Cauta coduri CAEN dupa cod partial sau text din denumire.
    Exemplu: `/caen?q=0111` sau `/caen?q=cereale`
    """
    pattern = f"%{q.strip()}%"
    sql_where = " WHERE c.cod LIKE ? OR c.denumire LIKE ? "

    with get_db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM clase c {sql_where}", (pattern, pattern)
        ).fetchone()[0]

        rows = conn.execute(
            _QUERY_BASE + sql_where + " ORDER BY c.cod LIMIT ? OFFSET ?",
            (pattern, pattern, limit, offset),
        ).fetchall()

    return {"total": total, "results": [dict(r) for r in rows]}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
