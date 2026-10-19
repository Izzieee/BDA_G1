"""
Script auxiliar de testes do PetVida — NÃO faz parte da entrega.

Rode na máquina que tem o SQL Server com o banco PetVida criado:

    py -3.14 testes.py

Cria registros com o prefixo TESTE, verifica cada operação do
repositorio.py e apaga tudo no final. Não altera os dados iniciais do banco.
"""

import pyodbc

from db import conectar, testar_conexao, transacao
from repositorio import (
    RegraDeNegocioError,
    TutorNaoEncontradoError,
    PetNaoEncontradoError,
    ConsultaNaoEncontradaError,
    adicionar_procedimento,
    atualizar_peso_pet,
    atualizar_status_consulta,
    atualizar_tutor,
    buscar_pet_com_tutor,
    buscar_tutor,
    criar_pet,
    criar_tutor,
    excluir_consulta,
    excluir_pet,
    excluir_tutor,
    historico_do_pet,
    agendar_consulta,
    listar_consultas_por_procedimento,
    listar_pets_do_tutor,
    listar_procedimentos_da_consulta,
    listar_tutores,
    remover_procedimento,
    total_da_consulta,
    transferir_pet,
)

acertos = 0
falhas = []


def checar(nome, condicao, detalhe=""):
    global acertos
    if condicao:
        acertos += 1
        print(f"  OK   {nome}")
    else:
        falhas.append(nome)
        print(f"  FALHA {nome} {detalhe}")


def esperar_erro(nome, funcao, *args, **kwargs):
    """Verifica que a operação lança a exceção de negócio esperada."""
    try:
        funcao(*args, **kwargs)
        checar(nome, False, "(nenhum erro lançado)")
    except (RegraDeNegocioError, TutorNaoEncontradoError,
            PetNaoEncontradoError, ConsultaNaoEncontradaError, ValueError):
        checar(nome, True)
    except Exception as erro:
        checar(nome, False, f"(erro inesperado: {type(erro).__name__}: {erro})")


def contar(sql, *params):
    with transacao() as cur:
        cur.execute(sql, *params)
        return cur.fetchone()[0]


# ==========================================================================
print("\n--- 1. CONEXÃO (Etapa 1) ---")
try:
    servidor, banco, versao = testar_conexao()
    checar("testar_conexao retorna servidor/banco/versão",
           bool(servidor and banco and versao), f"({servidor}, {banco})")
    checar("conectou ao banco PetVida", banco == "PetVida", f"(banco: {banco})")
except Exception as erro:
    checar("testar_conexao", False, f"({erro})")
    print("\nSem conexão não dá para continuar. Confira o SQL Server e as variáveis.")
    raise SystemExit(1)

tutores_antes = contar("SELECT COUNT(*) FROM dbo.tutor")
consultas_antes = contar("SELECT COUNT(*) FROM dbo.consulta")

# ==========================================================================
print("\n--- 2. CRUD DE TUTOR (Etapa 2) ---")

id_tutor = criar_tutor("TESTE Da Atividade", "99900011122", "teste@email.com")
checar("criar_tutor devolve o ID gerado", isinstance(id_tutor, int) and id_tutor > 0)

tutor = buscar_tutor(id_tutor)
checar("buscar_tutor encontra o recém-criado", tutor is not None and tutor.nome == "TESTE Da Atividade")

checar("listar_tutores devolve lista", isinstance(listar_tutores(), list))
filtro = listar_tutores("TESTE Da")
checar("listar_tutores filtra com LIKE parametrizado",
       len(filtro) >= 1 and all("TESTE Da" in t.nome for t in filtro))

esperar_erro("criar_tutor com CPF duplicado é bloqueado",
             criar_tutor, "TESTE Duplicado", "99900011122")
esperar_erro("criar_tutor com CPF inválido é bloqueado",
             criar_tutor, "TESTE Inválido", "123")

atualizar_tutor(id_tutor, nome="TESTE Da Atividade Editado", telefone="(17) 90000-0000")
tutor = buscar_tutor(id_tutor)
checar("atualizar_tutor altera nome e telefone",
       tutor.nome == "TESTE Da Atividade Editado" and tutor.telefone == "(17) 90000-0000")

esperar_erro("atualizar_tutor recusa coluna fora da lista branca (cpf)",
             atualizar_tutor, id_tutor, cpf="00000000000")
esperar_erro("atualizar_tutor de ID inexistente é bloqueado",
             atualizar_tutor, 999999, nome="X")
esperar_erro("excluir_tutor de ID inexistente é bloqueado",
             excluir_tutor, 999999)

# ==========================================================================
print("\n--- 3. RELAÇÃO 1:N TUTOR -> PET (Etapa 3) ---")

id_pet = criar_pet(id_tutor, "TESTE Rex", "Cão", "SRD", None, 12.34)
checar("criar_pet devolve o ID gerado", isinstance(id_pet, int) and id_pet > 0)

esperar_erro("criar_pet com espécie fora da lista é bloqueado",
             criar_pet, id_tutor, "TESTE Dragão", "Dragão")

pets = listar_pets_do_tutor(id_tutor)
checar("listar_pets_do_tutor navega do tutor para os pets",
       len(pets) == 1 and pets[0].nome == "TESTE Rex")

pet = buscar_pet_com_tutor(id_pet)
checar("buscar_pet_com_tutor navega do pet para o tutor com JOIN",
       pet is not None and pet.nome_tutor == "TESTE Da Atividade Editado")

atualizar_peso_pet(id_pet, 13.5)
checar("atualizar_peso_pet altera o peso", buscar_pet_com_tutor(id_pet).peso_kg == 13.5)
esperar_erro("atualizar_peso_pet com peso negativo é bloqueado",
             atualizar_peso_pet, id_pet, -1)
esperar_erro("atualizar_peso_pet de pet inexistente é bloqueado",
             atualizar_peso_pet, 999999, 5)

# ==========================================================================
print("\n--- 4. RELAÇÃO N:M CONSULTA <-> PROCEDIMENTO (Etapa 4) ---")

id_consulta = agendar_consulta(id_pet, 1, "2026-11-01 10:00",
                               "TESTE consulta da atividade",
                               [(1, 1), (2, 2)])  # consulta 150 + 2x vacina 90
checar("agendar_consulta devolve o ID gerado", isinstance(id_consulta, int))

itens = listar_procedimentos_da_consulta(id_consulta)
checar("listar_procedimentos_da_consulta (consulta -> itens)", len(itens) == 2)

# valor cobrado deve ser o preco_base atual: 150.00 + 2 * 90.00 = 330.00
checar("total_da_consulta soma quantidade x valor_cobrado",
       float(total_da_consulta(id_consulta)) == 330.00,
       f"(total: {total_da_consulta(id_consulta)})")

checar("listar_consultas_por_procedimento (procedimento -> consultas)",
       any(c.id_consulta == id_consulta
           for c in listar_consultas_por_procedimento(2)))

adicionar_procedimento(id_consulta, 7, 1)  # corte de unhas, 25.00
checar("adicionar_procedimento incrementa a tabela associativa",
       len(listar_procedimentos_da_consulta(id_consulta)) == 3)
esperar_erro("adicionar_procedimento repetido é bloqueado",
             adicionar_procedimento, id_consulta, 7, 1)
esperar_erro("adicionar_procedimento com quantidade 0 é bloqueado",
             adicionar_procedimento, id_consulta, 3, 0)
esperar_erro("remover_procedimento de item inexistente é bloqueado",
             remover_procedimento, id_consulta, 6)

esperar_erro("atualizar_status_consulta com status inválido é bloqueado",
             atualizar_status_consulta, id_consulta, "QUALQUER")
atualizar_status_consulta(id_consulta, "CANCELADA")
checar("atualizar_status_consulta altera o status",
       "CANCELADA" == [c for c in listar_consultas_por_procedimento(7)
                       if c.id_consulta == id_consulta][0].status)
esperar_erro("adicionar_procedimento em consulta cancelada é bloqueado",
             adicionar_procedimento, id_consulta, 4, 1)

# teste de rollback: nada pode ser gravado se um item falhar
antes = contar("SELECT COUNT(*) FROM dbo.consulta")
esperar_erro("agendar_consulta com procedimento inexistente é bloqueado",
             agendar_consulta, id_pet, 1, "2026-11-02 10:00", "TESTE rollback", [(9999, 1)])
depois = contar("SELECT COUNT(*) FROM dbo.consulta")
checar("rollback: consulta e itens não ficam 'meio gravados'", antes == depois)

# ==========================================================================
print("\n--- 5. BÔNUS: HISTÓRICO DO PET ---")

historico = historico_do_pet(id_pet)
# total da consulta = 150.00 (consulta) + 2 x 90.00 (vacina) + 25.00 (unhas) = 355.00
checar("historico_do_pet usa a view vw_resumo_consulta",
       len(historico) == 1 and float(historico[0].valor_total) == 355.00)

# ==========================================================================
print("\n--- 6. EXCLUSÕES E CASCADE ---")

esperar_erro("excluir_tutor com pets é bloqueado", excluir_tutor, id_tutor)
esperar_erro("excluir_pet com consultas é bloqueado", excluir_pet, id_pet)

excluir_consulta(id_consulta)
checar("excluir_consulta some com os itens (ON DELETE CASCADE)",
       contar("SELECT COUNT(*) FROM dbo.consulta_procedimento WHERE id_consulta = ?",
              id_consulta) == 0)

excluir_pet(id_pet)
checar("excluir_pet funciona após não haver consultas", True)
excluir_tutor(id_tutor)
checar("excluir_tutor funciona após não haver pets", True)
checar("nenhum registro TESTE sobrou no banco",
       contar("SELECT COUNT(*) FROM dbo.tutor WHERE nome LIKE 'TESTE%'") == 0)

# ==========================================================================
print("\n--- 7. SQL INJECTION (parametrização) ---")

injetado = listar_tutores("' OR 1=1 --")
checar("filtro com injeção não retorna tudo (retorna 0)", len(injetado) == 0)

with transacao() as cur:
    cur.execute("SELECT COUNT(*) FROM dbo.tutor")
    total_tutores = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM dbo.consulta")
    total_consultas = cur.fetchone()[0]
checar("banco íntegro: contagem de tutores e consultas de volta ao início",
       total_tutores == tutores_antes and total_consultas == consultas_antes,
       f"(tutores: {total_tutores}, consultas: {total_consultas})")

# ==========================================================================
print("\n" + "=" * 55)
print(f"RESULTADO: {acertos} OK, {falhas} FALHAS")
if falhas:
    raise SystemExit(1)
print("Todos os testes passaram.")
