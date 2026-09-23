#!/usr/bin/env python3
"""Create the initial cataloged GeoPackage for Territorio Agentico Manaus."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

VERSION_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = VERSION_ROOT.parent
OUTPUT_GPKG = VERSION_ROOT / "03_base_geo" / "manaus_base_geo_v001.gpkg"
CATALOG_DIR = VERSION_ROOT / "04_catalogo_metadados"
REPORT_PATH = VERSION_ROOT / "05_validacao" / "relatorios" / "manaus_validacao_estrutura_v001.txt"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

WKT_4326 = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
WKT_4674 = 'GEOGCS["SIRGAS 2000",DATUM["Sistema_de_Referencia_Geocentrico_para_las_AmericaS_2000",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6674"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4674"]]'
WKT_31980 = 'PROJCS["SIRGAS 2000 / UTM zone 20S",GEOGCS["SIRGAS 2000",DATUM["Sistema_de_Referencia_Geocentrico_para_las_AmericaS_2000",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6674"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4674"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-63],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","31980"]]'


def stamp(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stats(path: Path):
    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        item = path.stat()
        return 1, item.st_size, stamp(item.st_ctime), stamp(item.st_mtime), digest.hexdigest()
    files = [item for item in path.rglob("*") if item.is_file()]
    item = path.stat()
    return (
        len(files),
        sum(file.stat().st_size for file in files),
        stamp(item.st_ctime),
        stamp(max((file.stat().st_mtime for file in files), default=item.st_mtime)),
        None,
    )


def schema(conn):
    conn.execute("PRAGMA application_id = 0x47504B47")
    conn.execute("PRAGMA user_version = 10400")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
    CREATE TABLE gpkg_spatial_ref_sys (
      srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
      organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL,
      definition TEXT NOT NULL, description TEXT);
    CREATE TABLE gpkg_contents (
      table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
      identifier TEXT UNIQUE, description TEXT DEFAULT '',
      last_change DATETIME NOT NULL, min_x REAL, min_y REAL, max_x REAL, max_y REAL,
      srs_id INTEGER, FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id));
    CREATE TABLE gpkg_geometry_columns (
      table_name TEXT NOT NULL, column_name TEXT NOT NULL,
      geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL,
      z TINYINT NOT NULL, m TINYINT NOT NULL,
      PRIMARY KEY (table_name, column_name),
      FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
      FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id));
    CREATE TABLE gpkg_tile_matrix_set (
      table_name TEXT NOT NULL PRIMARY KEY, srs_id INTEGER NOT NULL,
      min_x REAL NOT NULL, min_y REAL NOT NULL, max_x REAL NOT NULL, max_y REAL NOT NULL,
      FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
      FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id));
    CREATE TABLE gpkg_tile_matrix (
      table_name TEXT NOT NULL, zoom_level INTEGER NOT NULL,
      matrix_width INTEGER NOT NULL, matrix_height INTEGER NOT NULL,
      tile_width INTEGER NOT NULL, tile_height INTEGER NOT NULL,
      pixel_x_size REAL NOT NULL, pixel_y_size REAL NOT NULL,
      PRIMARY KEY (table_name, zoom_level),
      FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name));
    CREATE TABLE gpkg_extensions (
      table_name TEXT, column_name TEXT, extension_name TEXT NOT NULL,
      definition TEXT NOT NULL, scope TEXT NOT NULL,
      UNIQUE (table_name, column_name, extension_name));
    CREATE TABLE gpkg_metadata (
      id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      md_scope TEXT NOT NULL DEFAULT 'dataset', md_standard_uri TEXT NOT NULL,
      mime_type TEXT NOT NULL DEFAULT 'text/xml', metadata TEXT NOT NULL DEFAULT '');
    CREATE TABLE gpkg_metadata_reference (
      reference_scope TEXT NOT NULL, table_name TEXT, column_name TEXT,
      row_id_value INTEGER, timestamp DATETIME NOT NULL,
      md_file_id INTEGER NOT NULL, md_parent_id INTEGER,
      FOREIGN KEY (md_file_id) REFERENCES gpkg_metadata(id),
      FOREIGN KEY (md_parent_id) REFERENCES gpkg_metadata(id));

    CREATE TABLE ta_projeto (
      id INTEGER PRIMARY KEY, projeto TEXT NOT NULL, territorio TEXT NOT NULL,
      municipio TEXT NOT NULL, uf TEXT NOT NULL, versao TEXT NOT NULL,
      codigo_versao TEXT NOT NULL, situacao TEXT NOT NULL,
      crs_geografico INTEGER NOT NULL, crs_metrico INTEGER NOT NULL,
      criado_em TEXT NOT NULL, responsavel_institucional TEXT);
    CREATE TABLE ta_catalogo_fontes (
      id_fonte TEXT PRIMARY KEY, nome TEXT NOT NULL, tipo TEXT NOT NULL,
      caminho_relativo TEXT NOT NULL, formato TEXT, quantidade_arquivos INTEGER,
      tamanho_bytes INTEGER, criado_em_arquivo TEXT, modificado_em_arquivo TEXT,
      recebido_em TEXT NOT NULL, sha256 TEXT, classificacao_acesso TEXT NOT NULL,
      situacao TEXT NOT NULL, observacoes TEXT);
    CREATE TABLE ta_catalogo_camadas (
      id_camada TEXT PRIMARY KEY, id_fonte TEXT NOT NULL,
      nome_origem TEXT NOT NULL, nome_proposto TEXT NOT NULL,
      grupo_tematico TEXT NOT NULL, geometria TEXT, quantidade_registros INTEGER,
      crs_epsg INTEGER, crs_original TEXT, classificacao_acesso TEXT NOT NULL,
      situacao_validacao TEXT NOT NULL, observacoes TEXT,
      FOREIGN KEY (id_fonte) REFERENCES ta_catalogo_fontes(id_fonte));
    CREATE TABLE ta_catalogo_campos (
      id INTEGER PRIMARY KEY AUTOINCREMENT, id_camada TEXT NOT NULL,
      nome_origem TEXT NOT NULL, nome_padronizado TEXT, tipo_origem TEXT,
      descricao TEXT, sensivel INTEGER NOT NULL DEFAULT 0, regra_tratamento TEXT,
      FOREIGN KEY (id_camada) REFERENCES ta_catalogo_camadas(id_camada));
    CREATE TABLE ta_regras (
      id_regra TEXT PRIMARY KEY, categoria TEXT NOT NULL, regra TEXT NOT NULL,
      origem TEXT NOT NULL, situacao TEXT NOT NULL, registrado_em TEXT NOT NULL);
    CREATE TABLE ta_linhagem (
      id INTEGER PRIMARY KEY AUTOINCREMENT, id_fonte TEXT NOT NULL,
      id_camada_destino TEXT, operacao TEXT NOT NULL, parametros TEXT,
      executado_em TEXT, responsavel TEXT, resultado TEXT,
      FOREIGN KEY (id_fonte) REFERENCES ta_catalogo_fontes(id_fonte));
    CREATE TABLE ta_validacoes (
      id INTEGER PRIMARY KEY AUTOINCREMENT, objeto_tipo TEXT NOT NULL,
      objeto_id TEXT NOT NULL, teste TEXT NOT NULL, resultado TEXT NOT NULL,
      detalhe TEXT, validado_em TEXT, responsavel TEXT);
    CREATE TABLE ta_historico_versoes (
      versao TEXT PRIMARY KEY, codigo_versao TEXT NOT NULL, data TEXT NOT NULL,
      descricao TEXT NOT NULL, situacao TEXT NOT NULL);
    """)

    conn.executemany(
        "INSERT INTO gpkg_spatial_ref_sys VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Undefined geographic SRS", -1, "NONE", -1, "undefined", "Undefined geographic coordinate reference system"),
            ("Undefined cartesian SRS", 0, "NONE", 0, "undefined", "Undefined Cartesian coordinate reference system"),
            ("WGS 84 geodetic", 4326, "EPSG", 4326, WKT_4326, "WGS 84 geographic 2D"),
            ("SIRGAS 2000", 4674, "EPSG", 4674, WKT_4674, "Brazilian official geographic reference"),
            ("SIRGAS 2000 / UTM zone 20S", 31980, "EPSG", 31980, WKT_31980, "Metric reference recommended for Manaus"),
        ],
    )
    descriptions = {
        "ta_projeto": "Identificacao da Base Geo",
        "ta_catalogo_fontes": "Inventario das fontes",
        "ta_catalogo_camadas": "Catalogo das camadas identificadas",
        "ta_catalogo_campos": "Dicionario de campos",
        "ta_regras": "Regras de governanca e tratamento",
        "ta_linhagem": "Rastreabilidade das transformacoes",
        "ta_validacoes": "Resultados de validacao",
        "ta_historico_versoes": "Historico da Base Geo",
    }
    for name, description in descriptions.items():
        conn.execute(
            "INSERT INTO gpkg_contents (table_name,data_type,identifier,description,last_change,srs_id) VALUES (?,'attributes',?,?,?,NULL)",
            (name, name, description, NOW),
        )


def populate(conn):
    manuals = list(WORKSPACE_ROOT.glob("Manual_do_Territ*Geotecnologia.pdf"))
    manual_rel = manuals[0].relative_to(WORKSPACE_ROOT).as_posix() if manuals else "Manual_do_Territorio_Agentico_em_Geotecnologia.pdf"
    source_specs = [
        ("fonte_001", "Manual do Territorio Agentico em Geotecnologia", "documento_normativo", manual_rel, "PDF", "interna", "catalogada", "Manual institucional v1.0 - 2026."),
        ("fonte_002", "Bairros e zonas de Manaus", "base_geoespacial", "01 BaseDadosGeoExterna/BAIRROS E ZONAS MANAUS.gpkg", "GPKG", "interna", "aguardando_validacao", "Uma camada poligonal."),
        ("fonte_003", "Localidades de Manaus", "base_geoespacial", "01 BaseDadosGeoExterna/LOCALIDADES MANAUS.gpkg", "GPKG", "interna", "aguardando_validacao", "Uma camada poligonal."),
        ("fonte_004", "Escolas", "base_geoespacial", "01 BaseDadosGeoExterna/escolas.gdb", "FileGDB", "restrita", "aguardando_validacao", "Inclui contatos, contratos e campos potencialmente sensiveis."),
        ("fonte_005", "Lotes", "base_geoespacial", "01 BaseDadosGeoExterna/LOTES.gdb", "FileGDB", "restrita", "aguardando_validacao", "Base volumosa; integrar por caso de uso."),
        ("fonte_006", "Setores censitarios 2022", "base_geoespacial", "01 BaseDadosGeoExterna/SETORES.gdb", "FileGDB", "interna", "aguardando_validacao", "Base censitaria com atributos populacionais."),
        ("fonte_007", "Arquivo compactado de escolas", "arquivo_compactado", "01 BaseDadosGeoExterna/escolas.gdb.rar", "RAR", "restrita", "referencia_auxiliar", "Preservar como recebido."),
        ("fonte_008", "Geodatabase de lotes em subpasta", "base_geoespacial", "01 BaseDadosGeoExterna/LOTES/Novo Arquivo Geodatabase.gdb", "FileGDB", "restrita", "pendente_acesso", "GDAL informou permissao negada."),
    ]
    rows = []
    for source_id, name, kind, relative, fmt, access, status, notes in source_specs:
        full = WORKSPACE_ROOT / relative
        if full.exists():
            count, size, created, modified, digest = stats(full)
        else:
            count, size, created, modified, digest = 0, 0, None, None, None
            status = "nao_localizada"
        rows.append((source_id, name, kind, relative, fmt, count, size, created, modified, NOW, digest, access, status, notes))
    conn.executemany("INSERT INTO ta_catalogo_fontes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)

    layers = [
        ("cam_001", "fonte_002", "BAIRROS E ZONAS_bairros_e_zonas", "ref_bairros_zonas_manaus", "referencia_territorial", "POLYGON", 64, 4674, "SIRGAS 2000 sem autoridade EPSG declarada", "interna", "pendente", "Confirmar fonte, data e validade geometrica."),
        ("cam_002", "fonte_003", "LOCALIDADES MANAUS_LOCALIDADES4_shp", "ref_localidades_manaus", "referencia_territorial", "POLYGON", 663, 4674, "SIRGAS 2000 sem autoridade EPSG declarada", "interna", "pendente", "Confirmar conceito de localidade e sobreposicoes."),
        ("cam_003", "fonte_004", "Escolas", "edu_escolas_manaus", "rede_educacional", "POINT", 544, None, "semef_SIR2000 personalizado: TM, meridiano -60, FE 400000, FN 5000000", "restrita", "pendente_crs_e_sensibilidade", "Nao converter para EPSG:31980 sem teste e validacao visual."),
        ("cam_004", "fonte_005", "LOTES", "cad_lotes_manaus", "cadastro_territorial", "MULTIPOLYGON", 442463, None, "semef_SIR2000 personalizado: TM, meridiano -60, FE 400000, FN 5000000", "restrita", "pendente_crs_e_escopo", "Integrar somente campos e recortes necessarios."),
        ("cam_005", "fonte_006", "SETORES_CENSITARIOS_2022", "ref_setores_censitarios_manaus_2022", "referencia_territorial", "MULTIPOLYGON", 3210, None, "semef_SIR2000 personalizado: TM, meridiano -60, FE 400000, FN 5000000", "interna", "pendente_crs", "Validar codigos IBGE e compatibilidade com malha oficial."),
    ]
    conn.executemany("INSERT INTO ta_catalogo_camadas VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", layers)

    fields = [
        ("cam_001", "OBJECTID", "id_origem", "INTEGER", "Identificador original", 0, "preservar"),
        ("cam_001", "NOME_BAIRR", "nome_bairro", "TEXT", "Nome do bairro", 0, "padronizar texto"),
        ("cam_001", "ZONAS", "zona", "TEXT", "Zona administrativa", 0, "validar dominio"),
        ("cam_002", "NOME_LOCAL", "nome_localidade", "TEXT", "Nome da localidade", 0, "padronizar texto"),
        ("cam_003", "INEP", "codigo_inep", "REAL", "Codigo INEP", 0, "converter para texto e preservar zeros"),
        ("cam_003", "ESCOLA", "nome_escola", "TEXT", "Nome da unidade", 0, "padronizar texto"),
        ("cam_003", "GESTOR", "gestor", "TEXT", "Nome do gestor", 1, "restringir acesso"),
        ("cam_003", "CONTATO", "contato", "TEXT", "Contato institucional ou pessoal", 1, "restringir acesso"),
        ("cam_003", "TELEFONE", "telefone", "TEXT", "Telefone", 1, "restringir acesso"),
        ("cam_004", "CGL", "cgl", "TEXT", "Codigo geral do lote", 0, "validar unicidade"),
        ("cam_005", "CD_SETOR", "codigo_setor", "TEXT", "Codigo do setor censitario", 0, "preservar como texto"),
        ("cam_005", "TOTAL_PESSOAS", "total_pessoas", "REAL", "Populacao total", 0, "validar com fonte IBGE"),
    ]
    conn.executemany(
        "INSERT INTO ta_catalogo_campos (id_camada,nome_origem,nome_padronizado,tipo_origem,descricao,sensivel,regra_tratamento) VALUES (?,?,?,?,?,?,?)",
        fields,
    )

    rules = [
        ("reg_001", "preservacao", "Nao alterar, mover ou sobrescrever arquivos originais.", "usuario_e_manual", "aprovada", NOW),
        ("reg_002", "instrucoes", "Catalogar instrucoes e negociar conflitos antes de aplica-las.", "usuario", "aprovada", NOW),
        ("reg_003", "validacao", "Resultados institucionais dependem de validacao tecnica humana.", "usuario_e_manual", "aprovada", NOW),
        ("reg_004", "nomenclatura", "Identificar produtos com territorio, projeto e versao.", "usuario", "aprovada", NOW),
        ("reg_005", "crs", "Usar EPSG:4674 e EPSG:31980 somente apos confirmar o CRS de origem.", "padrao_tecnico", "aprovada", NOW),
        ("reg_006", "seguranca", "Nao expor dados pessoais, contatos ou informacoes contratuais.", "manual", "aprovada", NOW),
        ("reg_007", "rastreabilidade", "Registrar fonte, data, operacao, parametro, responsavel e resultado.", "manual", "aprovada", NOW),
        ("reg_008", "integracao", "Nao importar bases pesadas antes de definir o caso de uso.", "analise_inicial", "proposta_tecnica", NOW),
    ]
    conn.executemany("INSERT INTO ta_regras VALUES (?,?,?,?,?,?)", rules)
    conn.execute(
        "INSERT INTO ta_projeto VALUES (1,?,?,?,?,?,?,?,?,?,?,?)",
        ("Territorio Agentico Manaus", "manaus", "Manaus", "AM", "0.1.0", "v001", "estrutura_inicial_aguardando_validacao_tecnica", 4674, 31980, NOW, "SEMED Manaus - DGTI/Geotecnologia"),
    )
    conn.execute(
        "INSERT INTO ta_historico_versoes VALUES (?,?,?,?,?)",
        ("0.1.0", "v001", NOW[:10], "Estrutura, catalogo inicial e governanca.", "pre_validacao"),
    )
    validations = [
        ("fonte", "fonte_002", "abertura_gdal", "aprovado", "1 camada; 64 feicoes."),
        ("fonte", "fonte_003", "abertura_gdal", "aprovado", "1 camada; 663 feicoes."),
        ("fonte", "fonte_004", "abertura_gdal", "aprovado_com_pendencia", "544 feicoes; CRS personalizado."),
        ("fonte", "fonte_005", "abertura_gdal", "aprovado_com_pendencia", "442463 feicoes; CRS personalizado."),
        ("fonte", "fonte_006", "abertura_gdal", "aprovado_com_pendencia", "3210 feicoes; CRS personalizado."),
        ("fonte", "fonte_008", "abertura_gdal", "reprovado_temporariamente", "Permissao negada."),
    ]
    conn.executemany(
        "INSERT INTO ta_validacoes (objeto_tipo,objeto_id,teste,resultado,detalhe) VALUES (?,?,?,?,?)",
        validations,
    )


def metadata(conn):
    body = json.dumps({
        "title": "Base Geo do Territorio Agentico Manaus",
        "version": "0.1.0",
        "status": "estrutura inicial aguardando validacao tecnica",
        "responsible": "SEMED Manaus - DGTI/Geotecnologia",
        "created": NOW,
        "crs_geographic": "EPSG:4674",
        "crs_metric": "EPSG:31980",
    }, ensure_ascii=False)
    cursor = conn.execute(
        "INSERT INTO gpkg_metadata (md_scope,md_standard_uri,mime_type,metadata) VALUES ('geopackage',?,'application/json',?)",
        ("https://www.geopackage.org/spec140/", body),
    )
    conn.execute(
        "INSERT INTO gpkg_metadata_reference (reference_scope,timestamp,md_file_id) VALUES ('geopackage',?,?)",
        (NOW, cursor.lastrowid),
    )
    conn.execute(
        "INSERT INTO gpkg_extensions VALUES (NULL,NULL,'gpkg_metadata',?,'read-write')",
        ("https://www.geopackage.org/spec140/#extension_metadata",),
    )


def validate(conn):
    required = {"gpkg_spatial_ref_sys", "gpkg_contents", "gpkg_geometry_columns", "gpkg_tile_matrix_set", "gpkg_tile_matrix", "gpkg_extensions"}
    existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    issues = []
    if required - existing:
        issues.append("Missing OGC tables: " + ", ".join(sorted(required - existing)))
    if conn.execute("PRAGMA application_id").fetchone()[0] != 0x47504B47:
        issues.append("Invalid GeoPackage application_id")
    if conn.execute("PRAGMA user_version").fetchone()[0] != 10400:
        issues.append("Invalid GeoPackage user_version")
    for srs_id in (-1, 0, 4326, 4674, 31980):
        if not conn.execute("SELECT 1 FROM gpkg_spatial_ref_sys WHERE srs_id=?", (srs_id,)).fetchone():
            issues.append(f"Missing SRS {srs_id}")
    if conn.execute("PRAGMA foreign_key_check").fetchall():
        issues.append("Foreign key errors")
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        issues.append("SQLite integrity error")
    if issues:
        raise RuntimeError("; ".join(issues))


def export_files(conn):
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    for table, filename in [
        ("ta_catalogo_fontes", "manaus_catalogo_fontes_v001.csv"),
        ("ta_catalogo_camadas", "manaus_catalogo_camadas_v001.csv"),
        ("ta_catalogo_campos", "manaus_catalogo_campos_v001.csv"),
    ]:
        cursor = conn.execute(f'SELECT * FROM "{table}"')
        with (CATALOG_DIR / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow([item[0] for item in cursor.description])
            writer.writerows(cursor.fetchall())
    manifest = {
        "projeto": "Territorio Agentico Manaus",
        "versao": "0.1.0",
        "codigo_versao": "v001",
        "gerado_em": NOW,
        "geopackage": "03_base_geo/manaus_base_geo_v001.gpkg",
        "fontes_catalogadas": conn.execute("SELECT COUNT(*) FROM ta_catalogo_fontes").fetchone()[0],
        "camadas_identificadas": conn.execute("SELECT COUNT(*) FROM ta_catalogo_camadas").fetchone()[0],
        "campos_iniciais": conn.execute("SELECT COUNT(*) FROM ta_catalogo_campos").fetchone()[0],
        "regras_registradas": conn.execute("SELECT COUNT(*) FROM ta_regras").fetchone()[0],
        "situacao": "pre_validacao",
    }
    (CATALOG_DIR / "manaus_manifesto_v001.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    REPORT_PATH.write_text(
        "VALIDACAO ESTRUTURAL - MANAUS BASE GEO V001\n"
        f"Gerado em: {NOW}\n"
        "SQLite integrity_check: ok\n"
        "Foreign keys: ok\n"
        "GeoPackage application_id: ok\n"
        "GeoPackage user_version 1.4.0: ok\n"
        "SRS registrados: -1, 0, 4326, 4674, 31980\n"
        "Situacao: estrutura aprovada; dados aguardando validacao tecnica humana.\n",
        encoding="utf-8",
    )


def main():
    OUTPUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_GPKG.exists():
        raise FileExistsError(f"Base exists and will not be overwritten: {OUTPUT_GPKG}")
    conn = sqlite3.connect(OUTPUT_GPKG)
    try:
        schema(conn)
        populate(conn)
        metadata(conn)
        validate(conn)
        conn.commit()
        export_files(conn)
        conn.execute("VACUUM")
    except Exception:
        conn.close()
        OUTPUT_GPKG.unlink(missing_ok=True)
        raise
    else:
        conn.close()
    print(OUTPUT_GPKG)


if __name__ == "__main__":
    main()
