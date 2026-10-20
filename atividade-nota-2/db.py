import os
from contextlib import contextmanager

import pyodbc


class ConexaoError(Exception):
    pass


def _env(nome):
    valor = os.getenv(nome)
    if not valor:
        raise EnvironmentError(f"Variável de ambiente {nome} não definida")
    return valor


def montar_connection_string():
    servidor = _env("PETVIDA_SERVER")
    banco = _env("PETVIDA_DATABASE")
    driver = os.getenv("PETVIDA_DRIVER", "ODBC Driver 17 for SQL Server")

    partes = [
        f"Driver={{{driver}}}",
        f"Server={servidor}",
        f"Database={banco}",
        "Trusted_Connection=yes",
        "TrustServerCertificate=yes",
    ]
    return ";".join(partes) + ";"


def conectar():
    try:
        return pyodbc.connect(montar_connection_string(), autocommit=False)
    except pyodbc.OperationalError as erro:
        raise ConexaoError(
            f"Não foi possível conectar ao SQL Server: {erro}"
        ) from erro


def testar_conexao():
    with conectar() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    @@SERVERNAME AS servidor,
                    DB_NAME() AS banco,
                    @@VERSION AS versao
                """
            )
            linha = cursor.fetchone()
            return linha.servidor, linha.banco, linha.versao
        finally:
            cursor.close()


@contextmanager
def transacao():
    conn = conectar()
    cur = None
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur is not None:
            cur.close()
        conn.close()


if __name__ == "__main__":
    servidor, banco, versao = testar_conexao()
    print("Servidor:", servidor)
    print("Banco:   ", banco)
    print("Versão:  ", versao.splitlines()[0])
