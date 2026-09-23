# Validacao da base de consulta Manaus v001

Status: candidato local, ainda nao publicado no GitHub.

## Resultado tecnico

- Formato: OGC GeoPackage 1.4.0.
- CRS de todas as camadas: SIRGAS 2000 (EPSG:4674).
- Tamanho: 5,1 MB.
- Integridade SQLite: aprovada.
- Chaves estrangeiras: aprovadas.
- Indices espaciais: presentes nas quatro camadas.
- Geometrias nulas: zero.
- Geometrias invalidas: zero.
- Campos sensiveis listados na auditoria: zero.
- SHA-256: fe80c68a7e18c75e87f7a2a811f51a9251f498ebe4c67e6c08d53ae744e5e18e.

## Camadas

- ref_bairros_zonas_manaus: 64 multipoligonos.
- ref_localidades_manaus: 663 multipoligonos.
- edu_escolas_manaus: 544 pontos.
- ref_setores_censitarios_manaus_2022: 3.210 multipoligonos.

## Exclusoes deliberadas

A camada detalhada de lotes nao foi incluida por volume e sensibilidade cadastral.

Da camada de escolas foram excluidos gestor, contato, telefone, ramal, endereco do locador, dados contratuais, valores, processos, usuarios de edicao, observacoes e links internos.

## Pendencias para publicacao

1. Confirmar que as fontes permitem publicacao no repositorio.
2. Validar institucionalmente a lista de campos das escolas.
3. Confirmar que bairros, localidades e setores podem ser distribuidos.
4. Aprovar o status de candidato para publicado.
5. Somente depois realizar commit e push para o GitHub.
