<template>
  <div class="sl-page">
    <!-- Header -->
    <div class="sl-header">
      <div class="sl-header-left">
        <div class="sl-title-row">
          <h1 class="sl-title font-syne">Sumário do Sistema</h1>
          <span class="sl-badge">Referência</span>
        </div>
        <p class="sl-subtitle">
          Como os dados são classificados, filtrados e calculados neste painel.
        </p>
      </div>
      <div v-if="stats" class="sl-header-stats">
        <div class="sl-stat">
          <span class="sl-stat-val mono">{{ fmt(stats.total_abastecimentos) }}</span>
          <span class="sl-stat-lbl">abastecimentos</span>
        </div>
        <div class="sl-stat">
          <span class="sl-stat-val mono">{{ fmt(stats.total_veiculos) }}</span>
          <span class="sl-stat-lbl">veículos</span>
        </div>
        <div class="sl-stat">
          <span class="sl-stat-val mono">{{ fmt(stats.total_postos) }}</span>
          <span class="sl-stat-lbl">postos</span>
        </div>
        <div class="sl-stat">
          <span class="sl-stat-val mono" style="font-size:12px">{{ stats.periodo_inicio }} → {{ stats.periodo_fim }}</span>
          <span class="sl-stat-lbl">período</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="sl-loading">Carregando...</div>
    <div v-else-if="error" class="sl-error">{{ error }}</div>

    <template v-else>
      <!-- ── Regras de coleta ──────────────────────────────────────────────── -->
      <section class="sl-section">
        <h2 class="sl-section-title font-syne">Regras de Coleta</h2>
        <div class="sl-rules-grid">
          <div class="sl-rule-card">
            <div class="sl-rule-icon">⊘</div>
            <div>
              <div class="sl-rule-name">Filtro base</div>
              <div class="sl-rule-desc mono">{{ stats?.filtro_base }}</div>
            </div>
          </div>
          <div class="sl-rule-card">
            <div class="sl-rule-icon">⊙</div>
            <div>
              <div class="sl-rule-name">Cálculo km/L</div>
              <div class="sl-rule-desc mono">{{ stats?.calculo_kml }}</div>
            </div>
          </div>
          <div class="sl-rule-card">
            <div class="sl-rule-icon">⊕</div>
            <div>
              <div class="sl-rule-name">Fonte de filiais</div>
              <div class="sl-rule-desc mono">{{ stats?.fonte_filiais }}</div>
            </div>
          </div>
          <div class="sl-rule-card" v-if="placasRenomeadas.length">
            <div class="sl-rule-icon">⇄</div>
            <div>
              <div class="sl-rule-name">Placas renomeadas</div>
              <div class="sl-rule-desc mono">
                <span v-for="r in placasRenomeadas" :key="r.antiga">
                  {{ r.antiga }} → {{ r.nova }}&nbsp;
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Grupos de veículo ─────────────────────────────────────────────── -->
      <section class="sl-section">
        <h2 class="sl-section-title font-syne">Classificação de Veículos</h2>
        <p class="sl-section-desc">
          Cada veículo é classificado pelo seu modelo e marca. A meta de km/L é o percentil 75 da frota real;
          o alerta (⚠) é o percentil 25.
        </p>
        <div class="sl-table-wrap">
          <table class="sl-table">
            <thead>
              <tr>
                <th>Grupo</th>
                <th>Modelos de referência</th>
                <th>Combustível</th>
                <th class="right">km/L meta</th>
                <th class="right">km/L alerta</th>
                <th class="right">Veículos</th>
                <th class="right">Abast.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in gruposVeiculo" :key="g.grupo">
                <td>
                  <span class="sl-chip" :style="{ background: grupoColor(g.grupo) + '22', color: grupoColor(g.grupo) }">
                    {{ g.grupo }}
                  </span>
                </td>
                <td class="sl-models">{{ (g.modelos_exemplo || []).join(', ') || '—' }}</td>
                <td>
                  <span v-if="g.combustivel_padrao" class="sl-fuel-tag" :style="{ color: fuelColor(g.combustivel_padrao) }">
                    {{ g.combustivel_padrao }}
                  </span>
                  <span v-else class="dim">—</span>
                </td>
                <td class="right mono">{{ g.kml_meta ?? '—' }}</td>
                <td class="right mono">{{ g.kml_alerta ?? '—' }}</td>
                <td class="right mono">{{ g.qtd_veiculos || '—' }}</td>
                <td class="right mono">{{ fmt(g.qtd_abastecimentos) || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── Grupos de combustível ─────────────────────────────────────────── -->
      <section class="sl-section">
        <h2 class="sl-section-title font-syne">Classificação de Combustíveis</h2>
        <div class="sl-fuel-grid">
          <div
            v-for="g in gruposCombustivel"
            :key="g.grupo"
            class="sl-fuel-card"
            :style="{ borderColor: g.cor + '55' }"
          >
            <div class="sl-fuel-header" :style="{ color: g.cor }">
              <span class="sl-fuel-name font-syne">{{ g.grupo }}</span>
              <span class="sl-fuel-qty mono">{{ fmt(g.qtd_abastecimentos) }} abast.</span>
            </div>
            <div class="sl-fuel-tags">
              <span v-for="v in g.variacoes" :key="v" class="sl-var-tag">{{ v }}</span>
            </div>
            <div class="sl-fuel-stats">
              <div>
                <span class="sl-stat-num mono">{{ fmtL(g.litros_total) }}</span>
                <span class="sl-stat-unit">litros</span>
              </div>
              <div>
                <span class="sl-stat-num mono">R$ {{ fmtK(g.gasto_total) }}</span>
                <span class="sl-stat-unit">gasto total</span>
              </div>
              <div v-if="g.preco_medio">
                <span class="sl-stat-num mono">R$ {{ g.preco_medio?.toFixed(3) }}</span>
                <span class="sl-stat-unit">preço médio/L</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Filiais por região ─────────────────────────────────────────────── -->
      <section class="sl-section">
        <h2 class="sl-section-title font-syne">Filiais por Região</h2>
        <div class="sl-regiao-grid">
          <div v-for="r in porRegiao" :key="r.regiao" class="sl-regiao-card">
            <div class="sl-regiao-name font-syne">{{ r.regiao }}</div>
            <div class="sl-regiao-filiais">
              <span v-for="f in r.filiais" :key="f" class="sl-filial-tag">{{ f }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Distribuição de idade da frota ───────────────────────────────── -->
      <section v-if="idadeFrota.length" class="sl-section">
        <h2 class="sl-section-title font-syne">Idade da Frota</h2>
        <div class="sl-idade-grid">
          <div v-for="faixa in idadeFrota" :key="faixa.label" class="sl-idade-bar-row">
            <span class="sl-idade-label">{{ faixa.label }}</span>
            <div class="sl-bar-track">
              <div
                class="sl-bar-fill"
                :style="{ width: faixa.pct + '%', background: faixa.color }"
              ></div>
            </div>
            <span class="sl-idade-count mono">{{ faixa.count }} veíc.</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { GRITSCH_CONFIG } from '../gritsch.config'
const BASE_URL = GRITSCH_CONFIG.URLS.BACKEND

const loading = ref(true)
const error = ref(null)
const data = ref(null)

const gruposVeiculo    = computed(() => data.value?.grupos_veiculo    ?? [])
const gruposCombustivel = computed(() => data.value?.grupos_combustivel ?? [])
const porRegiao        = computed(() => data.value?.por_regiao        ?? [])
const placasRenomeadas = computed(() => data.value?.placas_renomeadas ?? [])
const palmasPlacas     = computed(() => data.value?.palmas_placas     ?? [])
const stats            = computed(() => data.value?.estatisticas      ?? null)

const IDADE_COLORS = {
  '0–2 anos': '#22c55e',
  '3–5 anos': '#3b82f6',
  '6–10 anos': '#f97316',
  '> 10 anos': '#ef4444',
}

const idadeFrota = computed(() => {
  const dist = stats.value?.distribuicao_idade_frota ?? {}
  const total = Object.values(dist).reduce((a, b) => a + b, 0)
  if (!total) return []
  const order = ['0–2 anos', '3–5 anos', '6–10 anos', '> 10 anos']
  return order
    .filter(k => k in dist)
    .map(k => ({
      label: k,
      count: dist[k],
      pct: Math.round((dist[k] / total) * 100),
      color: IDADE_COLORS[k] ?? '#6b7280',
    }))
})

const GRUPO_COLORS = {
  'Caminhão17Ton':  '#f97316',
  'Caminhão12Ton':  '#fb923c',
  'Caminhão10.5Ton':'#fdba74',
  'Caminhão9Ton':   '#fcd34d',
  'Caminhão7.5Ton': '#fbbf24',
  'Caminhão6Ton':   '#f59e0b',
  'Caminhão5.5Ton': '#d97706',
  'Caminhão5Ton':   '#b45309',
  'Caminhão4.2Ton': '#92400e',
  'Pesado':         '#3b82f6',
  'Médio':          '#60a5fa',
  'Leve':           '#93c5fd',
  'Kombi':          '#6366f1',
  'Moto':           '#8b5cf6',
}

const FUEL_COLORS = {
  'Diesel':   '#f97316',
  'Gasolina': '#3b82f6',
  'Álcool':   '#10b981',
  'Arla':     '#8b5cf6',
}

const grupoColor = (g) => GRUPO_COLORS[g] ?? '#6b7280'
const fuelColor  = (f) => FUEL_COLORS[f]  ?? '#6b7280'

const fmt  = (n) => n != null ? Number(n).toLocaleString('pt-BR') : '—'
const fmtL = (n) => n != null ? Number(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
const fmtK = (n) => {
  if (n == null) return '—'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(0) + 'k'
  return Number(n).toLocaleString('pt-BR')
}

onMounted(async () => {
  try {
    const res = await fetch(`${BASE_URL}/api/sistema/legenda`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = await res.json()
  } catch (e) {
    error.value = `Erro ao carregar dados: ${e.message}`
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.sl-page {
  padding: 32px 40px 60px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Header */
.sl-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 32px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}
.sl-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.sl-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.02em;
}
.sl-badge {
  background: var(--orange-bg);
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 99px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.sl-subtitle {
  font-size: 14px;
  color: var(--text3);
  max-width: 480px;
}
.sl-header-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.sl-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}
.sl-stat-val {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}
.sl-stat-lbl {
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* Sections */
.sl-section {
  margin-bottom: 48px;
}
.sl-section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}
.sl-section-desc {
  font-size: 13px;
  color: var(--text3);
  margin-bottom: 16px;
}

/* Rules */
.sl-rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.sl-rule-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.sl-rule-icon {
  font-size: 18px;
  color: var(--orange);
  flex-shrink: 0;
  margin-top: 2px;
}
.sl-rule-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}
.sl-rule-desc {
  font-size: 12px;
  color: var(--text3);
  line-height: 1.5;
}

/* Vehicle table */
.sl-table-wrap {
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid var(--border);
}
.sl-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.sl-table thead tr {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.sl-table th {
  padding: 11px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}
.sl-table th.right, .sl-table td.right { text-align: right; }
.sl-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}
.sl-table tbody tr:last-child { border-bottom: none; }
.sl-table tbody tr:hover { background: var(--surface); }
.sl-table td {
  padding: 10px 14px;
  color: var(--text2);
  vertical-align: middle;
}
.sl-chip {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.sl-models {
  color: var(--text3);
  font-size: 12px;
  max-width: 260px;
}
.sl-fuel-tag {
  font-size: 12px;
  font-weight: 600;
}
.dim { color: var(--text3); }

/* Fuel cards */
.sl-fuel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.sl-fuel-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left-width: 3px;
  border-radius: 10px;
  padding: 16px;
}
.sl-fuel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.sl-fuel-name {
  font-size: 15px;
  font-weight: 700;
}
.sl-fuel-qty {
  font-size: 12px;
  color: var(--text3);
}
.sl-fuel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}
.sl-var-tag {
  background: var(--s2);
  color: var(--text3);
  font-size: 11px;
  padding: 3px 7px;
  border-radius: 5px;
}
.sl-fuel-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.sl-stat-num {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}
.sl-stat-unit {
  font-size: 11px;
  color: var(--text3);
}

/* Filiais */
.sl-regiao-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.sl-regiao-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.sl-regiao-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 10px;
}
.sl-regiao-filiais {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.sl-filial-tag {
  background: var(--s2);
  color: var(--text2);
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 5px;
}
.sl-palmas-note {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}

/* Idade da frota */
.sl-idade-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 560px;
}
.sl-idade-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.sl-idade-label {
  font-size: 13px;
  color: var(--text2);
  width: 80px;
  flex-shrink: 0;
}
.sl-bar-track {
  flex: 1;
  height: 8px;
  background: var(--s2);
  border-radius: 99px;
  overflow: hidden;
}
.sl-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease;
}
.sl-idade-count {
  font-size: 12px;
  color: var(--text3);
  width: 70px;
  text-align: right;
  flex-shrink: 0;
}

.sl-loading, .sl-error {
  padding: 48px;
  text-align: center;
  color: var(--text3);
  font-size: 14px;
}
.sl-error { color: #ef4444; }

.mono { font-family: 'JetBrains Mono', monospace; }
.font-syne { font-family: 'Inter', sans-serif; }

/* spacer pushes "Referência" section to bottom */
.sidebar-spacer { flex: 1; }
</style>
