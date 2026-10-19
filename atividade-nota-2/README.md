# Atividade Nota #2 — PetVida (Python + SQL Server com pyodbc)

Implementação do Desafio Técnico "Conexão Python + SQL Server com pyodbc" usando o banco **PetVida** (clínica veterinária fictícia).

## Arquivos do projeto

```text
atividade-nota-2/
├── db.py             # Etapa 1: conexão, transação e teste de conexão
├── repositorio.py    # Etapas 2 a 4: CRUD e relacionamentos 1:N e N:M
├── verificar.py      # verificador básico do projeto
└── README.md
```

## 1. Criar o banco

Execute `01_estrutura_petvida.sql` (o mesmo da pasta `trabalho-odbc`) no SSMS como administrador. Ao final, a consulta de conferência deve listar 5 consultas.

## 2. Instalar o pyodbc

```powershell
py -3.14 -m pip install pyodbc
```

Também é necessário ter instalado o **Microsoft ODBC Driver 17 (ou 18) for SQL Server**. Confira os drivers disponíveis com `py -3.14 -c "import pyodbc; print(pyodbc.drivers())"`. Se o driver instalado for outro (por exemplo, o legado `SQL Server`), defina a variável opcional `PETVIDA_DRIVER` com o nome exato do driver (padrão: `ODBC Driver 17 for SQL Server`).

## 3. Configurar as variáveis de ambiente

Nenhuma credencial ou endereço fica fixo no código: o `db.py` lê as variáveis de ambiente `PETVIDA_SERVER` e `PETVIDA_DATABASE` (mesma base usada em `trabalho-odbc`).

No PowerShell (para a sessão atual):

```powershell
$env:PETVIDA_SERVER = ".\SQLEXPRESS"   # instância do seu SQL Server
$env:PETVIDA_DATABASE = "PetVida"
```

Ou permanentemente (para novos terminais):

```powershell
setx PETVIDA_SERVER ".\SQLEXPRESS"
setx PETVIDA_DATABASE "PetVida"
```

A conexão usa a autenticação do Windows (`Trusted_Connection=yes`), portanto não há senha no código.

## 4. Rodar o verificador

```powershell
py -3.14 verificar.py
```

O verificador checa a sintaxe de `db.py` e `repositorio.py`, importa os módulos, testa a conexão e lista os tutores cadastrados.

Também dá para testar a conexão direto:

```powershell
py -3.14 db.py
```

## Operações disponíveis em `repositorio.py`

- **Tutores (Etapa 2):** `criar_tutor` (retorna o ID gerado via `OUTPUT INSERTED`), `buscar_tutor`, `listar_tutores` (filtro com `LIKE` parametrizado), `atualizar_tutor` (lista branca: nome, email, telefone) e `excluir_tutor` (bloqueada se houver pets).
- **Pets 1:N (Etapa 3):** `criar_pet`, `atualizar_peso_pet`, `transferir_pet`, `excluir_pet`, `listar_pets_do_tutor` (tutor → pets) e `buscar_pet_com_tutor` (pet → tutor com `JOIN`).
- **Consultas e procedimentos N:M (Etapa 4):** `agendar_consulta` (consulta + tabela associativa numa única transação, valor cobrado = `preco_base` atual), `adicionar_procedimento`, `remover_procedimento`, `listar_procedimentos_da_consulta`, `listar_consultas_por_procedimento`, `total_da_consulta`, `atualizar_status_consulta` e `excluir_consulta` (itens apagados em cascata).
- **Bônus:** `historico_do_pet` usando a view `vw_resumo_consulta`.

## Regras técnicas seguidas

- Todas as consultas usam parâmetros `?` do `pyodbc` (valores nunca entram concatenados na string SQL — veja a seção SQL Injection do OWASP).
- Nomes de colunas, que não aceitam `?`, só são montados dinamicamente a partir de uma lista branca definida no código (`atualizar_tutor`).
- A função `transacao()` em `db.py` abre a conexão com `autocommit=False`, confirma no sucesso, desfaz em caso de erro e sempre fecha cursor e conexão no `finally` — nenhuma conexão fica aberta no servidor.
- A estrutura do banco é usada exatamente como entregue; nenhuma constraint foi removida.
- Erros do banco (`pyodbc.IntegrityError`, `pyodbc.OperationalError`) são traduzidos em exceções de negócio compreensíveis.
