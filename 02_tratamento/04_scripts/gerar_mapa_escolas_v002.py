#!/usr/bin/env python3
"""Pipeline v002: Base Geo -> GeoJSON derivado -> mapa tecnico, sem alterar a fonte."""

import argparse
import json
from pathlib import Path

from executor_geoespacial_v002 import DEFAULT_GPKG, espacializar_escolas
from renderizador_cartografico_v002 import DEFAULT_LAYOUT, renderizar


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gpkg", type=Path, default=DEFAULT_GPKG)
    p.add_argument("--campo")
    p.add_argument("--valor")
    p.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    p.add_argument("--geojson", type=Path, default=Path("06_produtos/mapas_v002/escolas.geojson"))
    p.add_argument("--saida", type=Path, default=Path("06_produtos/mapas_v002/escolas_abnt_tecnico.pdf"))
    p.add_argument("--titulo")
    args = p.parse_args()

    espacial = espacializar_escolas(args.gpkg, args.campo, args.valor, args.geojson)
    mapa = renderizar(args.geojson, args.saida, args.layout, args.titulo)

    print(json.dumps({
        "status": "gerado",
        "fonte_alterada": False,
        "espacializacao": espacial,
        "mapa": mapa,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
