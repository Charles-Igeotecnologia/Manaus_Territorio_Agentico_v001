#!/usr/bin/env python3
"""Build the sanitized GeoPackage candidate intended for GitHub distribution."""

import hashlib
import os
import shutil
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

VERSION_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = VERSION_ROOT.parent
DATA_ROOT = WORKSPACE_ROOT / "01 BaseDadosGeoExterna"
PUBLIC_DIR = VERSION_ROOT / "dados_publicados"
OUTPUT = PUBLIC_DIR / "manaus_base_consulta_v001.gpkg"
OGR2OGR = Path(
    os.environ.get("OGR2OGR")
    or shutil.which("ogr2ogr")
    or r"C:\Program Files\QGIS 3.34.4\bin\ogr2ogr.exe"
)
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

LAYERS = [
    {
        "source": DATA_ROOT / "BAIRROS E ZONAS MANAUS.gpkg",
        "sql": 'SELECT OBJECTID AS id_origem, NOME_BAIRR AS nome_bairro, ZONAS AS zona FROM "BAIRROS E ZONAS_bairros_e_zonas"',
        "name": "ref_bairros_zonas_manaus",
        "geometry": "MULTIPOLYGON",
        "count": 64,
        "description": "Bairros e zonas de Manaus para referencia territorial.",
        "access": "publicacao_condicionada",
    },
    {
        "source": DATA_ROOT / "LOCALIDADES MANAUS.gpkg",
        "sql": 'SELECT NOME_LOCAL AS nome_localidade, ESTADO AS uf, MUNICIPI_1 AS codigo_municipio, TIPO_1 AS tipo_localidade, NOME AS nome_auxiliar, BAIRRO_1 AS bairro, ZONAS AS zona FROM "LOCALIDADES MANAUS_LOCALIDADES4_shp"',
        "name": "ref_localidades_manaus",
        "geometry": "MULTIPOLYGON",
        "count": 663,
        "description": "Localidades de Manaus para referencia territorial.",
        "access": "publicacao_condicionada",
    },
    {
        "source": DATA_ROOT / "escolas.gdb",
        "sql": 'SELECT CAST(SIGEAM AS CHARACTER(32)) AS codigo_sigeam, CAST(INEP AS CHARACTER(32)) AS codigo_inep, ESCOLA AS nome_escola, ESCOLA_GED AS nome_escola_ged, DDZ AS ddz, DISTRITO AS distrito, BAIRRO AS bairro, ZONAS AS zona, MODALIDADE AS modalidade, SALAS AS salas, TURMAS AS turmas, EDUCACAO_ESPECIAL AS educacao_especial, ESP_EJA AS esp_eja, BER AS ber, CRECHE_I AS creche_i, CRECHE_II AS creche_ii, CRECHE_III AS creche_iii, PRE_1 AS pre_1, PRE_2 AS pre_2, FUNDAMENTAL_1 AS fundamental_1, FUNDAMENTAL_2 AS fundamental_2, FUNDAMENTAL_3 AS fundamental_3, FUNDAMENTAL_4 AS fundamental_4, FUNDAMENTAL_5 AS fundamental_5, FUNDAMENTAL_6 AS fundamental_6, FUNDAMENTAL_7 AS fundamental_7, FUNDAMENTAL_8 AS fundamental_8, FUNDAMENTAL_9 AS fundamental_9, IAS_1_FA AS ias_1_fa, IAS_2_FA AS ias_2_fa, EJA_1_SE AS eja_1_se, EJA_2_SE AS eja_2_se, SRM AS srm, SR AS sr, SME AS sme, SREF AS sref, STATUS AS status, TIPO AS tipo, ALUNOS AS alunos, REGIAO AS regiao, PATRIMONIO_PUBLICO AS patrimonio_publico FROM Escolas',
        "name": "edu_escolas_manaus",
        "geometry": "POINT",
        "count": 544,
        "description": "Unidades educacionais sem contatos, gestores, contratos ou processos.",
        "access": "publicacao_condicionada",
    },
    {
        "source": DATA_ROOT / "SETORES.gdb",
        "sql": 'SELECT CD_SETOR AS codigo_setor, AREA_KM2 AS area_km2, CD_REGIAO AS codigo_regiao, NM_REGIAO AS nome_regiao, CD_UF AS codigo_uf, NM_UF AS nome_uf, CD_MUN AS codigo_municipio, NM_MUN AS nome_municipio, CD_DIST AS codigo_distrito, NM_DIST AS nome_distrito, CD_SUBDIST AS codigo_subdistrito, NM_SUBDIST AS nome_subdistrito, TOTAL_PESSOAS AS total_pessoas, TOTAL_DOMICILIOS AS total_domicilios, TOTAL_DOMICILIOS_PARTICULARES AS total_domicilios_particulares, TOTAL_DOMICILIOS_COLETIVOS AS total_domicilios_coletivos, MEDIA_MORAD_DOM_PARTI_OCUP AS media_moradores_domicilios_ocupados, PERCENTUAL_DOM_PART_OCU_IMPUT AS percentual_domicilios_ocupados_imputados, TOTAL_DOM_PARTI_OCUPADOS AS total_domicilios_particulares_ocupados, BAIRRO_GEOTI AS bairro_geoti, COD_BAI_STI AS codigo_bairro_sti, COD_BAI_STM AS codigo_bairro_stm FROM SETORES_CENSITARIOS_2022',
        "name": "ref_setores_censitarios_manaus_2022",
        "geometry": "MULTIPOLYGON",
        "count": 3210,
        "description": "Setores censitarios 2022 com indicadores agregados.",
        "access": "publicacao_condicionada",
    },
]

BANNED_SCHOOL_FIELDS = {
    "gestor", "contato", "telefone", "ramal_corporativo", "contratado",
    "endereco_locador", "observacao_contrato", "valor_mensal", "valor_anual",
    "numero_contrato_ano_ta", "processo_siged", "processo_protus",
    "setor_atual", "link_siged", "created_user", "last_edited_user",
}


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def add_layer(layer, append):
    command = [
        str(OGR2OGR),
        "-f", "GPKG",
        "-t_srs", "EPSG:4674",
        "-makevalid",
        "-dim", "XY",
        "-nln", layer["name"],
        "-nlt", layer["geometry"],
        "-lco", "GEOMETRY_NAME=geom",
        "-lco", "FID=fid",
        "-lco", "SPATIAL_INDEX=YES",
        "-lco", f"IDENTIFIER={layer['name']}",
        "-lco", f"DESCRIPTION={layer['description']}",
    ]
    if append:
        command.extend(["-update", "-append"])
    command.extend([
        str(OUTPUT),
        str(layer["source"]),
        "-dialect", "OGRSQL",
        "-sql", layer["sql"],
    ])
    run(command)


def add_catalog_and_metadata():
    conn = sqlite3.connect(OUTPUT)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE pub_catalogo_camadas (
                camada TEXT PRIMARY KEY,
                tema TEXT NOT NULL,
                fonte TEXT NOT NULL,
                registros INTEGER NOT NULL,
                crs TEXT NOT NULL,
                acesso TEXT NOT NULL,
                descricao TEXT NOT NULL,
                publicado_em TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE pub_regras_uso (
                id INTEGER PRIMARY KEY,
                regra TEXT NOT NULL
            )
        """)
        for table, description in [
            ("pub_catalogo_camadas", "Catalogo das camadas publicaveis"),
            ("pub_regras_uso", "Regras de uso da base de consulta"),
        ]:
            conn.execute("""
                INSERT INTO gpkg_contents
                (table_name,data_type,identifier,description,last_change,srs_id)
                VALUES (?,'attributes',?,?,?,NULL)
            """, (table, table, description, NOW))
        rows = []
        for layer in LAYERS:
            theme = "rede_educacional" if layer["name"].startswith("edu_") else "referencia_territorial"
            rows.append((
                layer["name"],
                theme,
                layer["source"].name,
                layer["count"],
                "EPSG:4674",
                layer["access"],
                layer["description"],
                NOW,
            ))
        conn.executemany("INSERT INTO pub_catalogo_camadas VALUES (?,?,?,?,?,?,?,?)", rows)
        conn.executemany(
            "INSERT INTO pub_regras_uso VALUES (?,?)",
            [
                (1, "Base candidata; exige validacao tecnica antes da publicacao institucional."),
                (2, "Nao contem gestores, contatos, telefones, contratos, valores, processos ou links internos."),
                (3, "Lotes cadastrais detalhados nao fazem parte desta versao."),
                (4, "Resultados devem informar camada, fonte e data de consulta."),
                (5, "Nao combinar esta base com dados pessoais para reidentificacao."),
            ],
        )
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS gpkg_metadata (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                md_scope TEXT NOT NULL DEFAULT 'dataset',
                md_standard_uri TEXT NOT NULL,
                mime_type TEXT NOT NULL DEFAULT 'text/xml',
                metadata TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS gpkg_metadata_reference (
                reference_scope TEXT NOT NULL,
                table_name TEXT,
                column_name TEXT,
                row_id_value INTEGER,
                timestamp DATETIME NOT NULL,
                md_file_id INTEGER NOT NULL,
                md_parent_id INTEGER,
                FOREIGN KEY (md_file_id) REFERENCES gpkg_metadata(id),
                FOREIGN KEY (md_parent_id) REFERENCES gpkg_metadata(id)
            );
        """)
        metadata = json.dumps({
            "title": "Manaus Base de Consulta v001",
            "territory": "Manaus",
            "status": "candidato_nao_publicado",
            "crs": "EPSG:4674",
            "created": NOW,
            "layers": [layer["name"] for layer in LAYERS],
            "excluded": ["lotes_detalhados", "dados_pessoais", "contatos", "contratos", "processos", "links_internos"],
        }, ensure_ascii=False)
        cursor = conn.execute("""
            INSERT INTO gpkg_metadata
            (md_scope,md_standard_uri,mime_type,metadata)
            VALUES ('geopackage','https://www.geopackage.org/spec140/','application/json',?)
        """, (metadata,))
        conn.execute("""
            INSERT INTO gpkg_metadata_reference
            (reference_scope,timestamp,md_file_id)
            VALUES ('geopackage',?,?)
        """, (NOW, cursor.lastrowid))
        conn.execute("""
            INSERT OR IGNORE INTO gpkg_extensions
            (table_name,column_name,extension_name,definition,scope)
            VALUES (NULL,NULL,'gpkg_metadata',
                    'https://www.geopackage.org/spec140/#extension_metadata',
                    'read-write')
        """)
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()


def validate():
    conn = sqlite3.connect(OUTPUT)
    try:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")
        if conn.execute("PRAGMA application_id").fetchone()[0] != 0x47504B47:
            raise RuntimeError("Invalid GeoPackage application_id")
        for layer in LAYERS:
            count = conn.execute(f'SELECT COUNT(*) FROM "{layer["name"]}"').fetchone()[0]
            if count != layer["count"]:
                raise RuntimeError(f'Unexpected count for {layer["name"]}: {count}')
            srs = conn.execute(
                "SELECT srs_id FROM gpkg_contents WHERE table_name=?", (layer["name"],)
            ).fetchone()[0]
            if srs != 4674:
                raise RuntimeError(f'Unexpected CRS for {layer["name"]}: {srs}')
        school_fields = {
            row[1].lower() for row in conn.execute('PRAGMA table_info("edu_escolas_manaus")')
        }
        exposed = BANNED_SCHOOL_FIELDS & school_fields
        if exposed:
            raise RuntimeError("Sensitive school fields exposed: " + ", ".join(sorted(exposed)))
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Foreign key check failed")
    finally:
        conn.close()


def write_support_files():
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    (PUBLIC_DIR / "manaus_base_consulta_v001.sha256").write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="ascii"
    )
    catalog = {
        "project": "Manaus Territorio Agentico v001",
        "status": "candidato_nao_publicado",
        "file": OUTPUT.name,
        "sha256": digest,
        "crs": "EPSG:4674",
        "created": NOW,
        "layers": [
            {
                "name": layer["name"],
                "records": layer["count"],
                "description": layer["description"],
                "access": layer["access"],
            }
            for layer in LAYERS
        ],
        "excluded": {
            "cad_lotes_manaus": "volume e sensibilidade cadastral; requer decisao tecnica",
            "school_fields": sorted(BANNED_SCHOOL_FIELDS),
        },
    }
    (PUBLIC_DIR / "manaus_base_consulta_v001_catalogo.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (PUBLIC_DIR / "README.md").write_text(
        "# Dados publicados - candidato v001\n\n"
        "GeoPackage enxuto para consultas do Territorio Agentico de Manaus.\n\n"
        "## Camadas\n\n"
        "- ref_bairros_zonas_manaus: 64 feicoes.\n"
        "- ref_localidades_manaus: 663 feicoes.\n"
        "- edu_escolas_manaus: 544 feicoes, sem dados pessoais ou contratuais.\n"
        "- ref_setores_censitarios_manaus_2022: 3.210 feicoes.\n\n"
        "## Situacao\n\n"
        "Candidato local. Nao publicar antes da validacao humana das fontes, licencas, campos e geometrias.\n"
        "A camada detalhada de lotes foi excluida por volume e sensibilidade cadastral.\n",
        encoding="utf-8",
    )


def update_root_catalog():
    path = VERSION_ROOT / "catalogo.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog["base_consulta_github"] = {
        "arquivo": "dados_publicados/manaus_base_consulta_v001.gpkg",
        "catalogo": "dados_publicados/manaus_base_consulta_v001_catalogo.json",
        "status": "candidato_nao_publicado",
        "crs": "EPSG:4674",
        "camadas": [layer["name"] for layer in LAYERS],
        "exclusoes": ["lotes_detalhados", "dados_pessoais", "dados_contratuais"],
    }
    catalog["atualizado_em"] = NOW
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if not OGR2OGR.exists():
        raise FileNotFoundError(OGR2OGR)
    for layer in LAYERS:
        if not layer["source"].exists():
            raise FileNotFoundError(layer["source"])
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        raise FileExistsError(f"Candidate already exists and will not be overwritten: {OUTPUT}")
    try:
        for index, layer in enumerate(LAYERS):
            add_layer(layer, append=index > 0)
        add_catalog_and_metadata()
        validate()
        write_support_files()
        update_root_catalog()
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT)


if __name__ == "__main__":
    main()

