import pyodbc
from contextlib import contextmanager


def montar_connection_string():
    return (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=.\SQLEXPRESS;"
        "Database=PetVida;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


def conectar():
    return pyodbc.connect(
        montar_connection_string(),
        autocommit=False
    )


def testar_conexao():
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                @@SERVERNAME AS servidor,
                DB_NAME() AS banco,
                @@VERSION AS versao
        """)
        linha = cursor.fetchone()
        return linha.servidor, linha.banco, linha.versao


@contextmanager
def transacao():
    conn = conectar()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


#TESTE1
with transacao() as cur:
    
    cur.execute("SELECT nome FROM dbo.tutor WHERE id_tutor = ?", 
                1)
    print(cur.fetchone().nome)

