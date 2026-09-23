# Ambientes de armazenamento - Manaus v001

## Trabalho local

- Caminho: definido em config/ambiente.local.json.
- Modelo: config/ambiente.local.example.json.
- Finalidade: processamento, edicao, validacao e geracao de produtos.
- Regra: o arquivo local de configuracao nao deve ser versionado.

## GitHub

- Repositorio: https://github.com/Charles-Igeotecnologia/Manaus_Territorio_Agentico_v001.git
- Finalidade: documentacao, scripts e GeoPackage sanitizado.
- Regra: nao publicar originais, credenciais ou dados restritos.

## Procedimento de publicacao

1. Encerrar programas conectados ao GeoPackage.
2. Validar OGC, integridade SQLite, geometrias e campos.
3. Gerar e conferir o SHA-256.
4. Revisar o conjunto de arquivos preparado pelo Git.
5. Publicar somente a versao aprovada.
6. Registrar commit, data e responsavel.
