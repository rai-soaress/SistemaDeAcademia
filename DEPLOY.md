# Banco e deploy

O projeto usa SQLite localmente e PostgreSQL nas hospedagens. O banco local,
administradores, PDFs e uploads nao sao enviados ao GitHub nem migrados automaticamente.

## Variaveis de ambiente

- `DATABASE_URL`: URL PostgreSQL fornecida pelo provedor. Sao aceitos os prefixos
  `postgres://`, `postgresql://` e `postgresql+psycopg://`.
- `SECRET_KEY`: chave privada fixa. Gere com
  `python -c "import secrets; print(secrets.token_hex(32))"`.
- `APP_ENV=production`: ativa a configuracao de producao.

Use a URL externa com TLS (`?sslmode=require`) para conectar de fora da rede
do provedor. Se a senha contiver caracteres reservados, use a URL ja codificada
fornecida pelo painel. Nunca coloque credenciais no Git.

## Render

1. Crie um PostgreSQL ou utilize um existente.
2. Importe este repositorio em **New > Blueprint**. O arquivo `render.yaml`
   configura o servico web e gera a chave de sessao.
3. Informe `DATABASE_URL` quando solicitado. Para PostgreSQL no mesmo Render e
   regiao, pode usar a URL interna; para outro provedor, use a URL externa com TLS.
4. O comando de inicio cria as tabelas antes de iniciar o Gunicorn.

O Blueprint nao cria banco nem contrata armazenamento. Confira as condicoes do
plano escolhido no painel, inclusive prazo de validade e backups do PostgreSQL.

## Vercel

1. Importe o repositorio e selecione Flask se a deteccao automatica nao ocorrer.
2. Configure `DATABASE_URL`, `SECRET_KEY` e `APP_ENV=production` antes do deploy.
   Use a URL externa do PostgreSQL, preferencialmente a conexao com pool do provedor.
3. O build em `vercel.json` cria/atualiza as tabelas e copia os arquivos estaticos
   para `public/static`. O ponto de entrada e `app.py`.
4. Use um banco separado para Preview; o build tambem inicializa o banco desse
   ambiente. Nao execute builds simultaneos contra um esquema ainda nao criado.

As duas plataformas podem compartilhar o mesmo PostgreSQL se voce quiser os mesmos
dados. A URL interna do Render nao funciona na Vercel.

## Inicializacao e verificacao

Com as variaveis configuradas e dependencias instaladas:

```sh
python -m flask --app app init-db
```

O comando pode ser repetido: cria tabelas ausentes e aplica os ajustes legados
de colunas sem apagar registros. Ele nao substitui um sistema de migracoes
versionadas para futuras alteracoes de esquema.

Acesse `/cadastro-admin` para criar o administrador no banco novo, depois teste
login, plano, aluno e pagamento. O cadastro local nao existe no banco remoto.

## Arquivos e limite desta preparacao

PostgreSQL persiste os registros, mas PDFs e midias continuam no sistema de
arquivos. Na Vercel, `instance` usa a pasta temporaria, que nao garante conservacao
nem compartilhamento entre execucoes. No Render sem disco persistente, esses
arquivos tambem podem desaparecer. Para conservar PDFs e uploads em producao,
sera necessario integrar armazenamento de objetos; no Render tambem e possivel
montar um disco e configurar `INSTANCE_PATH` para seu caminho absoluto.

Esta preparacao nao cria recursos nas contas nem transfere os dados locais.

Referencias: [Flask no Render](https://render.com/docs/deploy-flask),
[Flask na Vercel](https://vercel.com/docs/frameworks/backend/flask),
[conexoes PostgreSQL no Render](https://render.com/docs/postgresql-creating-connecting).
