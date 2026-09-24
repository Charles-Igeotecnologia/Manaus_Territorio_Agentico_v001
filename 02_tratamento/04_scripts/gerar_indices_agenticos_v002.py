#!/usr/bin/env python3
"""Gera indices agenticos leves a partir do GeoPackage autoritativo de consulta."""

import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dados_publicados" / "manaus_base_consulta_v001.gpkg"
OUT = ROOT / "06_indices_agenticos"
LAYER = "edu_escolas_manaus"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

FIELDS = ["codigo_sigeam", "codigo_inep", "nome_escola", "ddz", "distrito", "bairro", "zona", "modalidade", "status", "tipo", "alunos"]


def norm(value):
    return "" if value is None else str(value).strip()


def grouped(rows, field):
    c = Counter(norm(r[field]) or "nao_informado" for r in rows)
    return dict(sorted(c.items(), key=lambda item: item[0].casefold()))


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Fonte autoritativa nao encontrada: {SOURCE}")
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SOURCE)
    conn.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in conn.execute(f'PRAGMA table_info("{LAYER}")')}
        missing = set(FIELDS) - cols
        if missing:
            raise RuntimeError("Campos ausentes: " + ", ".join(sorted(missing)))
        rows = [dict(r) for r in conn.execute(f'SELECT {", ".join(FIELDS)} FROM "{LAYER}" ORDER BY nome_escola')]
    finally:
        conn.close()

    with (OUT / "escolas.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    for field, filename in [("ddz", "escolas_por_ddz.json"), ("bairro", "escolas_por_bairro.json"), ("zona", "escolas_por_zona.json"), ("modalidade", "modalidades.json")]:
        (OUT / filename).write_text(json.dumps(grouped(rows, field), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "versao": "v002",
        "gerado_em": NOW,
        "fonte_autoritativa": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "camada": LAYER,
        "registros": len(rows),
        "crs_geometria_fonte": "EPSG:4674",
        "nota": "Indices tabulares derivados. Operacoes espaciais devem consultar geometria validada na fonte autoritativa.",
        "arquivos": ["escolas.csv", "escolas_por_ddz.json", "escolas_por_bairro.json", "escolas_por_zona.json", "modalidades.json"]
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(rows)} escolas indexadas em {OUT}")


if __name__ == "__main__":
    main()
