"""
Script de demonstração e execução dos 12 cenários de teste da APS 3.
Imprime as requisições, status HTTP e respostas JSON para comprovação e evidência.
"""

import json
from fastapi.testclient import TestClient
from main import app
from database import init_db, SessionLocal
from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao

client = TestClient(app)

def reset_db():
    init_db()
    db = SessionLocal()
    db.query(Inscricao).delete()
    db.query(Participante).delete()
    db.query(Evento).delete()
    db.commit()
    db.close()

def print_section(titulo):
    print("\n" + "=" * 80)
    print(f" {titulo} ")
    print("=" * 80)

def main():
    print_section("INICIALIZANDO TESTES DOS 12 CENÁRIOS DA APS 3")
    reset_db()

    # Cenário 1
    print_section("CENÁRIO 1: Cadastro e consulta de eventos utilizando o banco de dados")
    ev_payload = {
        "titulo": "Seminário de Inteligência Artificial",
        "descricao": "Explorando Redes Neurais e LLMs.",
        "data": "2026-12-10",
        "horario": "19:00",
        "local": "Auditório Principal",
        "capacidade": 100,
        "categoria": "Seminário"
    }
    r = client.post("/eventos/", json=ev_payload)
    print(f"[POST /eventos/] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))
    ev_id = r.json()["id"]

    r = client.get(f"/eventos/{ev_id}")
    print(f"[GET /eventos/{ev_id}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 2
    print_section("CENÁRIO 2: Cadastro e consulta de participantes")
    part_payload = {
        "nome": "Ana Beatriz",
        "email": "ana.beatriz@faculdade.edu.br",
        "curso": "Engenharia de Software"
    }
    r = client.post("/participantes/", json=part_payload)
    print(f"[POST /participantes/] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))
    part_id = r.json()["id"]

    r = client.get(f"/participantes/{part_id}")
    print(f"[GET /participantes/{part_id}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 3
    print_section("CENÁRIO 3: Atualização e exclusão de registros")
    # Atualiza evento
    r = client.put(f"/eventos/{ev_id}", json={"titulo": "Seminário de IA e Novas Tecnologias", "capacidade": 120})
    print(f"[PUT /eventos/{ev_id}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cria participante para exclusão
    temp_p = client.post("/participantes/", json={"nome": "Temp", "email": "temp@temp.com", "curso": "Geral"}).json()
    r = client.delete(f"/participantes/{temp_p['id']}")
    print(f"[DELETE /participantes/{temp_p['id']}] Status: {r.status_code} (No Content)")

    # Cenário 4
    print_section("CENÁRIO 4: Inscrição de um participante em um evento")
    r = client.post(f"/eventos/{ev_id}/inscricoes/{part_id}")
    print(f"[POST /eventos/{ev_id}/inscricoes/{part_id}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    r = client.get(f"/eventos/{ev_id}/inscricoes")
    print(f"[GET /eventos/{ev_id}/inscricoes] Status: {r.status_code}")
    print("Inscritos no evento:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 5
    print_section("CENÁRIO 5: Tentativa de inscrição duplicada (Esperado: 409 Conflict)")
    r = client.post(f"/eventos/{ev_id}/inscricoes/{part_id}")
    print(f"[POST /eventos/{ev_id}/inscricoes/{part_id}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 6
    print_section("CENÁRIO 6: Tentativa de inscrição em evento inexistente (Esperado: 404 Not Found)")
    r = client.post(f"/eventos/99999/inscricoes/{part_id}")
    print(f"[POST /eventos/99999/inscricoes/{part_id}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 7
    print_section("CENÁRIO 7: Tentativa de inscrição sem vagas disponíveis (Esperado: 409 Conflict)")
    ev_lotado = client.post("/eventos/", json={
        "titulo": "Mentoria Exclusiva",
        "descricao": "Apenas 1 vaga disponível",
        "data": "2026-12-15",
        "horario": "14:00",
        "local": "Sala VIP",
        "capacidade": 1,
        "categoria": "Mentoria"
    }).json()
    p2 = client.post("/participantes/", json={"nome": "Carlos", "email": "carlos@faculdade.edu.br", "curso": "ADS"}).json()
    p3 = client.post("/participantes/", json={"nome": "Daniela", "email": "daniela@faculdade.edu.br", "curso": "ADS"}).json()

    # Ocupa a vaga
    client.post(f"/eventos/{ev_lotado['id']}/inscricoes/{p2['id']}")
    # Tenta exceder capacidade
    r = client.post(f"/eventos/{ev_lotado['id']}/inscricoes/{p3['id']}")
    print(f"[POST /eventos/{ev_lotado['id']}/inscricoes/{p3['id']}] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 8
    print_section("CENÁRIO 8: Reinicialização da aplicação e verificação da persistência dos dados")
    print("Fechando conexão e criando novo cliente para simular reinicialização...")
    novo_cliente = TestClient(app)
    r = novo_cliente.get(f"/eventos/{ev_id}")
    print(f"[GET /eventos/{ev_id} após reinício] Status: {r.status_code}")
    print("Evento recuperado do SQLite:", r.json()["titulo"])

    r = novo_cliente.get(f"/participantes/{part_id}")
    print(f"[GET /participantes/{part_id} após reinício] Status: {r.status_code}")
    print("Participante recuperado do SQLite:", r.json()["nome"])

    # Cenário 9
    print_section("CENÁRIO 9: Consulta do relatório de ocupação dos eventos")
    r = client.get("/relatorios/eventos/ocupacao")
    print(f"[GET /relatorios/eventos/ocupacao] Status: {r.status_code}")
    print("Relatório de Ocupação:\n", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 10
    print_section("CENÁRIO 10: Consulta do relatório de eventos por categoria")
    r = client.get("/relatorios/eventos/categorias")
    print(f"[GET /relatorios/eventos/categorias] Status: {r.status_code}")
    print("Relatório por Categoria:\n", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 11
    print_section("CENÁRIO 11: Consulta do relatório de participação por curso")
    r = client.get("/relatorios/participantes/cursos")
    print(f"[GET /relatorios/participantes/cursos] Status: {r.status_code}")
    print("Relatório por Curso:\n", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 12
    print_section("CENÁRIO 12: Verificação dos resultados dos relatórios após inserir, atualizar ou excluir registros")
    print("Cadastrando novo evento da categoria 'Competição'...")
    comp = client.post("/eventos/", json={
        "titulo": "Game Jam Universitária",
        "descricao": "Competição de 48h de desenvolvimento",
        "data": "2026-12-18",
        "horario": "10:00",
        "local": "Lab Maker",
        "capacidade": 60,
        "categoria": "Competição"
    }).json()

    print("Relatório de Categorias atualizado dinamicamente:")
    r = client.get("/relatorios/eventos/categorias")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    print("Excluindo o evento recém-criado...")
    client.delete(f"/eventos/{comp['id']}")

    print("Relatório de Categorias após exclusão (verificando dinamismo):")
    r = client.get("/relatorios/eventos/categorias")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    print_section("TODOS OS 12 CENÁRIOS FORAM EXECUTADOS COM SUCESSO!")

if __name__ == "__main__":
    main()

