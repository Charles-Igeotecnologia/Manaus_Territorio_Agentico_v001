#!/usr/bin/env python3
"""Executor geoespacial v002: consultas reproduziveis sobre geometria validada."""

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GPKG = ROOT / "dados_publicados" / "manaus_base_consulta_v001.gpkg"
AUDIT_DIR = ROOT / "06_produtos" / "auditoria_executor"
ALLOWED_LAYERS = {"edu_escolas_manaus", "ref_bairros_zonas_manaus", "ref_localidades_manaus", "ref_setores_censitarios_manaus_2022"}


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(path):
    if not path.exists():
        raise FileNotFoundError(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def layer_info(conn, layer):
    if layer not in ALLOWED_LAYERS:
        raise ValueError(f"Camada nao autorizada: {layer}")
    row = conn.execute("SELECT table_name, srs_id, description FROM gpkg_contents WHERE table_name=?", (layer,)).fetchone()
    if not row:
        raise ValueError(f"Camada inexistente: {layer}")
    count = conn.execute(f'SELECT COUNT(*) AS n FROM "{layer}"').fetchone()[0]
    return {"camada": layer, "registros": count, "srs_id": row["srs_id"], "crs": f'EPSG:{row["srs_id"]}' if row["srs_id"] else None, "descricao": row["description"]}


def escolas_por_campo(conn, campo):
    allowed = {"ddz", "bairro", "zona", "modalidade", "status", "tipo"}
    if campo not in allowed:
        raise ValueError("Campo nao autorizado")
    rows = conn.execute(f'SELECT COALESCE(NULLIF(TRIM("{campo}"), ""), "nao_informado") AS chave, COUNT(*) AS total FROM edu_escolas_manaus GROUP BY chave ORDER BY chave').fetchall()
    return [{"valor": r["chave"], "total": r["total"]} for r in rows]


def escolas_filtrar(conn, campo, valor):
    allowed = {"ddz", "bairro", "zona", "modalidade", "status", "tipo"}
    if campo not in allowed:
        raise ValueError("Campo nao autorizado")
    rows = conn.execute(f'SELECT codigo_sigeam, codigo_inep, nome_escola, ddz, bairro, zona, modalidade, status, alunos FROM edu_escolas_manaus WHERE LOWER(TRIM("{campo}")) = LOWER(TRIM(?)) ORDER BY nome_escola', (valor,)).fetchall()
    return [dict(r) for r in rows]


def audit(payload):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = AUDIT_DIR / f"consulta_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpkg", type=Path, default=DEFAULT_GPKG)
    sub = p.add_subparsers(dest="acao", required=True)
    a = sub.add_parser("info")
    a.add_argument("--camada", required=True)
    a = sub.add_parser("agrupar-escolas")
    a.add_argument("--campo", required=True)
    a = sub.add_parser("filtrar-escolas")
    a.add_argument("--campo", required=True)
    a.add_argument("--valor", required=True)
    args = p.parse_args()

    conn = connect(args.gpkg)
    try:
        if args.acao == "info":
            resultado = layer_info(conn, args.camada)
        elif args.acao == "agrupar-escolas":
            resultado = escolas_por_campo(conn, args.campo)
        else:
            resultado = escolas_filtrar(conn, args.campo, args.valor)
        payload = {
            "executado_em": now(),
            "fonte": str(args.gpkg),
            "acao": args.acao,
            "crs_transformado": False,
            "aviso_crs": "Nenhuma transformacao de CRS realizada nesta consulta.",
            "resultado": resultado,
        }
        log = audit(payload)
        payload["auditoria"] = str(log)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
