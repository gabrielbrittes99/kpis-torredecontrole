# Plano de Refatoração — KPIs Torre de Controle

> **Criado em:** 2026-04-08
> **Status:** Em andamento
> **Estimativa:** ~5 dias de trabalho (módulo por módulo)

---

## Sumário

1. [Visão Geral do Estado Atual](#1-visão-geral-do-estado-atual)
2. [Mapa de Fontes de Dados](#2-mapa-de-fontes-de-dados)
3. [Mapa de Endpoints → Views](#3-mapa-de-endpoints--views)
4. [Erros Críticos a Corrigir](#4-erros-críticos-a-corrigir)
5. [Consolidação de Routers](#5-consolidação-de-routers)
6. [Corrigir Fontes Existentes](#6-corrigir-fontes-existentes)
7. [Escopo do Schema torre](#7-escopo-do-schema-torre)
8. [Automatização ANP](#8-automatização-anp)
9. [Plano de Execução por Módulo](#9-plano-de-execução-por-módulo)
10. [Checklist Final](#10-checklist-final)

---

## 1. Visão Geral do Estado Atual

### Stack
| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11 + FastAPI |
| Frontend | Vue 3 + Vite + ApexCharts |
| BD Abastecimentos | PostgreSQL (Railway) |
| BD Transações RT | PostgreSQL DW (`silver`) |
| BD Veículos/Manutenção | SQL Server (BlueFleet) |
| BD Próprio | PostgreSQL DW (`torre`) — APENAS tabelas novas sem origem existente |
| Dados FKM | Excel `.xlsb` — lido diretamente (sem cópia) |
| Dados ANP | DW `silver.anp_precos` (ETL manual) |
| APIs Externas | TruckPag (recusadas), EIA (Brent), AwesomeAPI (câmbio) |

### Números
- **18 routers** no backend
- **12 views** no frontend
- **~6 routers sem uso** direto no frontend (candidatos a remoção/consolidação)
- **4 erros críticos** impedindo endpoints de funcionar

---

## 2. Mapa de Fontes de Dados

### 2.1 Railway PostgreSQL
| Tabela | Conteúdo | Usado por |
|--------|----------|-----------|
| `integration_truckpag_transacoes` | Abastecimentos históricos (110k+ registros) | `data_cache.py` (fallback) |

**Papel:** Fonte de abastecimentos. O `data_cache.py` usa como fallback quando o DW não está configurado.

### 2.2 DW PostgreSQL — Schema `silver`
| Tabela | Conteúdo | Usado por |
|--------|----------|-----------|
| `silver.truckpag_analitico_transacao` | Transações real-time (abastecimento + pedágio + estornos) | `data_cache.py` (primário) |
| `silver.anp_precos` | Preços ANP por UF/produto | `anp_client.py` |

**Papel:** Fonte primária de transações e benchmark ANP.

### 2.3 DW PostgreSQL — Schema `torre` (nosso)
| Tabela | Conteúdo | Status |
|--------|----------|--------|
| *(a definir)* | FKM fechamento mensal | **A criar** |
| *(a definir)* | Veículos (cópia SQL Server) | **A criar** |
| *(a definir)* | Manutenção (cópia SQL Server) | **A criar** |

**Papel:** Nosso schema para tabelas derivadas e ETLs.

### 2.4 SQL Server BlueFleet
| Tabela | Conteúdo | Usado por |
|--------|----------|-----------|
| `Veiculos` | Cadastro de veículos (placa, modelo, filial, FIPE) | `db_sqlserver.py` |
| `ItensOrdemServico` | Ordens de serviço de manutenção (770k+ registros) | `db_sqlserver.py` |

**Papel:** Fonte de veículos e manutenção. **Será copiado para DW `torre`** via ETL.

### 2.5 Excel FKM
| Arquivo | Conteúdo | Usado por |
|---------|----------|-----------|
| `Evolucao FKM 2026.xlsb` | Fechamento mensal (7k+ linhas, 611 placas) | `db_fkm.py` |

**Papel:** Fonte do FKM. **Será migrado para DW `torre`** com ETL de importação.

### 2.6 APIs Externas
| API | Conteúdo | Módulo |
|-----|----------|--------|
| TruckPag | Transações recusadas em tempo real | `truckpag_api.py` |
| EIA (gov US) | Preço Brent (petróleo) | `market_client.py` |
| AwesomeAPI | Câmbio USD/BRL | `market_client.py` |
| Google News RSS | Notícias combustível/logística | `market_client.py` |
| ANP (gov BR) | Preços públicos de combustível | `etl_anp.py` |

---

## 3. Mapa de Endpoints → Views

### 3.1 Routers USADOS pelo frontend

| Router | Prefixo API | View(s) que consome | Fonte de dados |
|--------|-------------|---------------------|----------------|
| `visao_geral` | `/api/visao-geral` | VisaoGeral.vue | data_cache (transações) |
| `operacional` | `/api/operacional` | DashboardOperacional.vue | data_cache + KML refs |
| `diretoria` | `/api/diretoria` | DashboardDiretoria.vue | data_cache + benchmark |
| `precos` | `/api/precos` | VisaoGeral + Operacional | data_cache (transações) |
| `benchmark` | `/api/benchmark` | DashboardDiretoria.vue | ANP + data_cache |
| `manutencao` | `/api/manutencao` | ManutencaoGeral.vue | FKM + SQL Server |
| `pedagios` | `/api/pedagios` | PedagiosGeral.vue | data_cache (pedágios) |
| `tco` | `/api/tco` | TcoGeral.vue | FKM + SQL Server + cache |
| `fkm` | `/api/fkm` | DashboardFKM.vue | FKM Excel |
| `gestao_transacoes` | `/api/gestao-transacoes` | GestaoTransacoes.vue | TruckPag API |
| `estornos` | `/api/estornos` | EstornosAuditoria.vue | data_cache (estornos) |
| `sistema` | `/api/sistema` | SistemaLegenda.vue | config.py |

### 3.2 Routers SEM uso direto no frontend

| Router | Prefixo API | Motivo provável | Ação sugerida |
|--------|-------------|-----------------|---------------|
| `combustivel` | `/api/combustivel` | Substituído por `visao_geral` | **REMOVER** |
| `frota` | `/api/frota` | Substituído por `operacional` | **REMOVER** |
| `contratos` | `/api/contratos` | FKM já exibe contratos | **REMOVER** (absorver no FKM) |
| `alertas` | `/api/alertas` | Nenhuma view consome | **AVALIAR** — pode ser útil internamente |
| `veiculos` | `/api/veiculos` | Usado internamente pelo cache | **MANTER** como módulo interno |
| `market` | (se existe) | Dados Brent/câmbio | **AVALIAR** — pode integrar na diretoria |

### 3.3 Views do frontend por seção

| Seção (sidebar) | View | Rota | Status |
|-----------------|------|------|--------|
| **Combustível** | VisaoGeral | `/visao-geral` | OK |
| | DashboardOperacional | `/operacional` | ERRO (import `get_kml_referencia`) |
| | DashboardDiretoria | `/diretoria` | OK (depende benchmark) |
| **Manutenção** | ManutencaoGeral | `/manutencao` | OK |
| | ManutencaoOperacional | `/manutencao/operacional` | A verificar |
| | ManutencaoDiretoria | `/manutencao/diretoria` | A verificar |
| **Pedágios** | PedagiosGeral | `/pedagios` | OK |
| **TCO** | TcoGeral | `/tco` | OK |
| **FKM** | DashboardFKM | `/fkm` | OK |
| **Monitoramento** | GestaoTransacoes | `/transacoes` | OK (depende TruckPag API) |
| | EstornosAuditoria | `/estornos` | OK |
| **Referência** | SistemaLegenda | `/sumario` | ERRO (import `VEICULO_GROUPS`) |

---

## 4. Erros Críticos a Corrigir

### 4.1 `config.py` — Funções/constantes faltantes

| O que falta | Importado em | Impacto |
|-------------|-------------|---------|
| `get_veiculo_group(modelo, marca, placa)` | `data_cache.py:25` | **CRÍTICO** — cache não carrega, TODOS os endpoints falham |
| `get_kml_referencia(grupo, combustivel)` | `operacional.py:13` | **CRÍTICO** — dashboard Operacional não abre |
| `VEICULO_GROUPS` (lista de grupos) | `sistema.py` | **MÉDIO** — página de legendas falha |
| `is_fuel_incompatible(grupo, combustivel)` | `data_cache.py:480` | **MÉDIO** — validação de KML não funciona |

**Ação:** Implementar as 4 funções/constantes em `config.py`.

### 4.2 `utils.py` — Parâmetro com nome errado

| Arquivo | Linha | Problema |
|---------|-------|---------|
| `utils.py:25` | `data_fundo` | Deveria ser `data_inicio`? Verificar uso nos routers |

**Ação:** Auditar todos os chamadores e corrigir o nome do parâmetro.

### 4.3 Imports quebrados em routers

Após corrigir o `config.py`, verificar se todos os routers importam corretamente:
- [ ] `data_cache.py` → `get_veiculo_group`
- [ ] `operacional.py` → `get_kml_referencia`
- [ ] `sistema.py` → `VEICULO_GROUPS`
- [ ] `data_cache.py` → `is_fuel_incompatible`

---

## 5. Consolidação de Routers

### 5.1 Routers a REMOVER

#### `combustivel.py` (substituído por `visao_geral.py`)
- **Endpoints:** `/filtros`, `/kpis`, `/diario`, `/por-tipo`, `/historico-mensal`, `/top-postos`
- **Razão:** `visao_geral.py` cobre tudo isso com endpoints mais completos
- **Checklist:**
  - [ ] Verificar se algum endpoint de `combustivel.py` NÃO existe em `visao_geral.py`
  - [ ] Migrar lógica exclusiva (se houver)
  - [ ] Remover router de `main.py`
  - [ ] Remover arquivo `routers/combustivel.py`
  - [ ] Remover `frontend/src/api/combustivel.js` (se existir e não for usado)

#### `frota.py` (substituído por `operacional.py`)
- **Endpoints:** `/eficiencia-km-litro`, `/custo-por-placa`, `/ranking-motoristas`, `/abastecimentos-suspeitos`, `/custo-mensal-frota`
- **Razão:** `operacional.py` tem endpoints equivalentes e mais completos
- **Checklist:**
  - [ ] Verificar lógica exclusiva de `frota.py`
  - [ ] Migrar se necessário
  - [ ] Remover router de `main.py`
  - [ ] Remover arquivo `routers/frota.py`
  - [ ] Remover `frontend/src/api/frota.js` (se existir)

#### `contratos.py` (absorvido pelo FKM)
- **Endpoints:** `/filtros`, `/kpis`, `/ranking`
- **Razão:** `fkm.py` já tem filtro por contrato e exibe dados por contrato
- **Checklist:**
  - [ ] Verificar se FKM já cobre todos os endpoints
  - [ ] Remover router de `main.py`
  - [ ] Remover arquivo `routers/contratos.py`

### 5.2 Routers a AVALIAR

#### `alertas.py`
- **Situação:** Nenhuma view consome diretamente
- **Possibilidades:**
  - A) Integrar alertas no dashboard Operacional (recomendado)
  - B) Criar view dedicada de alertas
  - C) Remover se não for usado
- **Decisão:** ⬜ Pendente (decidir durante execução)

#### `veiculos.py`
- **Situação:** Usado internamente (enrichment do cache)
- **Ação:** Manter, mas verificar se endpoints HTTP são necessários ou se pode ser apenas módulo interno

### 5.3 Resultado esperado

**De 18 routers → ~13 routers:**

| # | Router | Prefixo | Responsabilidade |
|---|--------|---------|-----------------|
| 1 | `visao_geral` | `/api/visao-geral` | Dashboard principal combustível |
| 2 | `operacional` | `/api/operacional` | Gestão de frota + alertas |
| 3 | `diretoria` | `/api/diretoria` | Visão estratégica |
| 4 | `precos` | `/api/precos` | Rankings e variação de preços |
| 5 | `benchmark` | `/api/benchmark` | Comparativo ANP |
| 6 | `manutencao` | `/api/manutencao` | Custos de manutenção |
| 7 | `pedagios` | `/api/pedagios` | Gestão de pedágios |
| 8 | `tco` | `/api/tco` | Custo total de propriedade |
| 9 | `fkm` | `/api/fkm` | Fechamento mensal (inclui contratos) |
| 10 | `gestao_transacoes` | `/api/gestao-transacoes` | Monitoramento real-time |
| 11 | `estornos` | `/api/estornos` | Auditoria de estornos |
| 12 | `sistema` | `/api/sistema` | Configuração e legendas |
| 13 | `veiculos` | `/api/veiculos` | Cadastro de veículos (interno) |

---

## 6. Corrigir Fontes Existentes

### Princípio fundamental
**Não copiar dados que já existem.** Cada fonte é lida diretamente:

| Fonte | O que contém | Lido por |
|-------|-------------|----------|
| DW `silver.truckpag_analitico_transacao` | Transações TruckPag (combustível + pedágios) | `data_cache.py` |
| SQL Server BlueFleet | Veículos (modelo, marca, filial, ano) + Ordens de Serviço de manutenção | `db_sqlserver.py` |
| Railway PostgreSQL | Dados legados TruckPag (fallback se DW indisponível) | `data_cache.py` |
| Excel FKM `.xlsb` | Fechamento mensal (km, custos, contratos, filiais) | `db_fkm.py` |
| DW `torre.anp_precos` | Preços ANP por produto/UF/município (tabela criada por nós via ETL) | `anp_client.py` |

### 6.1 Problemas identificados nas fontes atuais

#### `data_cache.py` — Mapeamento de colunas DW
- **Status:** ✅ **CORRIGIDO** (2026-04-09)
- **Problema:** DW retorna `transacao_data`, `transacao_valor`, `veiculo_placa`, etc. mas `_normalize_dw_df` não mapeava esses nomes
- **Solução:** Adicionados nomes reais do DW às listas de candidatos em `_normalize_dw_df`

#### `db_sqlserver.py` — Query de manutenção com coluna inválida
- **Status:** ❌ Pendente
- **Problema:** `(207) Invalid column name 'FilialOperacional'` — coluna não existe com esse nome
- **Solução:** Inspecionar schema real do SQL Server e corrigir o nome da coluna

#### `data_cache.py` — Enriquecimento de modelo/marca do veículo
- **Status:** ⚠️ Parcial
- **Problema:** DW `silver` não tem `modelo_veiculo` nem `marca_veiculo` — todos os veículos ficam como grupo "Outros"
- **Solução:** Enriquecer modelo/marca via `get_veiculos_df()` do SQL Server, cruzando pela placa

#### `torre.anp_precos` — Tabela não existe
- **Status:** ❌ Pendente
- **Problema:** ETL ANP (`etl_anp.py`) escreve nessa tabela mas ela ainda não foi criada/populada localmente. Era `silver.anp_precos` — corrigido para `torre.anp_precos` (é dado que nós criamos via scraping ANP)
- **Solução:** Executar `etl_anp.py` uma vez para criar a tabela e carregar os dados

#### `utils.py` — Parâmetro `data_fundo` na posição errada
- **Status:** ❌ Pendente
- **Problema:** Posição 7 é `data_fundo` (não usado no body), mas `pedagios.py` passa `data_fim` nessa posição → filtro de período nunca aplica
- **Solução:** Remover `data_fundo` da assinatura

### 6.2 Checklist
- [x] `data_cache.py`: mapeamento de colunas do DW corrigido
- [ ] `db_sqlserver.py`: corrigir nome da coluna em `get_manutencao_df()`
- [ ] `data_cache.py`: enriquecer `modelo_veiculo` e `marca_veiculo` via SQL Server
- [ ] `etl_anp.py`: executar para criar `torre.anp_precos` no DW local
- [ ] `utils.py`: remover parâmetro `data_fundo`

---

## 7. Escopo do Schema `torre`

### Princípio
O schema `torre` é reservado **exclusivamente** para tabelas que não existem em nenhuma fonte atual e que precisamos criar para novas funcionalidades.

### Exemplos de uso CORRETO do `torre`
- Configurações de alertas personalizados por usuário/frota (thresholds de km/L, limites de gasto)
- Metas de KPIs definidas internamente (ex: meta de km/L por grupo, orçamento mensal por filial)
- Agregações pré-calculadas para TCO histórico (se performance exigir)
- Anotações/comentários sobre transações suspeitas

### O que NÃO vai para `torre`
| Dado | Motivo |
|------|--------|
| Transações TruckPag | Já estão no DW `silver` |
| Veículos | Já estão no SQL Server |
| Manutenção OS | Já estão no SQL Server |
| FKM | Já está no Excel (lido pelo `db_fkm.py`) |
| Preços ANP | Vai para `torre.anp_precos` — é dado gerado por nós via ETL ✅ |

### Checklist
- [ ] Definir quais KPIs/metas precisam de persistência (próximos sprints)
- [ ] Criar tabelas em `torre` conforme novas features forem definidas

---

## 8. Automatização ANP

### 8.1 Estado atual
- `etl_anp.py` é standalone (roda manualmente com `python -m etl_anp`)
- Dados vão para `silver.anp_precos` no DW
- `anp_client.py` lê do DW e cacheia em memória (24h)

### 8.2 Plano
Duas opções:

**Opção A — Scheduler no backend (recomendado):**
- Usar `apscheduler` ou `asyncio` loop para rodar ETL ANP a cada 24h
- Integrar no lifespan do FastAPI (já tem warmup de threads)
- Vantagem: zero dependência externa

**Opção B — Cron job separado:**
- Configurar cron no Railway/servidor
- Vantagem: não consome recursos da API

### 8.3 Checklist
- [ ] Escolher abordagem (A ou B)
- [ ] Se A: adicionar scheduler ao `main.py` lifespan
- [ ] Se B: criar script de cron + documentar
- [ ] Adicionar endpoint `POST /api/sistema/anp/refresh` para trigger manual
- [ ] Testar que benchmark endpoints atualizam corretamente

---

## 9. Plano de Execução por Módulo

### Módulo 1 — Corrigir erros críticos (PRIORIDADE MÁXIMA)
> **Objetivo:** Fazer todos os endpoints funcionarem sem erros de import

**Tarefas:**
1. Implementar `get_veiculo_group(modelo, marca, placa)` em `config.py`
   - Usar `VEICULO_RULES` (regras por substring) + `VEICULO_PLATE_OVERRIDES`
   - Retornar grupo do veículo (Bitruck, Truck, Toco, etc.)

2. Implementar `VEICULO_GROUPS` em `config.py`
   - Lista: `["Bitruck", "Truck", "Toco", "3/4", "Pesado", "Médio", "Leve", "Moto", "Outros"]`

3. Implementar `get_kml_referencia(grupo, combustivel)` em `config.py`
   - Retornar `(meta_kml, alerta_kml)` do dict `KML_REFERENCIA`

4. Implementar `is_fuel_incompatible(grupo, combustivel)` em `config.py`
   - Validar se grupo pesado usa gasolina (incompatível), etc.

5. Auditar e corrigir `data_fundo` em `utils.py`

6. **Testar:** subir o backend e verificar que todos os endpoints respondem

**Arquivos alterados:** `config.py`, `utils.py`
**Risco:** Baixo (adiciona código sem alterar existente)

---

### Módulo 2 — Consolidar routers
> **Objetivo:** Remover routers não utilizados, simplificar a base de código

**Tarefas:**
1. Auditar `combustivel.py` vs `visao_geral.py`:
   - Comparar endpoints lado a lado
   - Migrar lógica exclusiva (se houver)
   - Remover `combustivel.py` de `main.py`

2. Auditar `frota.py` vs `operacional.py`:
   - Mesma comparação
   - Remover `frota.py`

3. Auditar `contratos.py` vs `fkm.py`:
   - Verificar se FKM cobre tudo
   - Remover `contratos.py`

4. Avaliar `alertas.py`:
   - Decidir se integra no Operacional ou remove

5. Limpar imports no `main.py`

6. Limpar arquivos de API no frontend (`combustivel.js`, `frota.js`, etc.)

7. **Testar:** todas as views do frontend continuam funcionando

**Arquivos alterados:** `main.py`, routers removidos, frontend API files
**Risco:** Médio (pode quebrar algo se endpoint for usado em local não mapeado)

---

### Módulo 3 — Corrigir fontes de dados existentes
> **Objetivo:** Todas as fontes lidas corretamente, sem cópia de dados

**Tarefas:**
1. Corrigir `utils.py`: remover parâmetro `data_fundo` da assinatura de `apply_time_filters`

2. Corrigir `db_sqlserver.py`: inspecionar schema real e corrigir nome da coluna em `get_manutencao_df()`
   - Erro atual: `Invalid column name 'FilialOperacional'`

3. Enriquecer modelo/marca via SQL Server em `data_cache.py`:
   - Após `_enrich_filiais`, cruzar placa com `get_veiculos_df()` para preencher `modelo_veiculo` e `marca_veiculo`
   - Isso faz `get_veiculo_group()` classificar corretamente em vez de retornar "Outros"

4. Rodar `etl_anp.py` localmente para criar e popular `silver.anp_precos` no DW
   - Endpoints de benchmark funcionarão após isso

5. **Testar:** todos os dashboards respondendo sem 500

**Arquivos alterados:** `utils.py`, `db_sqlserver.py`, `data_cache.py`
**Risco:** Baixo-médio

---

### Módulo 4 — Consolidar routers (antigo Módulo 2)
> **Objetivo:** Remover routers não utilizados, simplificar a base de código

**Tarefas:**
1. Auditar `combustivel.py` vs `visao_geral.py` — remover redundante
2. Auditar `frota.py` vs `operacional.py` — remover redundante
3. Auditar `contratos.py` vs `fkm.py` — remover redundante
4. Avaliar `alertas.py` — integrar no Operacional ou remover
5. Limpar imports no `main.py`
6. Limpar arquivos de API no frontend (`combustivel.js`, `frota.js`, etc.)
7. **Testar:** todas as views do frontend continuam funcionando

**Arquivos alterados:** `main.py`, routers removidos, frontend API files
**Risco:** Médio (verificar que nenhum endpoint removido é consumido)

---

### Módulo 5 — Automatizar ANP + limpeza final
> **Objetivo:** ANP atualiza sozinha, sistema limpo e estável

**Tarefas:**
1. Integrar ETL ANP no scheduler do backend (apscheduler ou asyncio)
2. Criar endpoint `POST /api/sistema/anp/refresh` para trigger manual
3. Revisar `data_cache.py` — simplificar fluxo, remover fallbacks legados se DW estável
4. Revisar `main.py` — lifespan/warmup atualizado
5. **Testar:** ciclo completo de todos os dashboards end-to-end
6. Atualizar MEMORY.md

**Arquivos alterados:** `main.py`, `etl_anp.py`, `data_cache.py`
**Risco:** Baixo

---

## 10. Checklist Final

### Pré-execução
- [ ] Backup do banco DW (schema torre)
- [ ] Branch `refatoracao/limpeza-endpoints` criada
- [ ] `.env` com todas as credenciais configuradas localmente

### Módulo 1 — Erros críticos
- [ ] `get_veiculo_group()` implementada em `config.py`
- [ ] `VEICULO_GROUPS` definida em `config.py`
- [ ] `get_kml_referencia()` implementada em `config.py`
- [ ] `is_fuel_incompatible()` implementada em `config.py`
- [ ] `utils.py` parâmetro corrigido
- [ ] Backend sobe sem erros de import
- [ ] Todos os endpoints respondem (podem retornar vazio, mas não 500)

### Módulo 2 — Consolidação
- [ ] `combustivel.py` removido (lógica migrada se necessário)
- [ ] `frota.py` removido (lógica migrada se necessário)
- [ ] `contratos.py` removido (absorvido pelo FKM)
- [ ] `alertas.py` decidido (integrar ou remover)
- [ ] `main.py` atualizado
- [ ] Frontend limpo (APIs não usadas removidas)
- [ ] Todas as 12 views funcionando

### Módulo 3 — FKM → DW
- [ ] Tabela `torre.fkm_fechamento` criada
- [ ] `etl_fkm.py` criado e testado
- [ ] Primeira carga executada com sucesso
- [ ] `db_fkm.py` lendo do DW
- [ ] `DashboardFKM.vue` funcionando com dados do banco
- [ ] Dados validados contra Excel original

### Módulo 4 — SQL Server → DW
- [ ] Tabela `torre.veiculos` criada
- [ ] Tabela `torre.manutencao_os` criada
- [ ] `etl_sqlserver.py` criado e testado
- [ ] Primeira carga executada
- [ ] `db_sqlserver.py` lendo do DW
- [ ] Enrichment de filiais funcionando via DW
- [ ] Dashboards de manutenção, TCO e veículos funcionando

### Módulo 5 — ANP + limpeza
- [ ] ETL ANP automatizado
- [ ] Endpoint de refresh manual disponível
- [ ] `data_cache.py` fluxo simplificado
- [ ] Todos os dashboards testados end-to-end
- [ ] Documentação atualizada

---

## Apêndice A — Diagrama de Fluxo de Dados (Futuro)

```
┌─────────────────────────────────────────────────────────────┐
│                    FONTES ORIGINAIS                          │
├──────────────┬──────────────┬─────────────┬────────────────┤
│ Railway PG   │ SQL Server   │ Excel FKM   │ ANP (web)      │
│ (transações) │ (veíc+manut) │ (.xlsb)     │ (preços)       │
└──────┬───────┴──────┬───────┴──────┬──────┴───────┬────────┘
       │              │              │              │
       │         ETL periódico  ETL manual     ETL 24h
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DW PostgreSQL                             │
├──────────────────┬──────────────────────────────────────────┤
│ silver.          │ torre.                                    │
│  truckpag_*      │  veiculos                                │
│  anp_precos      │  manutencao_os                           │
│                  │  fkm_fechamento                          │
└────────┬─────────┴────────┬─────────────────────────────────┘
         │                  │
         ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              data_cache.py (pandas, TTL 30min)               │
│  transacoes │ pedagios │ estornos │ veiculos │ fkm │ anp    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI (13 routers)                             │
│  visao_geral │ operacional │ diretoria │ precos │ benchmark │
│  manutencao  │ pedagios    │ tco       │ fkm    │ estornos  │
│  gestao_transacoes │ sistema │ veiculos                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Vue 3 Frontend (12 views)                       │
└─────────────────────────────────────────────────────────────┘
```

## Apêndice B — Variáveis de Ambiente Necessárias

```env
# Railway PostgreSQL (abastecimentos)
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname

# DW PostgreSQL (transações RT + schema torre)
DW_HOST=192.168.0.37
DW_PORT=5433
DW_NAME=dw
DW_USER=...
DW_PASSWORD=...

# SQL Server BlueFleet (fonte para ETL)
SQLSERVER_HOST=...
SQLSERVER_PORT=1433
SQLSERVER_DB=...
SQLSERVER_USER=...
SQLSERVER_PASSWORD=...

# FKM Excel (fonte para ETL)
FKM_FILE_PATH=../documentacao API - Truckpag/Evolucao FKM 2026.xlsb

# APIs externas
TRUCKPAG_URL=prd.truckpag.com.br
TRUCKPAG_TOKEN=...
EIA_API_KEY=...

# App
CORS_ORIGINS=*
CACHE_TTL_MINUTES=30
```
