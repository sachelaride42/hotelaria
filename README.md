# Sistema de Gestão Hoteleira

Projeto de Conclusão de Curso (TCC) em Engenharia de Software. Automatiza o fluxo operacional da recepção de um hotel: reservas, check-in, check-out, controle de consumo, governança (limpeza) e pagamentos.

---

## Funcionalidades

- Dashboard com grade de quartos e status em tempo real
- Check-in de hóspedes
- Gestão de reservas
- Controle de hospedagens ativas com grade de ocupação
- Lançamento de produtos e serviços por hospedagem
- Extrato financeiro por hospedagem
- Checkout e fechamento de conta
- Governança: controle e atualização do status de limpeza dos quartos
- Cadastro e gestão de clientes
- Cadastro e gestão de quartos
- Cadastro e gestão de tipos de quarto
- Cadastro e gestão de produtos e serviços
- Gestão de usuários (recepcionistas e gerentes)
- Perfil de usuário autenticado

---

## Interface

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Reservas
#### Criar Reserva
![Criar reserva](docs/screenshots/criar-reserva.png)
#### Gestão de Reservas
![Gestão de reservas](docs/screenshots/gestao-de-reservas.png)

### Check-in
#### Check-in - etapa 1
![Check-in — etapa 1](docs/screenshots/checkin-etapa-1.png)
#### Check-in - etapa 2
![Check-in — etapa 2](docs/screenshots/checkin-etapa-2.png)

### Hospedagens
#### Hospedagens ativas
![Hospedagens ativas](docs/screenshots/hospedagens-ativas.png)
#### Detalhes da Hospedagem
![Detalhes da hospedagem](docs/screenshots/detalhes-da-hospedagem.png)
#### Hóspede
![Hóspede](docs/screenshots/hospede.png)
#### Histórico da Hospedagem
![Histórico de hospedagem](docs/screenshots/historico-hospedagem.png)
#### Extrato da conta
![Extrato da conta](docs/screenshots/extrato-da-conta.png)

### Produtos / Serviços
#### Lançar Produtos / Serviços
![Lançar Produtos / Serviços](docs/screenshots/lancar%20produtos-servicos.png)
#### Extrato da conta
![Extrato da conta](docs/screenshots/extrato-da-conta.png)

### Checkout
#### Checkout e Caixa
![Checkout e caixa](docs/screenshots/checkout-e-caixa.png)
#### Realizar Checkout
![Realizar checkout](docs/screenshots/realizar-checkout.png)

### Governança
#### Governança
![Governança](docs/screenshots/governanca.png)

### Administração
#### Gestão de Clientes
![Gestão de clientes](docs/screenshots/gestao-de-clientes.png)
#### Gestão de Produtos e Serviços
![Gestão de produtos e serviços](docs/screenshots/gestao-de-produtos-servicos.png)
#### Gestão de Quartos
![Gestão de quartos](docs/screenshots/gestao-de-quartos.png)
#### Gestão de Tipos de Quarto
![Tipos de quarto](docs/screenshots/gestao-de-tipos-de-quartos.png)
#### Gestão de Usuários
![Gestão de usuários](docs/screenshots/gestao-de-usuarios.png)

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

## Sugestões para futuros aprimoramentos

O atual sistema já cumpre todas as funcionalidades para o escopo de trabalho em que foi definido. Porém, ainda há espaço para aprimoramentos se o objetivo for tornar o sistema mais robusto.

- Cadastro completo de hóspedes com dados legalmente exigidos
- Auditabilidade econômico-financeira com registros imutáveis
- Conformidade e auditabilidade segundo a LGPD
- Rastreabilidade de operações críticas por funcionário responsável
- Fechamento de caixa por turno vinculado ao operador
- Relatório de receita por período com exportação
- Integração com meios de pagamento eletrônico (cartão e PIX)
- Emissão de nota fiscal eletrônica (NF-e) no checkout
- Controle de estoque de produtos com alertas de reposição
- Controle de manutenção preventiva e corretiva de quartos
- Painel de indicadores gerenciais (taxa de ocupação, RevPAR, ticket médio)
- Integração com plataformas de reserva online (Booking.com, Airbnb)
- Portal de autoatendimento para hóspedes
- Backup automático e plano de recuperação de dados