"""
Verificador básico do projeto PetVida.

Salve este arquivo como verificar.py na mesma pasta de db.py e repositorio.py.
Os testes de conexão e consulta precisam de um SQL Server configurado e do banco PetVida.
Este arquivo não cria, altera nem exclui dados.
"""

import ast
import importlib
import sys
from pathlib import Path


PASTA_PROJETO = Path(__file__).resolve().parent
ARQUIVOS = ("db.py", "repositorio.py")


def verificar_sintaxe():
    print("\n[1] Verificação de sintaxe")
    sucesso = True

    for nome in ARQUIVOS:
        caminho = PASTA_PROJETO / nome
        if not caminho.exists():
            print(f"  ERRO: arquivo não encontrado: {nome}")
            sucesso = False
            continue

        try:
            codigo = caminho.read_text(encoding="utf-8")
            ast.parse(codigo, filename=nome)
            print(f"  OK: {nome}")
        except (SyntaxError, UnicodeDecodeError) as erro:
            print(f"  ERRO em {nome}: {erro}")
            sucesso = False

    return sucesso


def verificar_importacao():
    print("\n[2] Verificação de importação")
    try:
        importlib.import_module("db")
        repositorio = importlib.import_module("repositorio")
        print("  OK: db.py e repositorio.py foram importados.")
        return repositorio
    except Exception as erro:
        print(f"  ERRO ao importar os módulos: {type(erro).__name__}: {erro}")
        print("  Confira se pyodbc está instalado e se os arquivos estão na mesma pasta.")
        return None


def verificar_conexao():
    print("\n[3] Teste de conexão com SQL Server")
    try:
        db = importlib.import_module("db")
        servidor, banco, versao = db.testar_conexao()
        print(f"  OK: conexão estabelecida.")
        print(f"  Servidor: {servidor}")
        print(f"  Banco: {banco}")
        print(f"  Versão: {versao.splitlines()[0] if versao else 'não informada'}")
        return True
    except Exception as erro:
        print(f"  FALHOU: {type(erro).__name__}: {erro}")
        print("  Confira o serviço SQL Server, o driver ODBC, a instância e o banco PetVida.")
        return False


def verificar_listagem_tutores(repositorio):
    print("\n[4] Teste de leitura da tabela de tutores")
    try:
        tutores = repositorio.listar_tutores()
        print(f"  OK: consulta executada. Total de tutores encontrados: {len(tutores)}")
        for tutor in tutores[:5]:
            print(f"  - ID: {tutor.id_tutor} | Nome: {tutor.nome}")
        if len(tutores) > 5:
            print("  (Exibindo somente os primeiros 5 registros.)")
        return True
    except Exception as erro:
        print(f"  FALHOU: {type(erro).__name__}: {erro}")
        print("  Confirme se o banco PetVida e a tabela dbo.tutor existem.")
        return False


def main():
    print("=" * 55)
    print("VERIFICADOR DO PROJETO PETVIDA")
    print("=" * 55)

    sintaxe_ok = verificar_sintaxe()
    if not sintaxe_ok:
        print("\nCorrija os erros de sintaxe antes de continuar.")
        sys.exit(1)

    repositorio = verificar_importacao()
    if repositorio is None:
        sys.exit(1)

    conexao_ok = verificar_conexao()
    if conexao_ok:
        leitura_ok = verificar_listagem_tutores(repositorio)
    else:
        leitura_ok = False
        print("\n[4] Teste de leitura ignorado porque a conexão falhou.")

    print("\n" + "=" * 55)
    if conexao_ok and leitura_ok:
        print("RESULTADO: verificações concluídas com sucesso.")
        sys.exit(0)
    print("RESULTADO: há verificações que falharam. Consulte as mensagens acima.")
    print("A sintaxe e a importação podem estar corretas mesmo se o SQL Server não estiver acessível.")
    sys.exit(2)


if __name__ == "__main__":
    main()
