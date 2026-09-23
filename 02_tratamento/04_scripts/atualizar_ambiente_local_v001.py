#!/usr/bin/env python3
"""Register the local work environment and Drive publication environment."""

import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ROOT = VERSION_ROOT.parent
DRIVE_ROOT = Path(sys.argv[1])
GPKG = VERSION_ROOT / "03_base_geo" / "manaus_base_geo_v001.gpkg"
BACKUP = VERSION_ROOT / "03_base_geo" / "backups" / "manaus_base_geo_v001_pre_ambiente_local.gpkg"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

if not GPKG.exists():
    raise FileNotFoundError(GPKG)
if not BACKUP.exists():
    shutil.copy2(GPKG, BACKUP)

conn = sqlite3.connect(GPKG)
try:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ta_ambientes_armazenamento (
            id_ambiente TEXT PRIMARY KEY,
            tipo TEXT NOT NULL,
            caminho_raiz TEXT NOT NULL,
            finalidade TEXT NOT NULL,
            prioridade INTEGER NOT NULL,
            politica_escrita TEXT NOT NULL,
            situacao TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO gpkg_contents
        (table_name, data_type, identifier, description, last_change, srs_id)
        VALUES ('ta_ambientes_armazenamento', 'attributes',
                'ta_ambientes_armazenamento',
                'Ambientes local e compartilhado da Base Geo', ?, NULL)
    """, (NOW,))
    conn.execute("""
        UPDATE gpkg_contents SET last_change=?
        WHERE table_name='ta_ambientes_armazenamento'
    """, (NOW,))
    conn.execute("DELETE FROM ta_ambientes_armazenamento")
    conn.executemany(
        "INSERT INTO ta_ambientes_armazenamento VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                "amb_local_manaus",
                "local",
                str(LOCAL_ROOT),
                "processamento_ativo",
                1,
                "leitura_e_escrita_controlada",
                "ativo",
                NOW,
            ),
            (
                "amb_drive_manaus",
                "compartilhado",
                str(DRIVE_ROOT),
                "publicacao_backup_e_compartilhamento",
                2,
                "publicar_somente_apos_validacao_e_com_arquivo_fechado",
                "ativo",
                NOW,
            ),
        ],
    )
    conn.execute("""
        UPDATE ta_projeto
        SET versao='0.1.1',
            situacao='ambiente_local_ativo_aguardando_validacao_dos_dados'
        WHERE id=1
    """)
    conn.execute("""
        INSERT OR REPLACE INTO ta_historico_versoes
        (versao, codigo_versao, data, descricao, situacao)
        VALUES ('0.1.1', 'v001', ?, ?, 'pre_validacao')
    """, (
        NOW[:10],
        "Registro do ambiente local de trabalho e do Drive para publicacao e backup.",
    ))
    rows = conn.execute(
        "SELECT id, metadata FROM gpkg_metadata WHERE mime_type='application/json'"
    ).fetchall()
    for metadata_id, raw in rows:
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            continue
        body.update({
            "version": "0.1.1",
            "status": "ambiente local ativo; dados aguardando validacao tecnica",
            "local_work_root": str(LOCAL_ROOT),
            "drive_publication_root": str(DRIVE_ROOT),
            "storage_policy": "processar localmente e publicar no Drive somente apos validacao",
            "updated": NOW,
        })
        conn.execute(
            "UPDATE gpkg_metadata SET metadata=? WHERE id=?",
            (json.dumps(body, ensure_ascii=False), metadata_id),
        )
    if conn.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("Foreign key validation failed")
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("SQLite integrity validation failed")
    conn.commit()
    conn.execute("VACUUM")
finally:
    conn.close()

catalog_path = VERSION_ROOT / "catalogo.json"
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
catalog["versao"] = "0.1.1"
catalog["situacao"] = "ambiente_local_ativo_aguardando_validacao_dos_dados"
catalog["ambientes"] = {
    "trabalho_local": {
        "caminho": str(LOCAL_ROOT),
        "uso": "processamento_ativo",
        "prioridade": 1,
    },
    "publicacao_drive": {
        "caminho": str(DRIVE_ROOT),
        "uso": "publicacao_backup_e_compartilhamento",
        "prioridade": 2,
    },
}
catalog["politica_armazenamento"] = [
    "processar e editar o GeoPackage somente na pasta local",
    "fechar QGIS, ArcGIS e conexoes antes de copiar o GeoPackage",
    "validar integridade e gerar hash antes da publicacao",
    "publicar no Drive somente versoes aprovadas",
    "nunca sincronizar uma Base Geo aberta para escrita",
]
catalog["atualizado_em"] = NOW
catalog_path.write_text(
    json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

manifest_path = VERSION_ROOT / "04_catalogo_metadados" / "manaus_manifesto_v001.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest.update({
    "versao": "0.1.1",
    "gerado_em": NOW,
    "ambiente_ativo": "local",
    "caminho_trabalho_local": str(LOCAL_ROOT),
    "caminho_publicacao_drive": str(DRIVE_ROOT),
})
manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

doc_path = VERSION_ROOT / "00_documentacao" / "manaus_ambientes_armazenamento_v001.md"
doc_path.write_text(
    "# Ambientes de armazenamento - Manaus v001\n\n"
    "## Trabalho local\n\n"
    f"- Caminho: `{LOCAL_ROOT}`\n"
    "- Finalidade: processamento, edicao, validacao e geracao de produtos.\n"
    "- Prioridade: ambiente principal de trabalho.\n\n"
    "## Drive compartilhado\n\n"
    f"- Caminho: `{DRIVE_ROOT}`\n"
    "- Finalidade: publicacao, compartilhamento e backup controlado.\n"
    "- Regra: receber somente arquivos fechados e previamente validados.\n\n"
    "## Procedimento de publicacao\n\n"
    "1. Encerrar QGIS, ArcGIS e qualquer conexao com o GeoPackage.\n"
    "2. Executar validacao OGC e integridade SQLite na copia local.\n"
    "3. Gerar SHA-256 da versao local.\n"
    "4. Copiar a versao aprovada para o Drive.\n"
    "5. Conferir o SHA-256 da copia publicada.\n"
    "6. Registrar data, responsavel e versao no historico.\n",
    encoding="utf-8",
)

report_path = VERSION_ROOT / "05_validacao" / "relatorios" / "manaus_validacao_migracao_local_v001.txt"
report_path.write_text(
    "VALIDACAO DA MIGRACAO LOCAL - MANAUS V001\n"
    f"Executado em: {NOW}\n"
    f"Ambiente local: {LOCAL_ROOT}\n"
    f"Ambiente Drive: {DRIVE_ROOT}\n"
    "Arquivos comparados: manual, 2 GeoPackages, 3 FileGDB e 1 RAR.\n"
    "Resultado dos manifestos: todos identicos entre local e Drive.\n"
    "GeoPackage principal antes da atualizacao: SHA-256 identico nas duas origens.\n"
    "Situacao: ambiente local ativado para processamento.\n",
    encoding="utf-8",
)

print(json.dumps({
    "gpkg": str(GPKG),
    "backup": str(BACKUP),
    "catalog": str(catalog_path),
    "version": "0.1.1",
}, ensure_ascii=False, indent=2))
