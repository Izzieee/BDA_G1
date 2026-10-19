"""
Etapas 2 a 4 — CRUD de tutor, relacionamento 1:N tutor -> pet
e relacionamento N:M consulta <-> procedimento.

Toda consulta usa parâmetros "?" (pyodbc) — nunca valores colados no SQL.
Cada função abre sua própria conexão pelo contexto transacao() de db.py,
que confirma no sucesso, desfaz em erro e sempre fecha cursor/conexão.
"""

import pyodbc

from db import transacao


# --------------------------------------------------------------------------
# Exceções de negócio
# --------------------------------------------------------------------------

class TutorNaoEncontradoError(Exception):
    pass


class PetNaoEncontradoError(Exception):
    pass


class ConsultaNaoEncontradaError(Exception):
    pass


class RegraDeNegocioError(Exception):
    pass


# --------------------------------------------------------------------------
# Etapa 2 — CRUD de tutor
# --------------------------------------------------------------------------

def criar_tutor(nome, cpf, email=None, telefone=None):
    try:
        with transacao() as cur:
            cur.execute(
                """
                INSERT INTO dbo.tutor (nome, cpf, email, telefone)
                OUTPUT INSERTED.id_tutor
                VALUES (?, ?, ?, ?)
                """,
                nome, cpf, email, telefone
            )
            return cur.fetchone()[0]

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Não foi possível cadastrar o tutor. "
            "Verifique se o CPF tem 11 dígitos e se já não está cadastrado."
        ) from erro


def buscar_tutor(id_tutor):
    with transacao() as cur:
        cur.execute(
            """
            SELECT id_tutor, nome, cpf, email, telefone, data_cadastro
            FROM dbo.tutor
            WHERE id_tutor = ?
            """,
            id_tutor
        )
        return cur.fetchone()


def listar_tutores(filtro_nome=None):
    with transacao() as cur:
        if filtro_nome:
            cur.execute(
                """
                SELECT id_tutor, nome, cpf, email, telefone, data_cadastro
                FROM dbo.tutor
                WHERE nome LIKE ?
                ORDER BY nome
                """,
                f"%{filtro_nome}%"
            )
        else:
            cur.execute(
                """
                SELECT id_tutor, nome, cpf, email, telefone, data_cadastro
                FROM dbo.tutor
                ORDER BY nome
                """
            )
        return cur.fetchall()


def atualizar_tutor(id_tutor, **campos):
    campos_permitidos = {"nome", "email", "telefone"}  # lista branca de colunas

    if not campos:
        raise ValueError("Informe pelo menos um campo para atualizar.")

    if not set(campos).issubset(campos_permitidos):
        raise ValueError("Só é permitido atualizar nome, email e telefone.")

    with transacao() as cur:
        # Nomes de colunas não aceitam "?": só entram na SQL os nomes da lista branca.
        definicoes = ", ".join(f"{campo} = ?" for campo in campos)
        valores = list(campos.values()) + [id_tutor]

        cur.execute(
            f"UPDATE dbo.tutor SET {definicoes} WHERE id_tutor = ?",
            *valores
        )

        if cur.rowcount == 0:
            raise TutorNaoEncontradoError(f"Não existe tutor com o ID {id_tutor}.")

        return True


def excluir_tutor(id_tutor):
    try:
        with transacao() as cur:
            cur.execute("SELECT TOP 1 1 FROM dbo.pet WHERE id_tutor = ?", id_tutor)

            if cur.fetchone() is not None:
                raise RegraDeNegocioError(
                    "Não é possível excluir o tutor porque ele ainda tem pets."
                )

            cur.execute("DELETE FROM dbo.tutor WHERE id_tutor = ?", id_tutor)

            if cur.rowcount == 0:
                raise TutorNaoEncontradoError(f"Não existe tutor com o ID {id_tutor}.")

            return True

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "O banco de dados bloqueou a exclusão do tutor."
        ) from erro


# --------------------------------------------------------------------------
# Etapa 3 — Relacionamento 1:N tutor -> pet
# --------------------------------------------------------------------------

def criar_pet(id_tutor, nome, especie, raca=None, data_nascimento=None, peso_kg=None):
    try:
        with transacao() as cur:
            cur.execute(
                """
                INSERT INTO dbo.pet (id_tutor, nome, especie, raca, data_nascimento, peso_kg)
                OUTPUT INSERTED.id_pet
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                id_tutor, nome, especie, raca, data_nascimento, peso_kg
            )
            return cur.fetchone()[0]

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Não foi possível cadastrar o pet. Verifique o tutor, a espécie e o peso."
        ) from erro


def atualizar_peso_pet(id_pet, peso_kg):
    if peso_kg is not None and peso_kg <= 0:
        raise ValueError("O peso do pet deve ser maior que zero.")

    with transacao() as cur:
        cur.execute("UPDATE dbo.pet SET peso_kg = ? WHERE id_pet = ?", peso_kg, id_pet)

        if cur.rowcount == 0:
            raise PetNaoEncontradoError(f"Não existe pet com o ID {id_pet}.")

        return True


def transferir_pet(id_pet, novo_id_tutor):
    try:
        with transacao() as cur:
            cur.execute("UPDATE dbo.pet SET id_tutor = ? WHERE id_pet = ?",
                        novo_id_tutor, id_pet)

            if cur.rowcount == 0:
                raise PetNaoEncontradoError(f"Não existe pet com o ID {id_pet}.")

            return True

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Não foi possível transferir o pet. Verifique se o novo tutor existe."
        ) from erro


def excluir_pet(id_pet):
    try:
        with transacao() as cur:
            cur.execute("DELETE FROM dbo.pet WHERE id_pet = ?", id_pet)

            if cur.rowcount == 0:
                raise PetNaoEncontradoError(f"Não existe pet com o ID {id_pet}.")

            return True

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Não é possível excluir o pet porque há consultas relacionadas."
        ) from erro


def listar_pets_do_tutor(id_tutor):
    """Navega do lado 1 (tutor) para o lado N (pets)."""
    with transacao() as cur:
        cur.execute(
            """
            SELECT id_pet, id_tutor, nome, especie, raca, data_nascimento, peso_kg
            FROM dbo.pet
            WHERE id_tutor = ?
            ORDER BY nome
            """,
            id_tutor
        )
        return cur.fetchall()


def buscar_pet_com_tutor(id_pet):
    """Navega do lado N (pet) para o lado 1 (tutor) com JOIN."""
    with transacao() as cur:
        cur.execute(
            """
            SELECT p.id_pet, p.nome AS nome_pet, p.especie, p.raca,
                   p.data_nascimento, p.peso_kg,
                   t.id_tutor, t.nome AS nome_tutor, t.cpf, t.email, t.telefone
            FROM dbo.pet AS p
            INNER JOIN dbo.tutor AS t ON t.id_tutor = p.id_tutor
            WHERE p.id_pet = ?
            """,
            id_pet
        )
        return cur.fetchone()


# --------------------------------------------------------------------------
# Etapa 4 — Relacionamento N:M consulta <-> procedimento
# --------------------------------------------------------------------------

def agendar_consulta(id_pet, id_vet, data_hora, motivo, procedimentos):
    """Grava a consulta e os itens da tabela associativa numa única transação.
    procedimentos = lista de tuplas (id_procedimento, quantidade)."""
    try:
        with transacao() as cur:
            cur.execute(
                """
                INSERT INTO dbo.consulta (id_pet, id_veterinario, data_hora, motivo)
                OUTPUT INSERTED.id_consulta
                VALUES (?, ?, ?, ?)
                """,
                id_pet, id_vet, data_hora, motivo
            )
            id_consulta = cur.fetchone()[0]

            for id_procedimento, quantidade in procedimentos:
                if quantidade <= 0:
                    raise ValueError(
                        "A quantidade de cada procedimento deve ser maior que zero."
                    )

                cur.execute(
                    "SELECT preco_base FROM dbo.procedimento WHERE id_procedimento = ?",
                    id_procedimento
                )
                procedimento = cur.fetchone()

                if procedimento is None:
                    raise RegraDeNegocioError(
                        f"Não existe procedimento com o ID {id_procedimento}."
                    )

                cur.execute(
                    """
                    INSERT INTO dbo.consulta_procedimento
                        (id_consulta, id_procedimento, quantidade, valor_cobrado)
                    VALUES (?, ?, ?, ?)
                    """,
                    id_consulta, id_procedimento, quantidade, procedimento.preco_base
                )

            return id_consulta

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Não foi possível agendar a consulta. Verifique o pet, o veterinário "
            "e os procedimentos informados."
        ) from erro


def adicionar_procedimento(id_consulta, id_procedimento, quantidade=1):
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    try:
        with transacao() as cur:
            cur.execute("SELECT status FROM dbo.consulta WHERE id_consulta = ?",
                        id_consulta)
            consulta = cur.fetchone()

            if consulta is None:
                raise ConsultaNaoEncontradaError(
                    f"Não existe consulta com o ID {id_consulta}."
                )

            if consulta.status == "CANCELADA":
                raise RegraDeNegocioError(
                    "Não é possível adicionar procedimentos a uma consulta cancelada."
                )

            cur.execute(
                "SELECT preco_base FROM dbo.procedimento WHERE id_procedimento = ?",
                id_procedimento
            )
            procedimento = cur.fetchone()

            if procedimento is None:
                raise RegraDeNegocioError(
                    f"Não existe procedimento com o ID {id_procedimento}."
                )

            cur.execute(
                """
                INSERT INTO dbo.consulta_procedimento
                    (id_consulta, id_procedimento, quantidade, valor_cobrado)
                VALUES (?, ?, ?, ?)
                """,
                id_consulta, id_procedimento, quantidade, procedimento.preco_base
            )
            return True

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Esse procedimento já está na consulta ou os dados violam uma regra."
        ) from erro


def remover_procedimento(id_consulta, id_procedimento):
    with transacao() as cur:
        cur.execute(
            """
            DELETE FROM dbo.consulta_procedimento
            WHERE id_consulta = ? AND id_procedimento = ?
            """,
            id_consulta, id_procedimento
        )

        if cur.rowcount == 0:
            raise RegraDeNegocioError(
                "Esse procedimento não está associado à consulta."
            )

        return True


def listar_procedimentos_da_consulta(id_consulta):
    """N:M — consulta -> procedimentos."""
    with transacao() as cur:
        cur.execute(
            """
            SELECT p.id_procedimento, p.descricao, cp.quantidade, cp.valor_cobrado
            FROM dbo.consulta_procedimento AS cp
            INNER JOIN dbo.procedimento AS p ON p.id_procedimento = cp.id_procedimento
            WHERE cp.id_consulta = ?
            ORDER BY p.descricao
            """,
            id_consulta
        )
        return cur.fetchall()


def listar_consultas_por_procedimento(id_procedimento):
    """N:M — procedimento -> consultas."""
    with transacao() as cur:
        cur.execute(
            """
            SELECT c.id_consulta, c.id_pet, c.id_veterinario, c.data_hora,
                   c.motivo, c.status, cp.quantidade, cp.valor_cobrado
            FROM dbo.consulta_procedimento AS cp
            INNER JOIN dbo.consulta AS c ON c.id_consulta = cp.id_consulta
            WHERE cp.id_procedimento = ?
            ORDER BY c.data_hora
            """,
            id_procedimento
        )
        return cur.fetchall()


def total_da_consulta(id_consulta):
    with transacao() as cur:
        cur.execute(
            """
            SELECT ISNULL(SUM(quantidade * valor_cobrado), 0) AS valor_total
            FROM dbo.consulta_procedimento
            WHERE id_consulta = ?
            """,
            id_consulta
        )
        return cur.fetchone().valor_total


def atualizar_status_consulta(id_consulta, novo_status):
    status_permitidos = {"AGENDADA", "REALIZADA", "CANCELADA"}

    if novo_status not in status_permitidos:
        raise ValueError("Status inválido. Use AGENDADA, REALIZADA ou CANCELADA.")

    try:
        with transacao() as cur:
            cur.execute("UPDATE dbo.consulta SET status = ? WHERE id_consulta = ?",
                        novo_status, id_consulta)

            if cur.rowcount == 0:
                raise ConsultaNaoEncontradaError(
                    f"Não existe consulta com o ID {id_consulta}."
                )

            return True

    except pyodbc.IntegrityError as erro:
        raise RegraDeNegocioError(
            "Não foi possível atualizar o status da consulta."
        ) from erro


def excluir_consulta(id_consulta):
    """Os itens da tabela associativa somem pelo ON DELETE CASCADE."""
    with transacao() as cur:
        cur.execute("DELETE FROM dbo.consulta WHERE id_consulta = ?", id_consulta)

        if cur.rowcount == 0:
            raise ConsultaNaoEncontradaError(
                f"Não existe consulta com o ID {id_consulta}."
            )

        return True


# --------------------------------------------------------------------------
# Bônus — histórico do pet pela view vw_resumo_consulta
# --------------------------------------------------------------------------

def historico_do_pet(id_pet):
    with transacao() as cur:
        cur.execute(
            """
            SELECT data_hora, status, pet, veterinario, qtd_itens, valor_total
            FROM dbo.vw_resumo_consulta
            WHERE pet = (SELECT nome FROM dbo.pet WHERE id_pet = ?)
            ORDER BY data_hora
            """,
            id_pet
        )
        return cur.fetchall()
