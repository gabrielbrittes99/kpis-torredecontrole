# KPIs Torre de Controle — Gritsch

Dashboard de análise de combustível integrado com TruckPag e PostgreSQL (Railway).

## Stack

- **Backend:** Python 3.11+ · FastAPI · SQLAlchemy · pandas
- **Frontend:** Vue 3 · Vite · ApexCharts (vue3-apexcharts)
- **Banco:** PostgreSQL (Railway) — tabela `integration_truckpag_transacoes`

---

## Pré-requisitos

- Python 3.11+
- Node.js 18+ / npm

---

## Backend

### 1. Configurar variáveis de ambiente

Crie `backend/.env` (já existe localmente — não commitar):

```env
DB_HOST=...
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...

TRUCKPAG_URL=...
TRUCKPAG_USER=...
TRUCKPAG_PASSWORD=...

CORS_ORIGINS=http://localhost:5173
```

### 2. Instalar dependências

```fish
# fish shell (WSL)
cd backend
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

```bash
# bash / zsh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Rodar o servidor

```fish
# Sempre ative o venv antes (fish shell)
source .venv/bin/activate.fish
uvicorn main:app --reload --port 8000
```

API disponível em: `http://localhost:8000`
Docs interativos: `http://localhost:8000/docs`

---

## Frontend

### 1. Instalar dependências

```bash
cd frontend
npm install
```

### 2. Rodar em desenvolvimento

```bash
npm run dev
```

App disponível em: `http://localhost:5173`

> O frontend aponta para o backend em `http://localhost:8000` por padrão.

### 3. Build para produção

```bash
npm run build
# output em frontend/dist/
```

---

## Estrutura do projeto

```
├── backend/
│   ├── main.py           # FastAPI app + routers
│   ├── db.py             # Conexão PostgreSQL (SQLAlchemy)
│   ├── data_cache.py     # Cache pandas com TTL 30min
│   ├── routers/
│   │   ├── combustivel.py   # Visão Gerencial
│   │   ├── precos.py        # Inteligência de Preços
│   │   ├── frota.py         # Eficiência de Frota
│   │   └── diretoria.py     # Visão da Diretoria
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.vue          # Sidebar + navegação
    │   ├── views/           # 4 dashboards
    │   └── components/      # 16 componentes
    └── package.json
```

---

## Endpoints principais

| Seção | Prefixo |
|---|---|
| Visão Gerencial | `GET /api/combustivel/` |
| Inteligência de Preços | `GET /api/precos/` |
| Eficiência de Frota | `GET /api/frota/` |
| Visão da Diretoria | `GET /api/diretoria/` |
| Health check | `GET /health` |
| Forçar refresh do cache | `POST /api/combustivel/cache/refresh` |

---

## Deploy (Railway)

Dois serviços separados no Railway:

- **backend:** build via `Dockerfile` na raiz de `backend/`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **frontend:** build `npm run build`, serve estático de `dist/`

As variáveis de ambiente do banco são configuradas no painel do Railway.
