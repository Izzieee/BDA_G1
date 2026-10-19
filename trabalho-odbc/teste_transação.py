from db import transacao
with transacao() as cur:
    cur.execute("SELECT nome FROM dbo.tutor WHERE id_tutor = ?", 1)
    print(cur.fetchone().nome)