#!/usr/bin/env python3
"""Renderizador cartografico v002: separa dados geoespaciais da apresentacao."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LAYOUT = ROOT / "config" / "layouts" / "abnt_tecnico_v002.json"


def carregar_layout(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def renderizar(geojson, saida, layout_path=DEFAULT_LAYOUT, titulo=None):
    try:
        import geopandas as gpd
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("GeoPandas e Matplotlib sao necessarios para renderizacao.") from exc

    layout = carregar_layout(layout_path)
    gdf = gpd.read_file(geojson)
    if gdf.crs is None:
        raise ValueError("CRS ausente: renderizacao interrompida; nao e permitido inferir CRS.")
    if gdf.empty or gdf.geometry.isna().all():
        raise ValueError("GeoJSON sem geometria valida para renderizacao.")

    orientacao = layout.get("pagina", {}).get("orientacao_padrao", "paisagem")
    figsize = (11.69, 8.27) if orientacao == "paisagem" else (8.27, 11.69)
    fig, ax = plt.subplots(figsize=figsize)
    gdf.plot(ax=ax)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title(titulo or "Espacializacao das escolas - Base Geo")
    ax.set_axis_off()

    crs_txt = gdf.crs.to_string()
    rodape = f"CRS: {crs_txt} | Fonte: Base Geo | Gerado em: {datetime.now(timezone.utc).strftime('%Y-%m-%d')} UTC"
    fig.text(0.01, 0.01, rodape, fontsize=7)
    fig.tight_layout(rect=(0, 0.035, 1, 0.97))

    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida, bbox_inches="tight")
    plt.close(fig)

    return {
        "saida": str(saida),
        "layout": layout.get("id"),
        "layout_versao": layout.get("versao"),
        "crs_origem": crs_txt,
        "feicoes": int(len(gdf)),
        "geometria_alterada": False,
        "layout_editavel": bool(layout.get("principios", {}).get("layout_editavel", False)),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geojson", required=True, type=Path)
    p.add_argument("--saida", required=True, type=Path)
    p.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    p.add_argument("--titulo")
    args = p.parse_args()
    resultado = renderizar(args.geojson, args.saida, args.layout, args.titulo)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
