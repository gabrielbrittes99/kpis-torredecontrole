# KPIs Torre de Controle

Torre de monitoramento de KPIs da Gritsch via TV.

## Como usar na TV (Windows)

### 1. Clone o projeto
```powershell
git clone <url-do-repositorio> kpis-torredecontrole
cd kpis-torredecontrole
```

### 2. Configure o ambiente
Crie o arquivo `backend\.env` com suas credenciais:
```env
TRUCKPAG_URL=https://api.prd.truckpag.com.br
TRUCKPAG_TOKEN=seu_token_aqui

DB_HOST=seu_host
DB_PORT=5432
DB_NAME=railway
DB_USER=seu_usuario
DB_PASSWORD=sua_senha

SQLSERVER_HOST=bi.bluefleet.com.br
SQLSERVER_PORT=1433
SQLSERVER_USER=seu_usuario
SQLSERVER_PASSWORD=sua_senha
SQLSERVER_DB=referencia
```

### 3. Setup (primeira vez)
```powershell
.\setup.ps1
```

### 4. Rode
```powershell
.\run.ps1
```

Acesse: **http://localhost:8000**

## Requisitos
- Python 3.10+
- Node.js 18+
- Git