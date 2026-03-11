# KPIs Torre de Controle — Gritsch

Dashboard de análise de combustível e frota integrado com TruckPag, PostgreSQL (Railway) e SQL Server.

## Stack

- **Backend:** Python 3.11+ · FastAPI · SQLAlchemy · pandas
- **Frontend:** Vue 3 · Vite · ApexCharts (vue3-apexcharts)
- **Banco:** PostgreSQL (Railway) + SQL Server (BlueFleet)

---

## ⚡ Início Rápido (clone e rode)

### Pré-requisitos

- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Git** — [git-scm.com](https://git-scm.com/)

### 1. Clonar o repositório

```bash
git clone https://github.com/gabrielbrittes99/kpis-torredecontrole.git
cd kpis-torredecontrole
```

### 2. Rodar tudo com um comando

```bash
chmod +x start.sh
./start.sh
```

Isso vai:
- Criar o ambiente virtual Python (se não existir)
- Instalar dependências do backend e frontend
- Subir o **backend** na porta `8000`
- Subir o **frontend** na porta `5173`

Depois é só acessar:

| Serviço | URL |
|---|---|
| 🖥️ Frontend (Dashboard) | http://localhost:5173 |
| 🔧 Backend API | http://localhost:8000 |
| 📄 Swagger Docs | http://localhost:8000/docs |

> **Pressione `Ctrl+C`** no terminal para parar tudo.

---

## 🔧 Rodando Separadamente

Se preferir rodar backend e frontend em terminais separados:

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Estrutura do Projeto

```
kpis-torredecontrole/
├── start.sh                  # Script para rodar tudo junto
├── backend/
│   ├── main.py               # FastAPI app + routers
│   ├── db.py                 # Conexão PostgreSQL (SQLAlchemy)
│   ├── db_sqlserver.py       # Conexão SQL Server
│   ├── data_cache.py         # Cache pandas com TTL 30min
│   ├── anp_client.py         # Client API ANP
│   ├── truckpag_client.py    # Client API TruckPag
│   ├── .env                  # Variáveis de ambiente (já configurado)
│   ├── requirements.txt
│   └── routers/
│       ├── combustivel.py    # Visão Gerencial
│       ├── precos.py         # Inteligência de Preços
│       ├── frota.py          # Eficiência de Frota
│       ├── diretoria.py      # Visão da Diretoria
│       ├── operacional.py    # Visão Operacional
│       ├── veiculos.py       # Dados de Veículos
│       └── benchmark.py      # Benchmark ANP
├── frontend/
│   ├── .env                  # URL do backend (já configurado)
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── App.vue           # Sidebar + navegação
│       ├── views/            # 5 dashboards
│       ├── components/       # Componentes visuais
│       └── api/              # Chamadas à API
└── documentacao API - Truckpag/  # PDFs da documentação TruckPag
```

---

## 🔌 Endpoints Principais

| Seção | Prefixo |
|---|---|
| Visão Gerencial | `GET /api/combustivel/` |
| Inteligência de Preços | `GET /api/precos/` |
| Eficiência de Frota | `GET /api/frota/` |
| Visão da Diretoria | `GET /api/diretoria/` |
| Visão Operacional | `GET /api/operacional/` |
| Veículos | `GET /api/veiculos/` |
| Benchmark ANP | `GET /api/benchmark/` |
| Health check | `GET /health` |
| Refresh cache | `POST /api/combustivel/cache/refresh` |

---

## 🌐 Deploy (Railway)

Dois serviços separados no Railway:

- **Backend:** build via `Dockerfile` na raiz de `backend/`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend:** build `npm run build`, serve estático de `dist/`

As variáveis de ambiente do banco são configuradas no painel do Railway.
