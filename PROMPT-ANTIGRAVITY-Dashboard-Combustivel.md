# PROMPT — Dashboard de Combustível · Gritsch / TruckPag

## CONTEXTO DO PROJETO

Você é um especialista em desenvolvimento de dashboards analíticos. Preciso que crie um **dashboard completo de análise de combustível** para uma empresa de transporte chamada **Gritsch**, consumindo dados reais de uma tabela de banco de dados chamada `integration_truckpag_transacoes`.

A imagem de referência visual foi fornecida junto com este prompt — use-a como guia fiel de layout, cores e organização dos elementos.

---

## ESTRUTURA DA TABELA (banco de dados)

Tabela principal: `integration_truckpag_transacoes`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INT | Identificador único |
| `transacao` | VARCHAR | Código da transação |
| `data_transacao` | DATETIME | Data e hora do abastecimento |
| `hodometro` | INT | Hodômetro do veículo |
| `valor` | DECIMAL | Valor total em R$ |
| `litragem` | DECIMAL | Quantidade de litros |
| `cod_combustivel` | VARCHAR | Código do combustível |
| `nome_combustivel` | VARCHAR | Nome (ex: Diesel S10, Diesel Comum, Arla) |
| `servico` | VARCHAR | Tipo de serviço |
| `tipo_abastecimento` | VARCHAR | Tipo de abastecimento |
| `codigo_tanque` | VARCHAR | Código do tanque |
| `nome_tanque` | VARCHAR | Nome do tanque |
| `codigo_bomba` | VARCHAR | Código da bomba |
| `nome_bomba` | VARCHAR | Nome da bomba |
| `razao_social_posto` | VARCHAR | Razão social do posto |
| `nome_fantasia_posto` | VARCHAR | Nome fantasia do posto |
| `cnpj_posto` | VARCHAR | CNPJ do posto |
| `cidade_posto` | VARCHAR | Cidade do posto |
| `uf_posto` | VARCHAR | Estado do posto |
| `cartao_mascarado` | VARCHAR | Número do cartão (mascarado) |
| `motorista` | VARCHAR | Nome do motorista |
| `matricula_motorista` | VARCHAR | Matrícula do motorista |
| `cpf_motorista` | VARCHAR | CPF do motorista |
| `placa` | VARCHAR | Placa do veículo |
| `modelo_veiculo` | VARCHAR | Modelo do veículo |
| `ano_veiculo` | VARCHAR | Ano do veículo |
| `matricula_veiculo` | VARCHAR | Matrícula do veículo |
| `marca_veiculo` | VARCHAR | Marca do veículo |
| `cor_veiculo` | VARCHAR | Cor do veículo |
| `transacao_estornada` | VARCHAR | Se a transação foi estornada |
| `cnpj_cliente` | VARCHAR | CNPJ do cliente |
| `created_at` | DATETIME | Data de criação do registro |
| `IdVeiculo` | INT | ID do veículo (FK) |

> **Regra importante:** Considerar apenas registros onde `litragem > 0` para análises de combustível. Excluir transações estornadas (`transacao_estornada != 'S'`).

---

## LÓGICA DE NEGÓCIO — MÉTRICAS OBRIGATÓRIAS

### Grupo 1 — KPIs Gerais (cards no topo)

```sql
-- Total Valor (R$)
SELECT SUM(valor) FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'

-- Total Litros
SELECT SUM(litragem) FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'

-- Preço Médio por Litro
SELECT SUM(valor) / NULLIF(SUM(litragem), 0)
FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'

-- Qtd Abastecimentos
SELECT COUNT(*) FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'
```

### Grupo 2 — Mês Atual (usar o último mês com dados)

```sql
-- Identificar o último mês com dados
WITH ultimo_mes AS (
  SELECT MAX(data_transacao) as ultima_data FROM integration_truckpag_transacoes
),
ref AS (
  SELECT
    MONTH(ultima_data) as mes_ref,
    YEAR(ultima_data) as ano_ref,
    DAY(LAST_DAY(ultima_data)) as total_dias_mes
  FROM ultimo_mes
)

-- Valor realizado no mês atual (até o último dia com dados)
SELECT SUM(t.valor)
FROM integration_truckpag_transacoes t, ref r
WHERE litragem > 0
  AND transacao_estornada != 'S'
  AND MONTH(t.data_transacao) = r.mes_ref
  AND YEAR(t.data_transacao) = r.ano_ref

-- Litros realizados no mês atual
SELECT SUM(t.litragem)
FROM integration_truckpag_transacoes t, ref r
WHERE litragem > 0
  AND transacao_estornada != 'S'
  AND MONTH(t.data_transacao) = r.mes_ref
  AND YEAR(t.data_transacao) = r.ano_ref

-- Dias com dados no mês atual
SELECT COUNT(DISTINCT DATE(data_transacao))
FROM integration_truckpag_transacoes t, ref r
WHERE litragem > 0
  AND MONTH(t.data_transacao) = r.mes_ref
  AND YEAR(t.data_transacao) = r.ano_ref
```

### Grupo 3 — Mês Anterior

```sql
-- Mês anterior ao último mês com dados
WITH ultimo_mes AS (
  SELECT MAX(data_transacao) as ultima_data FROM integration_truckpag_transacoes
),
ref AS (
  SELECT
    MONTH(DATE_SUB(ultima_data, INTERVAL 1 MONTH)) as mes_ant,
    YEAR(DATE_SUB(ultima_data, INTERVAL 1 MONTH)) as ano_ant
  FROM ultimo_mes
)

SELECT SUM(t.valor) as valor_mes_anterior, SUM(t.litragem) as litros_mes_anterior
FROM integration_truckpag_transacoes t, ref r
WHERE t.litragem > 0
  AND t.transacao_estornada != 'S'
  AND MONTH(t.data_transacao) = r.mes_ant
  AND YEAR(t.data_transacao) = r.ano_ant
```

### Grupo 4 — Projeção de Fechamento do Mês

```
Lógica:
  media_diaria = valor_mes_atual / dias_com_dados
  projecao_valor = media_diaria * total_dias_mes
  projecao_litros = (litros_mes_atual / dias_com_dados) * total_dias_mes
  variacao_valor = projecao_valor - valor_mes_anterior
  variacao_pct = (projecao_valor - valor_mes_anterior) / valor_mes_anterior
  status = SE variacao_pct > 2% → "🔺 ALTA"
           SE variacao_pct < -2% → "🔻 BAIXA"
           SENÃO → "➡️ ESTÁVEL"
  progresso_mes_pct = dias_com_dados / total_dias_mes
```

### Grupo 5 — Série Temporal (gráfico diário)

```sql
SELECT
  DATE(data_transacao) as dia,
  SUM(valor) as total_valor,
  SUM(litragem) as total_litros,
  COUNT(*) as qtd_abastecimentos
FROM integration_truckpag_transacoes
WHERE litragem > 0
  AND transacao_estornada != 'S'
  AND MONTH(data_transacao) = [mes_ref]
  AND YEAR(data_transacao) = [ano_ref]
GROUP BY DATE(data_transacao)
ORDER BY dia
```

### Grupo 6 — Distribuição por Tipo de Combustível

```sql
SELECT
  nome_combustivel,
  SUM(valor) as total_valor,
  SUM(litragem) as total_litros,
  COUNT(*) as qtd,
  ROUND(SUM(litragem) / (SELECT SUM(litragem) FROM integration_truckpag_transacoes WHERE litragem > 0) * 100, 1) as pct_litros
FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'
GROUP BY nome_combustivel
ORDER BY total_litros DESC
```

### Grupo 7 — Preço Médio por Litro Mensal (histórico)

```sql
SELECT
  DATE_FORMAT(data_transacao, '%Y-%m') as ano_mes,
  SUM(valor) / NULLIF(SUM(litragem), 0) as preco_medio_litro,
  SUM(valor) as total_valor,
  SUM(litragem) as total_litros
FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'
GROUP BY DATE_FORMAT(data_transacao, '%Y-%m')
ORDER BY ano_mes
```

### Grupo 8 — Top Postos

```sql
SELECT
  razao_social_posto,
  cidade_posto,
  uf_posto,
  SUM(valor) as total_valor,
  SUM(litragem) as total_litros,
  SUM(valor) / NULLIF(SUM(litragem), 0) as preco_medio,
  COUNT(*) as qtd_abastecimentos
FROM integration_truckpag_transacoes
WHERE litragem > 0 AND transacao_estornada != 'S'
GROUP BY razao_social_posto, cidade_posto, uf_posto
ORDER BY total_valor DESC
LIMIT 10
```

---

## LAYOUT E COMPONENTES DO DASHBOARD

### Estrutura da Página (de cima para baixo)

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: "⛽ Combustível — Visão Gerencial"  [mês/ano badge] │
│  Filtros: [Filial] [Tipo Combustível] [Período] [Placa]     │
├─────────────────────────────────────────────────────────────┤
│  [KPI 1: Total R$] [KPI 2: Litros] [KPI 3: R$/L] [KPI 4: Qtd] │
│  cada card com: valor principal + variação vs mês anterior  │
├────────────────────────┬────────────────┬───────────────────┤
│  Gráfico Barras Diário │ Rosca Tipo     │ Linha Preço/L     │
│  (valor por dia do mês)│ Combustível    │ Histórico Mensal  │
├────────────────────────┴────────────────┴───────────────────┤
│  SEÇÃO PROJEÇÃO:                                            │
│  [Realizado] [Projeção Final] [Gauge Progresso] [Status 🔺] │
├─────────────────────────────────────────────────────────────┤
│  Tabela: Top 10 Postos (nome, cidade, valor, litros, R$/L)  │
└─────────────────────────────────────────────────────────────┘
```

### Detalhamento dos Componentes

**1. Cards KPI (4 cards em linha)**
- Borda esquerda colorida (laranja, azul, verde, vermelho respectivamente)
- Valor principal grande e em negrito
- Rótulo em maiúsculas pequeno acima
- Badge de variação abaixo: verde se positivo (custo caiu), vermelho se positivo (custo subiu)
  - Atenção: para R$ e Litros, aumento = ruim (vermelho). Para Preço/L, aumento = ruim (vermelho).
- Hover com elevação suave

**2. Gráfico de Barras — Gasto Diário**
- Eixo X: dias do mês
- Eixo Y: valor em R$
- Barras com cor azul, destaque laranja no dia de maior gasto
- Tooltip mostrando: data, valor, litros, qtd abastecimentos

**3. Gráfico de Rosca — Por Tipo de Combustível**
- Mostrar nome + percentual de litros
- Legenda lateral com: nome, litros totais, valor total
- Cores: azul para Diesel S10, laranja para Diesel Comum, verde para Arla

**4. Gráfico de Linha — Preço Médio/L Histórico**
- Eixo X: meses (formato Mmm/AA)
- Eixo Y: R$/litro
- Linha suave (curva), ponto destacado no último mês
- Cor verde, com área preenchida com gradiente sutil

**5. Seção de Projeção**
- Card "Realizado": valor acumulado no mês, com subtítulo "até dia XX"
- Card "Projeção Final": valor projetado até fim do mês, em laranja
- Barra de progresso: % do mês concluído (dias com dados / total de dias)
- Card "Status": ícone grande (🔺🔻➡️) + texto ALTA/BAIXA/ESTÁVEL + diferença em R$

**6. Tabela Top 10 Postos**
- Colunas: Posto, Cidade/UF, Total R$, Total Litros, R$/L médio, Qtd
- Ordenada por valor total decrescente
- Linhas com hover highlight
- Barra visual de tamanho proporcional ao valor na coluna Total R$

---

## ESPECIFICAÇÕES VISUAIS (baseadas na imagem de referência)

### Paleta de Cores
```css
--bg: #0b0e14;              /* fundo principal escuro */
--surface: #131720;          /* cards */
--surface2: #1a2030;         /* cards internos */
--border: #232b3e;           /* bordas */
--accent-orange: #f5a623;    /* cor principal / destaques */
--accent-green: #3ecf8e;     /* positivo / ok */
--accent-blue: #4a9eff;      /* informativo */
--accent-red: #ff5757;       /* negativo / alerta */
--text: #e8eaf0;             /* texto principal */
--muted: #6b7a99;            /* texto secundário */
```

### Tipografia
- Display/títulos: `Syne` (Google Fonts) — peso 700/800
- Mono/labels: `IBM Plex Mono` (Google Fonts) — peso 400/500
- Tamanhos: KPI principal 24-28px, labels 10-11px uppercase

### Animações
- Cards com fade-in escalonado no carregamento (animation-delay: 0.1s, 0.2s, etc.)
- Hover nos cards: `transform: translateY(-2px)` + transição de border-color
- Barras do gráfico diário com animação de crescimento
- Barra de progresso com fill animado

---

## STACK TÉCNICA RECOMENDADA

**Opção A — React + Recharts (preferencial)**
```
- React com hooks (useState, useEffect, useMemo)
- Recharts para todos os gráficos (BarChart, LineChart, PieChart)
- Tailwind CSS para layout base
- Fetch API para consumir backend
- Fontes via Google Fonts CDN
```

**Opção B — HTML/CSS/JS puro**
```
- Vanilla JS com fetch API
- Chart.js para gráficos
- CSS custom properties para tema
- Animações CSS puras
```

---

## INTEGRAÇÃO COM BACKEND

O componente deve consumir dados via API REST. Estrutura esperada dos endpoints:

```
GET /api/combustivel/kpis
→ { total_valor, total_litros, preco_medio, qtd_abastecimentos,
    valor_mes_atual, litros_mes_atual, valor_mes_anterior, litros_mes_anterior,
    dias_com_dados, total_dias_mes, mes_ref, ano_ref,
    projecao_valor, projecao_litros, variacao_valor, variacao_pct, status }

GET /api/combustivel/diario?mes=2&ano=2026
→ [{ dia, total_valor, total_litros, qtd_abastecimentos }]

GET /api/combustivel/por-tipo
→ [{ nome_combustivel, total_valor, total_litros, qtd, pct_litros }]

GET /api/combustivel/historico-mensal
→ [{ ano_mes, preco_medio_litro, total_valor, total_litros }]

GET /api/combustivel/top-postos?limit=10
→ [{ razao_social_posto, cidade_posto, uf_posto, total_valor, total_litros, preco_medio, qtd_abastecimentos }]
```

Se não houver backend ainda, popule com dados mockados realistas para demonstração, usando estes valores reais do banco como referência:
- Total histórico: R$ 11.537.593 | 1.950.149 litros | 33.549 abastecimentos
- Preço médio: R$ 5,92/litro
- Fev/2026 (último mês): R$ 1.140.159 | 193.462 litros | 22 dias com dados de 28
- Jan/2026 (mês anterior): R$ 1.771.062 | 299.130 litros
- Projeção Fev/2026: R$ 1.451.112 | Status: 🔻 BAIXA (-18,1%)

---

## FILTROS INTERATIVOS

Implementar filtros que refiltram todos os gráficos simultaneamente:

1. **Período**: seletor de mês/ano (padrão: último mês com dados)
2. **Tipo de combustível**: multiselect (Diesel S10, Diesel Comum, Arla, etc.)
3. **Filial/Empresa**: dropdown (quando existir tabela de filiais relacionada via `cnpj_cliente`)
4. **Placa do veículo**: busca/autocomplete

Ao alterar qualquer filtro, todos os gráficos e KPIs devem atualizar.

---

## REQUISITOS FUNCIONAIS OBRIGATÓRIOS

- [ ] 4 cards KPI na linha superior com variação vs mês anterior
- [ ] Gráfico de barras diário do mês selecionado
- [ ] Gráfico de rosca por tipo de combustível
- [ ] Gráfico de linha do preço médio histórico por mês
- [ ] Seção de projeção com: realizado, projeção, barra progresso, status (ALTA/BAIXA/ESTÁVEL)
- [ ] Tabela top 10 postos com barra visual proporcional
- [ ] Filtros funcionais (período mínimo)
- [ ] Loading state nos componentes
- [ ] Tema escuro conforme paleta especificada
- [ ] Responsivo para telas 1280px+
- [ ] Tooltips nos gráficos com informações completas

---

## REFERÊNCIA VISUAL

A imagem anexa mostra o layout exato esperado. Reproduza fielmente:
- Tema escuro industrial com acentos laranja/verde/azul
- Tipografia Syne para títulos, IBM Plex Mono para labels
- Cards com borda esquerda colorida
- Gráficos sem fundo branco, integrados ao tema escuro
- Seção de projeção em destaque com barra de progresso gradiente
- Card de status central com ícone grande e texto em destaque

---

*Prompt gerado por Claude (Anthropic) com base nos dados reais da tabela integration_truckpag_transacoes do B.I Manutenção Gritsch.*
