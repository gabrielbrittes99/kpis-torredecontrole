# Auditoria de Dados — Torre de Controle Gritsch
**Gerado em:** 17/03/2026
**Objetivo:** Mapear de onde vêm TODOS os dados exibidos no sistema para validação.

---

## 1. FONTE PRIMÁRIA DOS DADOS

### Tabela principal: `integration_truckpag_transacoes` (PostgreSQL Railway)

| Campo | Tipo | O que é |
|---|---|---|
| `data_transacao` | timestamp | Data/hora do abastecimento |
| `valor` | decimal | Valor pago em R$ |
| `litragem` | decimal | Litros abastecidos |
| `nome_combustivel` | text | Nome bruto do combustível (ex: "Diesel S10") |
| `placa` | text | Placa do veículo |
| `hodometro` | decimal | Leitura do hodômetro no momento |
| `modelo_veiculo` | text | Modelo (ex: "SPRINTER 417") |
| `marca_veiculo` | text | Marca (ex: "M. BENZ") |
| `motorista` | text | Nome do motorista |
| `razao_social_posto` | text | Nome jurídico do posto |
| `nome_fantasia_posto` | text | Nome de exibição/marca do posto (ex: "GP POSTOS") |
| `cidade_posto` | text | Cidade do posto |
| `uf_posto` | text | UF do posto |
| `transacao_estornada` | text | "0" = válido, qualquer outro valor = estornado |

**Estatísticas atuais:**
- Total de registros: **116.973**
- Abastecimentos válidos: **37.563** (litragem > 0 AND transacao_estornada = '0')
- Estornados: 1.545
- Sem litragem (serviços, taxas): 79.036
- Período: **21/06/2025 a 17/03/2026**
- Placas únicas: 561
- Postos únicos (razao_social): 979
- Tipos de combustível: 9

---

## 2. FILTRO BASE DO CACHE (aplicado a TUDO)

**Arquivo:** `backend/data_cache.py`

```sql
SELECT ... FROM integration_truckpag_transacoes
WHERE litragem > 0
  AND transacao_estornada = '0'
ORDER BY data_transacao
```

**⚠️ IMPORTANTE:** Este filtro é aplicado antes de qualquer cálculo.
Registros com `litragem = 0` (serviços, taxas de cartão, Arla avulso) são **excluídos** de todo o sistema.

### Transformações aplicadas no cache:

1. **`grupo_combustivel`** — calculado a partir de `nome_combustivel`:
   - "Diesel S10", "Diesel Aditivado", "Biodiesel" etc → `"Diesel"`
   - "Gasolina Comum", "Gasolina Aditivada" etc → `"Gasolina"`
   - "Alcool Comum", "Etanol Hidratado" etc → `"Álcool"`
   - "Arla 32" → `"Arla"`
   - Qualquer outro → `"Outros"` *(corrigido: não aparece mais no dashboard)*

2. **`grupo_veiculo`** — calculado a partir de `modelo_veiculo` + `marca_veiculo` via regras em `config.py`:
   - Sprinter, Master, etc → `"Pesado"`
   - Saveiro, Fiorino, Strada → `"Médio"`
   - Gol, Polo, 208 → `"Leve"`
   - Caminhões por porte: `"Caminhão4.2Ton"` a `"Caminhão17Ton"`

3. **`filial_nome` / `filial_estado` / `filial_regiao`** — atribuído por:
   - Enriquecimento via BlueFleet (SQL Server) quando disponível
   - Hardcoded por placa para Palmas e Curitiba Base (ver Seção 5)

4. **`km_percorrido`** — calculado como `DIFF(hodometro)` entre abastecimentos consecutivos da mesma placa. Aceita apenas valores entre 1 e 2.000 km (para evitar outliers).

---

## 3. PLACAS EXCLUÍDAS / SOBRESCRITAS

### 3.1 Placas Ignoradas (excluídas de TODO o sistema)
```
TBI2068
```
*(Razão: placa problemática — provavelmente não é veículo da frota)*

### 3.2 Placas com Filial Hardcoded
**Filial Palmas (TO — Região Norte):**
```
RHS8D34, SDR4D98, SDR8E04, SDR8E58, SDX2J14,
SEN1C55, SEN1C56, SFL1E46, UAV5J75
```

**Filial Curitiba Base (PR — Região Sul):**
```
TBU9D20
```

### 3.3 Placas com Combustível Forçado
Estas placas têm `grupo_combustivel = "Diesel"` independente do que registraram:
```
BCQ7B53, BCQ7B55, SDP5J32, RHE2E95, BAJ7269
```

### 3.4 Placas com Grupo de Veículo Forçado
```
SEN1C55 → "Leve"
```

---

## 4. POSTOS — PROBLEMA IDENTIFICADO E CORRIGIDO

### ⚠️ Bug Encontrado: Nome Errado nos Rankings

O sistema usava `razao_social_posto` (nome jurídico) para exibição e agrupamento.
O usuário conhece os postos pelo `nome_fantasia_posto`.

**Exemplo crítico — o posto mais utilizado da frota:**

| Campo | Valor |
|---|---|
| `razao_social_posto` | COMERCIO DE COMBUSTIVEIS PASTORELLO S.A |
| `nome_fantasia_posto` | **GP POSTOS - POSTO SAO JOSE** |
| `cidade_posto` | SAO JOSE DOS PINHAIS (PR) |
| Volume total | **335.719 litros** |
| Valor total | **R$ 1.906.372** |
| Abastecimentos | 1.629 |

**Este posto é o #1 em tudo** (volume, custo total) e não aparecia com o nome correto.
**Corrigido:** agora usa `nome_fantasia_posto` quando disponível.

### Top 15 Postos por Volume (dados corretos pós-correção):

| # | Nome Exibição | Cidade | UF | Litros | Valor |
|---|---|---|---|---|---|
| 1 | GP POSTOS - POSTO SAO JOSE | São José dos Pinhais | PR | 335.719 | R$ 1.906.372 |
| 2 | AUTO POSTO PRA FRENTE BRASIL 1 | Cascavel | PR | 123.224 | R$ 736.252 |
| 3 | POSTO 10 GOIANIA \| REDE CARRETEIRO | Goiânia | GO | 83.441 | R$ 517.945 |
| 4 | CHAPECO - FILIAL 17 - REDE TRADICAO | Chapecó | SC | 80.539 | R$ 485.494 |
| 5 | POSTO CAPITAL | Curitibanos | SC | 79.036 | R$ 465.461 |
| 6 | POSTO ZANDONA 12 | Blumenau | SC | 77.194 | R$ 462.744 |
| 7 | POSTO UNIDO | Maringá | PR | 54.595 | R$ 322.744 |
| 8 | REDE DINO - POSTO TREVINHO | Várzea Grande | MT | 53.309 | R$ 295.785 |
| 9 | POSTO VIADUTO | Palhoça | SC | 50.657 | R$ 302.347 |
| 10 | POSTO BARAO MATRIZ | São José dos Pinhais | PR | 47.039 | R$ 280.945 |

---

## 5. O QUE CADA ENDPOINT FAZ E DE ONDE VEM

### 5.1 Visão Geral (`/api/visao-geral/dashboard`)

| Dado exibido | Origem | Filtros aplicados |
|---|---|---|
| **Gasto Total / Volume / Preço Médio / Abastecimentos** | Soma direta do cache filtrado | Período + filial + grupo + combustível |
| **Gráfico Mensal 12m** | Agrupa cache por mês (últimos 12) | Filtros de atributo (grupo, filial, combustível) — **sem filtro de período** |
| **Gráfico Semanal 8s** | Agrupa cache por semana (últimas 8) | Idem |
| **Gráfico Diário 30d** | Agrupa cache por dia (últimos 30) | Idem |
| **Por Combustível** | `groupby(grupo_combustivel)` no período | Período + demais filtros |
| **Por Grupo de Veículo** | `groupby(grupo_veiculo)` no período | Período + demais filtros. **Exclui "Outros"** |
| **km/L e Custo/km** | Calculado sobre `kml_df` (hodômetro) | Mesmo período. Só placas com hodômetro válido |
| **Gasto por Filial** | `groupby(filial_nome)` no período | Período + demais filtros |
| **Preço médio por UF** | Endpoint separado `/api/precos/preco-por-uf` | Só combustível (sem filtro de período!) |

**⚠️ Atenção:** O gráfico de "Preço médio por estado" sempre mostra dados **históricos completos** (não respeita o período selecionado). O filtro de combustível funciona.

---

### 5.2 Visão Operacional (`/api/operacional/`)

#### `/kpis`
| Dado | Origem | Observação |
|---|---|---|
| Gasto Total | `SUM(valor)` no período filtrado | |
| Custo/KM | `SUM(valor) / SUM(km_percorrido)` | Só registros com hodômetro |
| km/L | `SUM(km_percorrido) / SUM(litragem)` | Só registros com hodômetro |
| Preço Médio/L | `SUM(valor) / SUM(litragem)` | |

**Filtro família:** converte `familia=diesel` para `grupo_combustivel IN ('Diesel')`.
Atenção: `familia=etanol` → `grupo_combustivel IN ('Álcool')`.

#### `/custo-por-grupo`
- Agrupa por `grupo_veiculo`
- `custo_km` = total_valor / total_km (hodômetro)
- `kml_referencia` = valor esperado de config.py por grupo/combustível
- `pct_vs_referencia` = (km_litro - kml_ref) / kml_ref × 100

**⚠️ Atenção:** `pct_vs_referencia` positivo = **acima da referência** (eficiência BOA). Negativo = abaixo.
Porém o badge no frontend: verde = positivo (ok), vermelho = negativo. Validar se a lógica está invertida.

#### `/custo-por-filial`
- Agrupa por `filial_nome`
- Calcula `custo_km` e `km_litro` por filial
- Inclui breakdown de composição de grupos de veículos
- **Filiais sem nome** (`filial_nome = ""`) são excluídas — representam placas sem identificação de filial no BlueFleet

#### `/ranking-postos-preco` ⚠️ CORRIGIDO
- **Antes:** agrupava e exibia por `razao_social_posto` → GP Postos aparecia como "PASTORELLO"
- **Depois:** usa `nome_fantasia_posto` quando disponível
- Mínimo 3 abastecimentos para entrar no ranking
- **Não aplica filtro de período** — mostra dados históricos completos
- `ordem=maior_volume` → ordena por `total_litros`
- `ordem=maior_custo` → ordena por `total_valor`
- `ordem=mais_caro` / `mais_barato` → ordena por `preco_medio`

#### `/variacao-mensal`
- Calcula `preco_medio = SUM(valor)/SUM(litragem)` por `(grupo_combustivel, ano_mes)`
- `variacao_pct` = variação percentual vs mês anterior para o mesmo combustível
- Retorna todos os meses disponíveis no cache filtrado

#### `/veiculos-acao`
- Compara cada placa com a **média do seu grupo de veículo**
- Critérios de alerta:
  - `CRITICO` = custo_km > média_grupo + 2 desvios padrão
  - `ALTO_CUSTO` = custo_km > média_grupo × 1,15 (15% acima)
  - `BAIXO_RENDIMENTO` = km_litro < referência × 0,80 (abaixo de 80% do esperado)
- Só inclui placas com hodômetro registrado (km calculável)
- Retorna `placa`, `modelo`, `grupo`, `filial`, `custo_km`, `media_grupo_custo_km`, `economia_possivel`

---

### 5.3 Inteligência de Preços (`/api/precos/`)

#### `/evolucao-por-tipo`
- `preco_medio` por `(grupo_combustivel, ano_mes)` — **histórico completo, sem filtro de período**
- Retorna série temporal por combustível

#### `/preco-por-uf`
- `preco_medio = SUM(valor)/SUM(litragem)` por `(uf_posto)`
- **Sem filtro de período** — histórico completo
- Aceita filtro de `combustivel`

#### `/analise-premium`
- Compara combustíveis "premium" (aditivados) vs comuns
- Calcula `gasto_extra` = diferença de preço × litros comprados de premium

#### `/variacao-mensal`
- Idem ao do operacional (mesmo endpoint, mesmo dado)

---

## 6. FILTROS GLOBAIS — O QUE FUNCIONA E O QUE NÃO FUNCIONA

| Filtro | Visão Geral | Operacional | Preços |
|---|---|---|---|
| **Período (mês/ano)** | ✅ Dashboard, ⚠️ Gráficos históricos não filtram | ✅ | ❌ Ranking/UF ignoram |
| **Filial** | ✅ | ✅ | ❌ Não implementado |
| **Estado** | ✅ | ✅ | ❌ Não implementado |
| **Região** | ✅ | ✅ | ❌ Não implementado |
| **Grupo de Veículo** | ✅ | ✅ | ❌ Não implementado |
| **Combustível** | ✅ | ✅ (via família) | ✅ Parcial |

**⚠️ Bug conhecido:** O frontend envia o parâmetro como `modoTempo` mas o backend espera `modo_tempo`. O filtro de modo temporal (bimestre, semestre, personalizado) **não funciona corretamente** — sempre usa o mês atual como padrão.

---

## 7. CÁLCULO DE KM/L E CUSTO/KM — COMO FUNCIONA

```
1. Ordena abastecimentos por placa + data
2. km_percorrido = hodometro_atual - hodometro_anterior (mesma placa)
3. Aceita apenas: 1 km < km_percorrido < 2.000 km
4. km/L = km_percorrido / litragem (do abastecimento anterior)
5. custo/km = valor / km_percorrido
```

**Limitações:**
- Se o hodômetro não for registrado no abastecimento → sem km/L
- Se houver dois abastecimentos no mesmo dia → pode gerar km negativo (descartado)
- Não valida se o hodômetro foi digitado errado (só exclui > 2.000 km entre abastecimentos)

**Placas sem hodômetro:** aparecem no sistema mas sem km/L e custo/km.
Hoje: nem todas as placas registram hodômetro — verifique com o motorista/operador.

---

## 8. FILIAIS — COMO SÃO IDENTIFICADAS

### Fonte primária: BlueFleet (SQL Server)
- O sistema tenta buscar a filial de cada placa no SQL Server da Gritsch
- Se a conexão falhar ou a placa não estiver cadastrada → `filial_nome = ""`

### Fallback hardcoded (config.py):
- 9 placas → **Gritsch Palmas (TO)**
- 1 placa → **Gritsch Curitiba (PR)**

### Placas sem filial:
Aparecem no alerta "Sem filial identificada" na Visão Geral.
**Causa:** Não estão cadastradas no BlueFleet ou o SQL Server não respondeu.

---

## 9. PONTOS DE ATENÇÃO PARA VALIDAÇÃO

| # | Item | Risco |
|---|---|---|
| 1 | **Placa TBI2068** | É excluída de TODO o sistema. Confirmar se deve ser ignorada |
| 2 | **5 placas com combustível forçado para Diesel** | BCQ7B53, BCQ7B55, SDP5J32, RHE2E95, BAJ7269 — confirmar |
| 3 | **SEN1C55 → grupo "Leve"** | Forçado manualmente. Confirmar se está correto |
| 4 | **Hodômetro não obrigatório** | km/L calculado apenas para placas que registram — parte da frota sem métrica de eficiência |
| 5 | **Filtro de período não funciona em Preços** | Rankings de postos sempre mostram histórico completo |
| 6 | **modoTempo não passa corretamente** | Bimestre/Semestre/Personalizado podem não filtrar corretamente |
| 7 | **Filiais sem BlueFleet** | Muitas placas sem filial identificada — depende da conexão SQL Server |
| 8 | **`nome_fantasia_posto` vazio em alguns postos** | Neste caso usa razao_social (nome jurídico) |
