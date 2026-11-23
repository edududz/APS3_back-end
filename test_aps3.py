import os
import pytest
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal, init_db
from main import app

from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Garante isolamento limpando as tabelas antes de cada teste."""
    init_db()
    db = SessionLocal()
    try:
        db.query(Inscricao).delete()
        db.query(Participante).delete()
        db.query(Evento).delete()
        db.commit()
    finally:
        db.close()
    yield

def test_cenario_01_cadastro_e_consulta_eventos():
    """Cenário 1: Cadastro e consulta de eventos utilizando o banco de dados."""
    payload = {
        "titulo": "Seminário de IA e Aprendizado de Máquina",
        "descricao": "Discussões sobre as novas tendências de IA.",
        "data": "2026-12-10",
        "horario": "19:00",
        "local": "Auditório Principal",
        "capacidade": 50,
        "categoria": "Seminário"
    }
    # Cadastro
    post_res = client.post("/eventos/", json=payload)
    assert post_res.status_code == 201, post_res.text
    evento_criado = post_res.json()
    assert evento_criado["id"] is not None
    assert evento_criado["titulo"] == payload["titulo"]

    # Consulta por ID
    get_res = client.get(f"/eventos/{evento_criado['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["titulo"] == payload["titulo"]

    # Listagem geral
    list_res = client.get("/eventos/")
    assert list_res.status_code == 200
    assert any(e["id"] == evento_criado["id"] for e in list_res.json())

def test_cenario_02_cadastro_e_consulta_participantes():
    """Cenário 2: Cadastro e consulta de participantes."""
    payload = {
        "nome": "Mariana Silva",
        "email": "mariana.silva@universidade.edu.br",
        "curso": "Engenharia de Software"
    }
    # Cadastro
    post_res = client.post("/participantes/", json=payload)
    assert post_res.status_code == 201
    participante = post_res.json()
    assert participante["id"] is not None
    assert participante["email"] == payload["email"]

    # Consulta por ID
    get_res = client.get(f"/participantes/{participante['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["nome"] == payload["nome"]

    # Listagem geral
    list_res = client.get("/participantes/")
    assert list_res.status_code == 200
    assert any(p["id"] == participante["id"] for p in list_res.json())

def test_cenario_03_atualizacao_e_exclusao_registros():
    """Cenário 3: Atualização e exclusão de registros."""
    # Criar evento temporário
    ev_res = client.post("/eventos/", json={
        "titulo": "Workshop Provisório",
        "descricao": "Evento a ser atualizado e excluído",
        "data": "2026-11-30",
        "horario": "10:00",
        "local": "Sala 101",
        "capacidade": 20,
        "categoria": "Workshop"
    })
    ev_id = ev_res.json()["id"]

    # Atualizar evento
    update_res = client.put(f"/eventos/{ev_id}", json={
        "titulo": "Workshop Atualizado",
        "capacidade": 25
    })
    assert update_res.status_code == 200
    assert update_res.json()["titulo"] == "Workshop Atualizado"
    assert update_res.json()["capacidade"] == 25

    # Excluir evento
    del_res = client.delete(f"/eventos/{ev_id}")
    assert del_res.status_code == 204

    # Verificar que não existe mais (404)
    get_res = client.get(f"/eventos/{ev_id}")
    assert get_res.status_code == 404
    assert get_res.json()["detail"] == "Evento não encontrado."

def test_validacao_email_duplicado():
    """Validação de integridade: e-mail já cadastrado (409 Conflict)."""
    client.post("/participantes/", json={
        "nome": "Participante Original",
        "email": "duplicado@teste.com",
        "curso": "Engenharia de Software"
    })
    res = client.post("/participantes/", json={
        "nome": "Participante Clone",
        "email": "duplicado@teste.com",
        "curso": "Ciência da Computação"
    })
    assert res.status_code == 409
    assert res.json()["detail"] == "Já existe um participante cadastrado com este e-mail."

def test_cenario_04_inscricao_participante_em_evento():
    """Cenário 4: Inscrição de um participante em um evento."""
    ev = client.post("/eventos/", json={
        "titulo": "Palestra Cloud Computing",
        "descricao": "Arquitetura em Nuvem",
        "data": "2026-12-01",
        "horario": "18:00",
        "local": "Auditório B",
        "capacidade": 30,
        "categoria": "Palestra"
    }).json()

    part = client.post("/participantes/", json={
        "nome": "Lucas Moura",
        "email": "lucas.moura@universidade.edu.br",
        "curso": "Sistemas de Informação"
    }).json()

    # Realizar inscrição
    insc_res = client.post(f"/eventos/{ev['id']}/inscricoes/{part['id']}")
    assert insc_res.status_code == 201
    assert insc_res.json()["detail"] == "Inscrição realizada com sucesso."

    # Verificar participante na lista de inscritos do evento
    list_insc = client.get(f"/eventos/{ev['id']}/inscricoes")
    assert list_insc.status_code == 200
    assert any(p["id"] == part["id"] for p in list_insc.json())

def test_cenario_05_tentativa_inscricao_duplicada():
    """Cenário 5: Tentativa de inscrição duplicada (deve retornar 409 Conflict)."""
    ev = client.post("/eventos/", json={
        "titulo": "Palestra DevOps",
        "descricao": "CI/CD com Docker e Kubernetes",
        "data": "2026-12-02",
        "horario": "19:30",
        "local": "Lab 05",
        "capacidade": 15,
        "categoria": "Palestra"
    }).json()

    part = client.post("/participantes/", json={
        "nome": "Fernanda Costa",
        "email": "fernanda.costa@universidade.edu.br",
        "curso": "Ciência da Computação"
    }).json()

    # Primeira inscrição (sucesso)
    res1 = client.post(f"/eventos/{ev['id']}/inscricoes/{part['id']}")
    assert res1.status_code == 201

    # Segunda tentativa (duplicada)
    res2 = client.post(f"/eventos/{ev['id']}/inscricoes/{part['id']}")
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Participante já está inscrito neste evento."

def test_cenario_06_tentativa_inscricao_evento_inexistente():
    """Cenário 6: Tentativa de inscrição em evento inexistente (deve retornar 404 Not Found)."""
    part = client.post("/participantes/", json={
        "nome": "Carlos Drummond",
        "email": "carlos.drummond@universidade.edu.br",
        "curso": "Letras"
    }).json()

    res = client.post(f"/eventos/999999/inscricoes/{part['id']}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Evento não encontrado."

def test_cenario_07_tentativa_inscricao_sem_vagas_disponiveis():
    """Cenário 7: Tentativa de inscrição sem vagas disponíveis (deve retornar 409 Conflict)."""
    # Evento com capacidade para apenas 1 pessoa
    ev = client.post("/eventos/", json={
        "titulo": "Minicurso Especial de Segurança",
        "descricao": "Workshop restrito a 1 vaga",
        "data": "2026-12-05",
        "horario": "14:00",
        "local": "Sala VIP",
        "capacidade": 1,
        "categoria": "Minicurso"
    }).json()

    p1 = client.post("/participantes/", json={
        "nome": "Aluno Um",
        "email": "aluno1@universidade.edu.br",
        "curso": "Redes de Computadores"
    }).json()

    p2 = client.post("/participantes/", json={
        "nome": "Aluno Dois",
        "email": "aluno2@universidade.edu.br",
        "curso": "Redes de Computadores"
    }).json()

    # Inscrição do aluno 1 ocupa a única vaga
    res1 = client.post(f"/eventos/{ev['id']}/inscricoes/{p1['id']}")
    assert res1.status_code == 201

    # Inscrição do aluno 2 deve falhar por falta de vagas
    res2 = client.post(f"/eventos/{ev['id']}/inscricoes/{p2['id']}")
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Não existem vagas disponíveis para este evento."

def test_cenario_08_reinicializacao_e_persistencia_dados():
    """Cenário 8: Reinicialização da aplicação e verificação da persistência dos dados."""
    # 1. Cadastra um evento e um participante
    ev = client.post("/eventos/", json={
        "titulo": "Hackathon Anual 2026",
        "descricao": "Maratona de inovação e tecnologia",
        "data": "2026-12-15",
        "horario": "08:00",
        "local": "Ginásio Poliesportivo",
        "capacidade": 200,
        "categoria": "Competição"
    }).json()

    part = client.post("/participantes/", json={
        "nome": "Beatriz Ramos",
        "email": "beatriz.ramos@universidade.edu.br",
        "curso": "Engenharia de Software"
    }).json()

    client.post(f"/eventos/{ev['id']}/inscricoes/{part['id']}")

    # 2. Simula o encerramento da conexão/sessão e reinicialização criando uma nova instância de TestClient
    nova_sessao = SessionLocal()
    nova_sessao.close()
    novo_client = TestClient(app)

    # 3. Consulta novamente os dados persistidos no SQLite
    res_ev = novo_client.get(f"/eventos/{ev['id']}")
    assert res_ev.status_code == 200
    assert res_ev.json()["titulo"] == "Hackathon Anual 2026"

    res_part = novo_client.get(f"/participantes/{part['id']}")
    assert res_part.status_code == 200
    assert res_part.json()["nome"] == "Beatriz Ramos"

    res_insc = novo_client.get(f"/eventos/{ev['id']}/inscricoes")
    assert res_insc.status_code == 200
    assert any(p["id"] == part["id"] for p in res_insc.json())

def test_cenario_09_relatorio_ocupacao_eventos():
    """Cenário 9: Consulta do relatório de ocupação dos eventos."""
    # Criar evento com capacidade 10 e inscrever 2 participantes
    ev = client.post("/eventos/", json={
        "titulo": "Palestra Blockchain",
        "descricao": "Conceitos de Web3",
        "data": "2026-12-11",
        "horario": "20:00",
        "local": "Auditório C",
        "capacidade": 10,
        "categoria": "Palestra"
    }).json()

    p1 = client.post("/participantes/", json={
        "nome": "Part Ocupacao 1",
        "email": "ocup1@email.com",
        "curso": "Engenharia de Software"
    }).json()
    p2 = client.post("/participantes/", json={
        "nome": "Part Ocupacao 2",
        "email": "ocup2@email.com",
        "curso": "Engenharia de Software"
    }).json()

    client.post(f"/eventos/{ev['id']}/inscricoes/{p1['id']}")
    client.post(f"/eventos/{ev['id']}/inscricoes/{p2['id']}")

    res = client.get("/relatorios/eventos/ocupacao")
    assert res.status_code == 200
    relatorio = res.json()
    assert isinstance(relatorio, list)

    item = next(e for e in relatorio if e["evento_id"] == ev["id"])
    assert item["titulo"] == "Palestra Blockchain"
    assert item["capacidade"] == 10
    assert item["total_inscritos"] == 2
    assert item["vagas_disponiveis"] == 8
    assert item["percentual_ocupacao"] == 20.0

def test_cenario_10_relatorio_eventos_por_categoria():
    """Cenário 10: Consulta do relatório de eventos por categoria."""
    res = client.get("/relatorios/eventos/categorias")
    assert res.status_code == 200
    relatorio = res.json()
    assert isinstance(relatorio, list)

    for item in relatorio:
        assert "categoria" in item
        assert "total_eventos" in item
        assert "capacidade_total" in item
        assert "total_inscricoes" in item
        assert item["total_eventos"] >= 0
        assert item["capacidade_total"] >= 0
        assert item["total_inscricoes"] >= 0

def test_cenario_11_relatorio_participacao_por_curso():
    """Cenário 11: Consulta do relatório de participação por curso."""
    res = client.get("/relatorios/participantes/cursos")
    assert res.status_code == 200
    relatorio = res.json()
    assert isinstance(relatorio, list)

    for item in relatorio:
        assert "curso" in item
        assert "total_participantes" in item
        assert "total_inscricoes" in item
        assert item["total_participantes"] >= 0
        assert item["total_inscricoes"] >= 0

def test_cenario_12_relatorios_apos_inserir_atualizar_excluir():
    """Cenário 12: Verificação dos resultados dos relatórios após inserir, atualizar ou excluir registros."""
    # 1. Cadastra evento específico de categoria única para monitoramento exato
    cat_teste = "CategoriaDinamica"
    ev = client.post("/eventos/", json={
        "titulo": "Evento Dinamico Teste",
        "descricao": "Teste de dinamismo nos relatorios",
        "data": "2026-12-20",
        "horario": "15:00",
        "local": "Sala D",
        "capacidade": 100,
        "categoria": cat_teste
    }).json()

    # Verifica relatório de categorias com o novo evento
    rel_cat1 = client.get("/relatorios/eventos/categorias").json()
    item_cat1 = next(c for c in rel_cat1 if c["categoria"] == cat_teste)
    assert item_cat1["total_eventos"] == 1
    assert item_cat1["capacidade_total"] == 100
    assert item_cat1["total_inscricoes"] == 0

    # 2. Cadastra participante com curso único e inscreve
    curso_teste = "CursoDinamico"
    part = client.post("/participantes/", json={
        "nome": "Participante Dinamico",
        "email": "dinamico@teste.com",
        "curso": curso_teste
    }).json()

    client.post(f"/eventos/{ev['id']}/inscricoes/{part['id']}")

    # Verifica relatórios atualizados com a inscrição
    rel_ocup = client.get("/relatorios/eventos/ocupacao").json()
    item_ocup = next(o for o in rel_ocup if o["evento_id"] == ev["id"])
    assert item_ocup["total_inscritos"] == 1
    assert item_ocup["vagas_disponiveis"] == 99
    assert item_ocup["percentual_ocupacao"] == 1.0

    rel_curso = client.get("/relatorios/participantes/cursos").json()
    item_curso = next(c for c in rel_curso if c["curso"] == curso_teste)
    assert item_curso["total_participantes"] == 1
    assert item_curso["total_inscricoes"] == 1

    # 3. Exclui o evento e verifica que os relatórios refletem a exclusão dinamicamente
    client.delete(f"/eventos/{ev['id']}")

    rel_cat_pos_del = client.get("/relatorios/eventos/categorias").json()
    assert not any(c["categoria"] == cat_teste for c in rel_cat_pos_del)

    rel_ocup_pos_del = client.get("/relatorios/eventos/ocupacao").json()
    assert not any(o["evento_id"] == ev["id"] for o in rel_ocup_pos_del)
