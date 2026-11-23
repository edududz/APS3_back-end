# API de Gerenciamento de Eventos Acadêmicos — APS 3
**Persistência e Consolidação de Dados com SQLite e SQLAlchemy**

Esta aplicação é a evolução da **APS 2**, substituindo o armazenamento em memória por um banco de dados relacional **SQLite** gerenciado pelo **SQLAlchemy ORM**. O projeto foi estruturado seguindo o padrão arquitetural **MVC** (Model-View-Controller, onde o Controller recebe as requisições HTTP e o Service encapsula as regras de negócio e consultas ao banco) e adiciona recursos avançados de consolidação de dados e relatórios analíticos.

---

## 1. Descrição do Projeto

A API RESTful permite que uma instituição de ensino gerencie seus eventos acadêmicos (palestras, workshops, minicursos, competições, etc.), participantes e inscrições com garantia de persistência e integridade referencial. Além das operações CRUD fundamentais, a API disponibiliza relatórios com agregações dinâmicas sobre ocupação de eventos, distribuição por categoria e engajamento por curso acadêmico.

### Principais Características
- **Persistência Relacional**: Banco de dados SQLite persistido em disco via SQLAlchemy ORM.
- **Integridade Referencial & Cascata**: Chaves estrangeiras ativadas (`PRAGMA foreign_keys=ON`) com exclusão em cascata (`cascade="all, delete-orphan"`), prevenindo registros órfãos.
- **Validação com Pydantic v2**: Schemas tipados garantem validações rígidas de e-mail, limites de capacidade, datas e strings obrigatórias.
- **Consolidação Dinâmica**: Consultas SQL avançadas utilizando `func.count`, `func.sum`, `distinct` e subqueries sem valores estáticos.
- **Tratamento de Exceções**: Retornos HTTP padronizados (`404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`) com mensagens claras.

---

## 2. Estrutura do Projeto (MVC)

A arquitetura do projeto separa claramente as responsabilidades:

```text
aps3_eventos/
│
├── main.py                    # Ponto de entrada da aplicação FastAPI e inicialização do banco
├── database.py                # Configuração da engine SQLite, sessões e Base ORM
├── requirements.txt           # Dependências do projeto
├── README.md                  # Documentação completa
├── eventos.db                 # Arquivo de dados SQLite persistente
│
├── controller/                # Camada Controller: rotas HTTP e injeção de dependências
│   ├── __init__.py
│   ├── evento_controller.py
│   ├── participante_controller.py
│   ├── inscricao_controller.py
│   └── relatorio_controller.py
│
├── model/                     # Camada Model (ORM): mapeamento objeto-relacional com SQLAlchemy
│   ├── __init__.py
│   ├── evento.py              # Entidade Evento
│   ├── participante.py        # Entidade Participante
│   └── inscricao.py           # Entidade Inscricao com FKs e UniqueConstraint
│
├── schema/                    # Camada Schema: validação de entrada e serialização com Pydantic
│   ├── __init__.py
│   ├── evento_schema.py
│   ├── participante_schema.py
│   ├── inscricao_schema.py
│   └── relatorio_schema.py
│
├── service/                   # Camada Service: regras de negócio e consultas SQLAlchemy
│   ├── __init__.py
│   ├── evento_service.py
│   ├── participante_service.py
│   ├── inscricao_service.py
│   └── relatorio_service.py
│
├── test_aps3.py               # Suíte automatizada de testes com pytest (12 cenários + testes de integridade)
└── run_cenarios.py            # Script interativo de demonstração e geração de evidências dos 12 cenários
```

---

## 3. Configuração do Banco de Dados

### 3.1 Localização do Arquivo SQLite
O banco de dados SQLite é criado e persistido no arquivo:
```
./eventos.db  (localizado na raiz do projeto)
```
URI de conexão: `sqlite:///./eventos.db`

### 3.2 Gerenciamento de Conexão e Sessões (`database.py`)
- **Engine**: configurada com `connect_args={"check_same_thread": False}` para compatibilidade com o modelo assíncrono do FastAPI.
- **Integridade de Chaves Estrangeiras**: evento SQLAlchemy escuta a conexão e executa `PRAGMA foreign_keys=ON;`, garantindo a exclusão em cascata das inscrições vinculadas quando um evento ou participante é excluído.
- **Ciclo de Vida das Sessões**: a função geradora `get_db()` é injetada nas rotas via `Depends(get_db)`. Ela abre uma sessão transacional `SessionLocal()` e assegura seu fechamento no bloco `finally`.
- **Criação das Tabelas**: a função `init_db()` invoca `Base.metadata.create_all(bind=engine)` no startup da aplicação (`lifespan`), sem a necessidade de migrações manuais.

---

## 4. Instalação e Execução

### Pré-requisitos
- Python 3.8 ou superior
- Gerenciador de pacotes `pip`

### Instalação das Dependências
```bash
# Clone ou acerte o diretório do projeto
cd aps3_eventos

# Criação do ambiente virtual (recomendado)
python -m venv venv

# Ativação do ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

# Instalação das bibliotecas necessárias
pip install -r requirements.txt
```

### Execução da Aplicação
Para rodar a API em modo de desenvolvimento com recarregamento automático:
```bash
uvicorn main:app --reload
```
A API estará acessível em: `http://127.0.0.1:8000`

### Documentação Interativa
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. Descrição das Rotas Principais

### 5.1 Eventos
- `POST /eventos/`: Cadastra um novo evento (HTTP 201).
- `GET /eventos/`: Retorna a lista de todos os eventos (HTTP 200).
- `GET /eventos/{id}`: Retorna os detalhes de um evento (HTTP 200 ou 404).
- `PUT /eventos/{id}`: Atualiza os dados de um evento (HTTP 200 ou 404).
- `DELETE /eventos/{id}`: Exclui um evento e suas inscrições associadas em cascata (HTTP 204 ou 404).

### 5.2 Participantes
- `POST /participantes/`: Cadastra um participante (HTTP 201 ou 409 se e-mail já existir).
- `GET /participantes/`: Retorna todos os participantes (HTTP 200).
- `GET /participantes/{id}`: Retorna os dados de um participante (HTTP 200 ou 404).
- `PUT /participantes/{id}`: Atualiza os dados de um participante (HTTP 200, 404 ou 409).
- `DELETE /participantes/{id}`: Exclui um participante e suas inscrições associadas em cascata (HTTP 204 ou 404).

### 5.3 Inscrições
- `POST /eventos/{evento_id}/inscricoes/{participante_id}`: Inscreve o participante no evento (HTTP 201).
  - Valida se o evento existe (`404`);
  - Valida se o participante existe (`404`);
  - Valida se já está inscrito (`409 Conflict: "Participante já está inscrito neste evento."`);
  - Valida se há vagas disponíveis (`409 Conflict: "Não existem vagas disponíveis para este evento."`).
- `GET /eventos/{evento_id}/inscricoes`: Lista os participantes inscritos no evento (HTTP 200 ou 404).

### 5.4 Relatórios e Consolidações
- `GET /relatorios/eventos/ocupacao`: Relatório detalhado de ocupação por evento.
- `GET /relatorios/eventos/categorias`: Agrupamento consolidado por categoria de evento.
- `GET /relatorios/participantes/cursos`: Agrupamento consolidado de inscritos e inscrições por curso.

---

## 6. Exemplos de Utilização da API (JSON)

### 6.1 Cadastro de Evento (`POST /eventos/`)
**Requisição:**
```json
{
  "titulo": "Workshop de Python Avançado",
  "descricao": "Tópicos modernos de FastAPI e SQLAlchemy ORM.",
  "data": "2026-12-10",
  "horario": "19:00",
  "local": "Auditório Principal",
  "capacidade": 50,
  "categoria": "Workshop"
}
```
**Resposta (HTTP 201 Created):**
```json
{
  "id": 1,
  "titulo": "Workshop de Python Avançado",
  "descricao": "Tópicos modernos de FastAPI e SQLAlchemy ORM.",
  "data": "2026-12-10",
  "horario": "19:00",
  "local": "Auditório Principal",
  "capacidade": 50,
  "categoria": "Workshop"
}
```

### 6.2 Cadastro de Participante (`POST /participantes/`)
**Requisição:**
```json
{
  "nome": "Mariana Silva",
  "email": "mariana.silva@universidade.edu.br",
  "curso": "Engenharia de Software"
}
```
**Resposta (HTTP 201 Created):**
```json
{
  "id": 1,
  "nome": "Mariana Silva",
  "email": "mariana.silva@universidade.edu.br",
  "curso": "Engenharia de Software"
}
```

### 6.3 Inscrição de Participante (`POST /eventos/1/inscricoes/1`)
**Resposta (HTTP 201 Created):**
```json
{
  "detail": "Inscrição realizada com sucesso."
}
```

### 6.4 Relatório de Ocupação (`GET /relatorios/eventos/ocupacao`)
**Resposta (HTTP 200 OK):**
```json
[
  {
    "evento_id": 1,
    "titulo": "Workshop de Python Avançado",
    "capacidade": 50,
    "total_inscritos": 1,
    "vagas_disponiveis": 49,
    "percentual_ocupacao": 2.0
  }
]
```

### 6.5 Relatório de Eventos por Categoria (`GET /relatorios/eventos/categorias`)
**Resposta (HTTP 200 OK):**
```json
[
  {
    "categoria": "Workshop",
    "total_eventos": 1,
    "capacidade_total": 50,
    "total_inscricoes": 1
  }
]
```

### 6.6 Relatório de Participação por Curso (`GET /relatorios/participantes/cursos`)
**Resposta (HTTP 200 OK):**
```json
[
  {
    "curso": "Engenharia de Software",
    "total_participantes": 1,
    "total_inscricoes": 1
  }
]
```

---

## 7. Demonstração e Execução dos 12 Cenários de Teste

O projeto atende com rigor todos os 12 cenários descritos na seção 11 do documento de requisitos:

| # | Cenário Exigido | Status da Implementação |
|---|---|---|
| 1 | Cadastro e consulta de eventos utilizando o banco de dados | Implementado e verificado no SQLite |
| 2 | Cadastro e consulta de participantes | Implementado e verificado no SQLite |
| 3 | Atualização e exclusão de registros | Implementado com integridade e retorno 204 / 404 |
| 4 | Inscrição de um participante em um evento | Implementado e verificado via relacionamento |
| 5 | Tentativa de inscrição duplicada | Retorna HTTP 409 (`Participante já está inscrito neste evento.`) |
| 6 | Tentativa de inscrição em evento inexistente | Retorna HTTP 404 (`Evento não encontrado.`) |
| 7 | Tentativa de inscrição sem vagas disponíveis | Retorna HTTP 409 (`Não existem vagas disponíveis para este evento.`) |
| 8 | Reinicialização da aplicação e verificação da persistência | Validado recriando cliente e consultando os dados no SQLite |
| 9 | Consulta do relatório de ocupação dos eventos | Implementado com SQLAlchemy (cálculo de vagas e %) |
| 10 | Consulta do relatório de eventos por categoria | Implementado com subqueries dinâmicas no SQLAlchemy |
| 11 | Consulta do relatório de participação por curso | Implementado com `COUNT(DISTINCT)` no SQLAlchemy |
| 12 | Verificação dos resultados após inserir/atualizar/excluir | Validado com recálculo automático e dinâmico |

### Como Executar os Testes Automatizados (Pytest)
```bash
pytest -v test_aps3.py
```

### Como Executar a Demonstração Completa com Evidências em Console
```bash
python run_cenarios.py
```
Esse script executará passo a passo os 12 cenários exibindo no console as requisições, status HTTP e respostas JSON formatadas.
