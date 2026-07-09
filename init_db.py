"""
Inițializare bază de date SQLite din fișierul CSV caen_rev3_coduri_clase.csv.
Rulează o singură dată (sau ori de câte ori vrei să reîncărci datele).
"""
import csv
import sqlite3
import os
import re

DB_PATH = os.getenv("DB_PATH", "caen.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "caen_rev3_coduri_clase.csv")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript("""
        DROP TABLE IF EXISTS clase;
        DROP TABLE IF EXISTS grupe;
        DROP TABLE IF EXISTS diviziuni;
        DROP TABLE IF EXISTS sectiuni;

        CREATE TABLE sectiuni (
            cod   TEXT PRIMARY KEY,
            denumire TEXT NOT NULL
        );

        CREATE TABLE diviziuni (
            cod          TEXT PRIMARY KEY,
            denumire     TEXT NOT NULL,
            sectiune_cod TEXT NOT NULL REFERENCES sectiuni(cod)
        );

        CREATE TABLE grupe (
            cod          TEXT PRIMARY KEY,
            denumire     TEXT NOT NULL,
            diviziune_cod TEXT NOT NULL REFERENCES diviziuni(cod)
        );

        CREATE TABLE clase (
            cod       TEXT PRIMARY KEY,
            denumire  TEXT NOT NULL,
            grupa_cod TEXT NOT NULL REFERENCES grupe(cod)
        );

        CREATE INDEX idx_clase_denumire ON clase(denumire);
    """)

    sectiuni_vazute: set = set()
    diviziuni_vazute: set = set()
    grupe_vazute: set = set()

    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            # --- Sectiune ---
            raw_sec = row["sectiune"].strip()
            # "SECŢIUNEA A - AGRICULTURĂ, ..."  sau  "SECŢIUNEA K – TELECOMUNICAȚII; ..."
            m = re.match(r"SEC[TȚŢ]IUNEA\s+(\S+)\s*[-–]\s*(.+)", raw_sec, re.IGNORECASE)
            if m:
                sec_cod = m.group(1).strip()
                sec_den = m.group(2).strip().rstrip(";").strip()
            else:
                # fallback: folosim textul complet ca denumire, cod generat
                sec_cod = raw_sec[:10]
                sec_den = raw_sec

            if sec_cod not in sectiuni_vazute:
                sectiuni_vazute.add(sec_cod)
                conn.execute(
                    "INSERT OR IGNORE INTO sectiuni (cod, denumire) VALUES (?, ?)",
                    (sec_cod, sec_den),
                )

            # --- Diviziune ---
            div_cod = row["diviziune_cod"].strip()
            div_den = row["diviziune"].strip()
            if div_cod not in diviziuni_vazute:
                diviziuni_vazute.add(div_cod)
                conn.execute(
                    "INSERT OR IGNORE INTO diviziuni (cod, denumire, sectiune_cod) VALUES (?, ?, ?)",
                    (div_cod, div_den, sec_cod),
                )

            # --- Grupa ---
            grp_cod = row["grupa_cod"].strip()
            grp_den = row["grupa"].strip()
            if grp_cod not in grupe_vazute:
                grupe_vazute.add(grp_cod)
                conn.execute(
                    "INSERT OR IGNORE INTO grupe (cod, denumire, diviziune_cod) VALUES (?, ?, ?)",
                    (grp_cod, grp_den, div_cod),
                )

            # --- Clasa ---
            conn.execute(
                "INSERT OR IGNORE INTO clase (cod, denumire, grupa_cod) VALUES (?, ?, ?)",
                (row["cod_caen"].strip(), row["clasa_caen"].strip(), grp_cod),
            )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM clase").fetchone()[0]
    conn.close()
    print(f"Baza de date initializata: {count} coduri CAEN in '{DB_PATH}'")


if __name__ == "__main__":
    init_db()
