# Arquitetura de Consulta Agentica - v0.02

## Fluxo

1. Interpretar a pergunta sem inferir geometria.
2. Ler `catalogo.json`, metadados e `06_indices_agenticos/manifest.json` quando disponivel.
3. Resolver consultas descritivas por indice leve quando suficiente.
4. Encaminhar operacoes espaciais ao executor geoespacial e a fonte autoritativa.
5. Validar o CRS antes de qualquer calculo metrico ou transformacao.
6. Declarar ao solicitante toda transformacao: origem, destino, motivo, operacao afetada e preservacao do original.
7. Produzir mapa quando a dimensao territorial for relevante e houver geometria validada.
8. Registrar fonte, camada, versao, CRS e auditoria da operacao.

## Fonte e derivados

O GeoPackage catalogado permanece autoritativo para geometria. CSV, JSON, GeoJSON e outros indices sao derivados para acelerar consultas e devem ser regeneraveis.

## Regra de geometria

**Geometria por evidencia, nunca por inferencia.**

Se uma feicao nao possuir geometria validada disponivel, o agente deve declarar a limitacao e nao fabricar coordenadas, poligonos ou limites.

## CRS

SIRGAS 2000 geografico (`EPSG:4674`) pode ser usado para interoperabilidade. A definicao institucional RTM/SIRGAS 2000 deve ser preservada e seus parametros matematicos validados antes de automatizar transformacoes ou calculos metricos. UTM 20S ou UTM 21S nao sao impostos como regra geral para Manaus.

## Testes de aceitacao

- `espacialize as escolas da Base Geo e gere um mapa`: deve localizar `edu_escolas_manaus`, validar CRS, usar geometria existente e produzir representacao cartografica.
- `quantas escolas existem por DDZ?`: deve usar indice derivado ou consulta reproduzivel da fonte.
- `quais escolas estao no bairro X?`: deve retornar registros e, quando pertinente, espacializacao.
- `quais escolas estao a menos de 1 km desta area?`: deve usar operacao espacial real em CRS metrico validado; nao estimativa textual.
- `mostre este imovel`: deve usar poligono validado ou declarar ausencia de geometria.

## Estado de implementacao

O executor inicial da v002 cobre inspecao de camada, agrupamento e filtragem tabular de escolas com log de auditoria. Buffer, interseccao, distancia, reprojecao e geracao cartografica permanecem condicionados a uma biblioteca/executor geoespacial capaz de ler a geometria e a validacao da configuracao CRS aplicavel.
