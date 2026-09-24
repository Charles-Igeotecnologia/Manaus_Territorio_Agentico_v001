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


def espacializar_escolas(gpkg, campo=None, valor=None, destino=None):
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError("GeoPandas e necessario para espacializacao.") from exc
    gdf = gpd.read_file(gpkg, layer="edu_escolas_manaus")
    if gdf.crs is None:
        raise ValueError("CRS ausente: espacializacao interrompida; nao e permitido inferir CRS.")
    if gdf.geometry.isna().all():
        raise ValueError("Camada sem geometria validada: espacializacao interrompida.")
    if campo:
        allowed = {"ddz", "bairro", "zona", "modalidade", "status", "tipo"}
        if campo not in allowed or valor is None:
            raise ValueError("Filtro espacial invalido")
        gdf = gdf[gdf[campo].astype(str).str.strip().str.casefold() == str(valor).strip().casefold()].copy()
    if destino:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(destino, driver="GeoJSON")
    return {
        "camada": "edu_escolas_manaus",
        "feicoes": int(len(gdf)),
        "crs_origem": gdf.crs.to_string(),
        "tipos_geometria": sorted(gdf.geom_type.dropna().unique().tolist()),
        "geojson": str(destino) if destino else None,
        "geometria_inferida": False,
    }


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
    a = sub.add_parser("espacializar-escolas")
    a.add_argument("--campo")
    a.add_argument("--valor")
    a.add_argument("--geojson", required=True)
    args = p.parse_args()

    if args.acao == "espacializar-escolas":
        resultado = espacializar_escolas(args.gpkg, args.campo, args.valor, args.geojson)
    else:
        conn = connect(args.gpkg)
        try:
            if args.acao == "info":
                resultado = layer_info(conn, args.camada)
            elif args.acao == "agrupar-escolas":
                resultado = escolas_por_campo(conn, args.campo)
            else:
                resultado = escolas_filtrar(conn, args.campo, args.valor)
        finally:
            conn.close()
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


if __name__ == "__main__":
    main()
