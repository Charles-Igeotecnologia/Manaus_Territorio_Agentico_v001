# Territorio Agentico Manaus - versao 0.1.0

Primeira estrutura portatil da Base Geo para o planejamento da educacao municipal de Manaus.

## Situacao

- Territorio: Manaus - AM
- Versao tecnica: 0.1.0
- Codigo da entrega: v001
- Estado: estrutura inicial catalogada, aguardando validacao tecnica
- Base principal: `03_base_geo/manaus_base_geo_v001.gpkg`

## Estrutura

- `00_documentacao`: orientacoes e padroes.
- `01_armazenamento`: recebimento, originais e referencias externas.
- `02_tratamento`: triagem, processamento, intermediarios, logs e scripts.
- `03_base_geo`: GeoPackage consolidado e backups.
- `04_catalogo_metadados`: catalogos exportados para leitura humana.
- `05_validacao`: pendencias, pareceres dos instrutores e relatorios.
- `06_produtos`: mapas, tabelas e produtos de trabalho.
- `07_entregas`: versoes aprovadas para distribuicao.
- `08_metodologia_agentica`: workflows e prompts aprovados.

## Preservacao

Os dados existentes nas pastas externas da raiz nao foram movidos ou alterados. Esta versao os referencia no catalogo e no GeoPackage. Copias de trabalho somente devem entrar em `02_tratamento`.

## Fluxo minimo

1. Receber e registrar o arquivo.
2. Preservar o original.
3. Classificar acesso e sensibilidade.
4. Conferir formato, campos, datas, chaves, geometria e CRS.
5. Negociar regras ambiguas com a equipe e os instrutores.
6. Processar uma copia rastreavel.
7. Validar tecnicamente.
8. Incorporar na Base Geo e registrar a versao.
9. Publicar somente o produto aprovado.

## Consulta pelo GitHub

O diretorio dados_publicados contem o GeoPackage sanitizado para consultas portateis. Dados originais e configuracoes locais permanecem fora do repositorio. Use config/ambiente.local.example.json como modelo quando for necessario regenerar a base a partir das fontes institucionais.
