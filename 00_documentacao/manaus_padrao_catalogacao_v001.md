# Padrao de catalogacao - Manaus v001

## Identidade

- Nome do territorio: `manaus`.
- Nome do projeto: `territorio_agentico`.
- Codigo inicial: `v001`.
- GeoPackage: `manaus_base_geo_v001.gpkg`.

## Nomenclatura

Formato de camada: `<tema>_<objeto>_<recorte>[_<ano>]`.

Exemplos: `ref_bairros_manaus`, `ref_setores_censitarios_manaus_2022`, `edu_escolas_manaus` e `cad_lotes_manaus`.

Prefixos: `ref_` referencia territorial; `edu_` educacao; `pla_` planejamento; `cad_` cadastro; `amb_` ambiente; `inf_` infraestrutura; `tab_` tabela sem geometria.

## Metadados obrigatorios

Cada fonte e camada registra identificador, titulo, descricao, caminho, formato, instituicao, datas, responsavel, acesso, geometria, CRS, quantidade de registros, limitacoes, validacao e versao.

Data de criacao do arquivo, publicacao do dado, referencia temporal e entrada no projeto sao campos distintos.

## Sistemas de referencia

- Referencia geografica: SIRGAS 2000, `EPSG:4674`.
- Calculos metricos em Manaus: SIRGAS 2000 / UTM 20S, `EPSG:31980`.
- CRS local ou personalizado permanece no original ate validacao.
- `semef_SIR2000` e personalizado e nao deve ser rotulado automaticamente como `EPSG:31980`.

## Governanca

- Originais sao imutaveis.
- Instrucoes documentais sao catalogadas e negociadas quando alterarem regras.
- Dados pessoais ou contratuais recebem classificacao restrita.
- Bases pesadas podem permanecer externas com caminho autorizado e metadados.
- Nenhum produto e institucional antes da validacao humana.
