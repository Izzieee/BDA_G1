# PetVida — conexão Python com SQL Server

Este repositório reúne o acesso ao banco de dados da clínica veterinária fictícia PetVida. O objetivo é praticar a conexão entre Python e SQL Server e organizar operações de cadastro, consulta, atualização e exclusão de dados (CRUD).

## O que você precisa ter instalado

- Windows com Python 3.14.
- SQL Server Express ou Developer instalado e iniciado.
- Banco `PetVida` criado com o script SQL da atividade.
- Microsoft ODBC Driver 18 for SQL Server.
- Visual Studio Code, se quiser editar e executar o projeto por ele.

## Arquivos do projeto

```text
PetVida/
├── db.py             # conexão e transações
├── repositorio.py    # operações com os dados
├── verificar.py      # testes básicos do projeto
└── main.py           # opcional: menu no terminal
```

## 1. Instalar a biblioteca

Abra o terminal na pasta do projeto e execute:

```powershell
py -3.14 -m pip install pyodbc
```

No VS Code, confira se o interpretador selecionado é o Python 3.14 (`Ctrl+Shift+P` → `Python: Select Interpreter`).

## 2. Conferir a conexão

A função `montar_connection_string()` em `db.py` informa os dados usados para conectar ao SQL Server. No exemplo local, ela utiliza o driver ODBC 18, o banco `PetVida` e a autenticação do Windows.

Confira principalmente o nome da instância na opção `Server`. Ele precisa corresponder à instalação do SQL Server do seu computador. Se estiver usando uma instância diferente, ajuste esse valor antes de executar os testes.

Não coloque senhas ou outras credenciais diretamente no código.

## 3. Rodar o verificador

Salve o arquivo `verificar.py` fornecido junto com `db.py` e `repositorio.py`, na mesma pasta. Depois execute:

```powershell
py -3.14 verificar.py
```

O verificador checa a sintaxe dos módulos, importa o repositório e tenta estabelecer uma conexão com o banco. Ele também mostra a quantidade de tutores cadastrados. Os testes que dependem do banco só passam se o SQL Server estiver ligado, a conexão estiver configurada e as tabelas da atividade existirem.

## 4. Executar o projeto

Se houver um arquivo `main.py`, execute-o assim:

```powershell
py -3.14 main.py
```

Para testar uma função diretamente, você também pode criar um arquivo Python separado e importar, por exemplo, `listar_tutores` de `repositorio.py`.

## Operações disponíveis no repositório

O módulo `repositorio.py` reúne funções para:

- **Tutores:** cadastrar, buscar, listar, atualizar e excluir.
- **Pets:** cadastrar, atualizar peso, transferir para outro tutor, excluir, listar por tutor e consultar junto com os dados do tutor.
- **Consultas e procedimentos:** agendar consulta, adicionar ou remover procedimentos, listar procedimentos, consultar atendimentos por procedimento, calcular o total, alterar status e excluir consulta.

As instruções SQL usam parâmetros `?` do `pyodbc`, mantendo os valores separados do comando SQL. A função `transacao()` em `db.py` confirma a transação quando tudo ocorre bem e desfaz a transação em caso de erro, além de fechar cursor e conexão.

## Atenção ao banco de dados

Antes de testar, confirme que o banco `PetVida` foi criado com o script SQL da atividade. Leia o script antes de executá-lo: se ele remover e criar o banco novamente, os dados existentes serão apagados.
