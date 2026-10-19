import os
import pyodbc
from contextlib import contextmanager


class ConexaoError(Exception):
    """ERRO: Falha ao conectar ou operar no banco de dados."""

    pass


def _env(nome):
    valor = os.getenv(nome)
    if not valor:
        raise EnvironmentError(f"Variável de ambiente {nome} não definida")
    return valor


def montar_connection_string():
    servidor = _env("PETVIDA_SERVER")
    banco = _env("PETVIDA_DATABASE")

    partes = [
        "Driver={ODBC Driver 17 for SQL Server}",
        f"Server={servidor}",
        f"Database={banco}",
        "Trusted_Connection=yes",
        "TrustServerCertificate=yes",
    ]
    return ";".join(partes) + ";"


def conectar():
    conn_str = montar_connection_string()
    try:
        return pyodbc.connect(conn_str, autocommit=False)
    except pyodbc.OperationalError as e:
        raise ConexaoError(
            f"Não foi possível fazer a conexão ao SQL Server: {e}"
        ) from e

@contextmanager
def transacao():
    conn = conectar()
    cur = None
    try:
        cur = conn.cursor()
        yield cur          # <-- o "as cur" recebe isso
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur is not None:
            cur.close
        conn.close()
