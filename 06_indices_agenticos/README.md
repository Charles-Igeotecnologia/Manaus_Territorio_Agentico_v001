# Indices agenticos - v002

Esta pasta abriga produtos derivados e leves destinados a consultas rapidas por agentes.

## Principios

- A fonte autoritativa continua sendo a camada vetorial catalogada, especialmente o GeoPackage quando assim definido.
- CSV, JSON, GeoJSON e Parquet sao derivados reproduziveis, nunca substitutos silenciosos da geometria oficial.
- Todo indice deve registrar fonte, camada, versao, CRS quando aplicavel, data de geracao e procedimento de derivacao.
- Operacoes espaciais reais (buffer, interseccao, distancia, area, reprojecao e similares) devem ser executadas sobre geometria validada por executor geoespacial.

## Produtos previstos

- `escolas.csv`
- `escolas_por_ddz.json`
- `escolas_por_bairro.json`
- `escolas_por_zona.json`
- `modalidades.json`
- `indicadores_educacionais.parquet`
- `manifest.json`

Os arquivos acima somente devem ser publicados apos geracao reproduzivel a partir da Base Geo validada.
