# Sistema de Gestão Hoteleira

Projeto de Conclusão de Curso (TCC) em Engenharia de Software. Automatiza o fluxo operacional da recepção de um hotel: reservas, check-in, check-out, controle de consumo, governança (limpeza) e pagamentos.

---

## Tecnologias

| Camada | Stack |
|---|---|
| **Frontend** | React 19, React Router v7, Vite |
| **Backend** | Python 3.14, FastAPI, SQLAlchemy (async), Alembic |
| **Banco de dados** | PostgreSQL 16 (via Docker) |
| **Autenticação** | JWT (python-jose + bcrypt) |
| **Testes** | pytest + pytest-asyncio, SQLite in-memory |

---

## Pré-requisitos

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para o banco)
- [Python 3.14+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/) e npm

---

## Instalação e execução

### 1. Clone o repositório

```bash
git clone https://github.com/<seu-usuario>/projetoHotelaria.git
cd projetoHotelaria
```

### 2. Suba o banco de dados

```bash
docker compose up -d
```

O PostgreSQL ficará disponível em `localhost:5000` (mapeado internamente para a porta 5432).

### 3. Configure o backend

```bash
# Copie o arquivo de variáveis de ambiente
cp backend/.env.example backend/.env
```

Abra `backend/.env` e preencha os valores:

```dotenv
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:1234@localhost:5000/hotelaria
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:1234@localhost:5000/hotelaria
SECRET_KEY=<gere uma chave abaixo>
```

> Para gerar uma `SECRET_KEY` segura:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Instale as dependências do backend e aplique as migrations

```bash
cd backend

# Crie e ative o ambiente virtual
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# Instale os pacotes
pip install -r requirements.txt

# Volte para a raiz e aplique as migrations
cd ..
$env:PYTHONPATH="."   # PowerShell
# export PYTHONPATH=. # Linux/macOS

python -m alembic -c backend/alembic.ini upgrade head
```

### 5. Inicie o backend

```bash
# Na raiz do projeto, com o .venv ativo
$env:PYTHONPATH="."   # PowerShell
# export PYTHONPATH=. # Linux/macOS

uvicorn backend.src.main:app --reload
```

A API estará disponível em **http://localhost:8000**.
Documentação interativa (Swagger): **http://localhost:8000/docs**

Na primeira inicialização, um usuário gerente padrão é criado automaticamente:

| Campo | Valor |
|---|---|
| E-mail | `admin@hotel.com` |
| Senha | `admin123` |

> Altere a senha após o primeiro acesso.

### 6. Instale as dependências do frontend e inicie

```bash
cd frontend
npm install
npm run dev
```

O frontend estará disponível em **http://localhost:5173**.

---

## Executando os testes

Na raiz do projeto, com o `.venv` ativo:

```bash
# Windows (PowerShell)
$env:PYTHONPATH="."
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v

# Linux / macOS
PYTHONPATH=. python -m pytest backend/tests/ -v
```

---

## Estrutura do projeto

```
projetoHotelaria/
├── backend/
│   ├── src/
│   │   ├── api/            # Routers, schemas e dependências (FastAPI)
│   │   ├── domain/         # Modelos de domínio e serviços de negócio
│   │   └── infra/          # ORM, repositórios e conexão com o banco
│   ├── migrations/         # Scripts Alembic
│   ├── tests/              # Testes unitários e de integração
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   └── src/                # Componentes React e páginas
├── docker-compose.yml
└── pytest.ini
```

---

