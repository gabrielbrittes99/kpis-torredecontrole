# AGENTS.md - KPIs Torre de Controle

## Project Overview

Dashboard de análise de combustível e frota integrado com TruckPag.

**Stack:**
- Backend: Python 3.11+ / FastAPI / SQLAlchemy / pandas
- Frontend: Vue 3 / Vite / ApexCharts
- Database: PostgreSQL (Railway) + SQL Server

## Build & Run Commands

### Start Everything
```bash
./start.sh
```

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (Vue + Vite)
```bash
cd frontend
npm install
npm run dev      # Development server on port 5173
npm run build    # Production build to frontend/dist
```

### Testing
No formal test framework configured. For manual API testing:
- Swagger UI: http://localhost:8000/docs
- Health check: `curl http://localhost:8000/health`

### Linting
No linting tools configured. Follow style guidelines below.

## Code Style Guidelines

### Python (Backend)

**Imports:**
- Standard library first, then third-party, then local
- Use absolute imports from project root
```python
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query

from db_pneus import get_pneus_df
```

**Naming:**
- snake_case for functions, variables, modules
- UPPER_CASE for constants
- Prefix private functions with `_`

**Types:**
- Use type hints for function parameters and returns
- Use `Optional[T]` for nullable parameters
- Use Pydantic models for complex request/response bodies

**Error Handling:**
- Use try/except with specific exception types
- Log errors with `logging.getLogger(__name__)`
- Return empty results instead of raising on data issues

**API Endpoints:**
- Prefix with `/api/{module}/`
- Use Query parameters for filters
- Return dict/list for JSON responses
- Include `tags` for Swagger organization

### JavaScript/Vue (Frontend)

**Imports:**
- ES6 import syntax
- Group: Vue core, then libraries, then local components
```javascript
import { ref, computed, onMounted } from 'vue'
import ApexCharts from 'vue3-apexcharts'
import { fetchPneusKpis } from '../api/pneus.js'
```

**Naming:**
- camelCase for variables, functions, props
- PascalCase for Vue components
- kebab-case for HTML attributes

**Composition API:**
- Always use `<script setup>` syntax
- Use `ref()` for reactive primitives
- Use `computed()` for derived values
- Use `onMounted()` for data loading

**Formatting:**
- 2-space indentation
- Single quotes for strings
- Trailing commas in objects/arrays
- Prettier not configured - maintain consistency

## Architecture Notes

### Backend Structure
- `backend/main.py` - FastAPI app, CORS, router registration
- `backend/routers/` - One module per business domain
- `backend/db_*.py` - Database access layers
- `backend/data_cache.py` - TTL cache for pandas DataFrames

### Frontend Structure
- `frontend/src/views/` - Page-level components (dashboards)
- `frontend/src/components/` - Reusable UI components
- `frontend/src/api/` - API client functions
- `frontend/src/router.js` - Vue Router configuration

### Data Flow
1. Frontend calls API via functions in `src/api/*.js`
2. Backend routers call database modules
3. Database modules read from PostgreSQL/SQL Server/excels
4. Results cached in memory with TTL (30min default)

## Common Patterns

### Adding New API Endpoint
1. Create router in `backend/routers/{module}.py`
2. Add router to `main.py` imports and `app.include_router()`
3. Create API function in `frontend/src/api/{module}.js`
4. Import and use in Vue component

### Adding New Dashboard View
1. Create `.vue` file in `frontend/src/views/`
2. Add route in `frontend/src/router.js`
3. Add navigation button in `frontend/src/App.vue`

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection
- `CORS_ORIGINS` - Allowed origins (default: *)

### Frontend (.env)
- `VITE_API_URL` - Backend URL (default: http://localhost:8000)

## Deployment

Railway deployment uses:
- Backend: Dockerfile at `backend/Dockerfile`
- Frontend: Static build from `frontend/dist`
