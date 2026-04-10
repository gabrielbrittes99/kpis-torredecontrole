<template>
  <div class="page">
    <GlobalTopbar
      title="TCO · Custo Total"
      subtitle="Análise unificada: Combustível + Manutenção + Pedágio por veículo"
      :showPeriod="false" :showFilters="false"
    >
      <template #center>
        <div class="topbar-filters">
          <div class="filter-group">
            <label>Mês</label>
            <select v-model="filtroMes" @change="loadData">
              <option v-for="m in mesesDisponiveis" :key="m" :value="m">{{ fmtMes(m) }}</option>
            </select>
          </div>
        </div>
      </template>
    </GlobalTopbar>

    <div class="page-body">

      <!-- ━━━━━ KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores TCO · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Custo Total da Frota"
            :value="kpis.custo_total || 0"
            format="currency"
            theme="primary"
          />
          <KpiCardPro
            title="Média por Veículo"
            :value="kpis.custo_medio_veiculo || 0"
            format="currency"
          />
          <KpiCardPro
            title="% Combustível"
            :value="kpis.breakdown?.combustivel?.pct || 0"
            format="percent"
            :decimals="1"
            :description="`Participação do combustível no TCO`"
          />
          <KpiCardPro
            title="% Manutenção"
            :value="kpis.breakdown?.manutencao?.pct || 0"
            format="percent"
            :decimals="1"
            :description="`Participação da manutenção no TCO`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ RANKING DE VEÍCULOS ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">
          Ranking dos Veículos Mais Onerosos
          <span class="section-badge" v-if="ranking.length">Top {{ ranking.length }}</span>
        </div>
        <div class="card chart-full">
          <div v-if="lRanking" class="skel" style="height:360px" />
          <div v-else-if="!ranking.length" class="empty">Sem dados no período selecionado</div>
          <template v-else>
            <div class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th style="width:40px">#</th>
                    <th>Placa</th>
                    <th>Grupo</th>
                    <th>Filial</th>
                    <th class="right">Combustível</th>
                    <th class="right">Manutenção</th>
                    <th class="right">Pedágio</th>
                    <th class="right bold-col">Custo Total</th>
                    <th class="right">Custo/KM</th>
                    <th style="width:140px">Proporção</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in ranking" :key="item.placa">
                    <td class="idx">{{ idx + 1 }}</td>
                    <td class="mono bold">{{ item.placa }}</td>
                    <td><span class="grupo-badge">{{ item.grupo || '—' }}</span></td>
                    <td class="dim">{{ item.filial || '—' }}</td>
                    <td class="right mono">{{ fmtR(item.custo_combustivel) }}</td>
                    <td class="right mono">{{ fmtR(item.custo_manutencao) }}</td>
                    <td class="right mono">{{ fmtR(item.custo_pedagio) }}</td>
                    <td class="right mono fw-bold orange">{{ fmtR(item.custo_total) }}</td>
                    <td class="right mono dim">{{ item.custo_km ? 'R$ ' + Number(item.custo_km).toLocaleString('pt-BR', {minimumFractionDigits:4, maximumFractionDigits:4}) : '—' }}</td>
                    <td>
                      <div class="prop-bar">
                        <div class="prop-seg comb" :style="{ width: pctBar(item.custo_combustivel, item.custo_total) + '%' }" title="Combustível" />
                        <div class="prop-seg man"  :style="{ width: pctBar(item.custo_manutencao, item.custo_total) + '%' }" title="Manutenção" />
                        <div class="prop-seg ped"  :style="{ width: pctBar(item.custo_pedagio, item.custo_total) + '%' }" title="Pedágio" />
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Legenda -->
            <div class="legenda">
              <span class="leg-item"><span class="leg-dot comb"></span> Combustível</span>
              <span class="leg-item"><span class="leg-dot man"></span> Manutenção</span>
              <span class="leg-item"><span class="leg-dot ped"></span> Pedágio</span>
            </div>
          </template>
        </div>
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { GRITSCH_CONFIG } from '../gritsch.config.js'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

const filtroMes = ref('')
const mesesDisponiveis = ref([])
const kpis    = ref({})
const ranking = ref([])

const lKpis    = ref(true)
const lRanking = ref(true)

const fmtR = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtMes = (ym) => {
  if (!ym) return '—'
  const [ano, mes] = ym.split('-')
  return new Date(Number(ano), Number(mes) - 1).toLocaleString('pt-BR', { month: 'short', year: 'numeric' })
}
const pctBar = (val, total) => total > 0 ? Math.min(100, (val / total) * 100) : 0

async function loadData() {
  if (!filtroMes.value) return
  lKpis.value = lRanking.value = true
  const p = `?ano_mes=${filtroMes.value}`
  await Promise.allSettled([
    fetch(`${BASE}/api/tco/kpis${p}`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => kpis.value = d ?? {})
      .catch(e => console.warn('[TCO] KPIs:', e))
      .finally(() => lKpis.value = false),
    fetch(`${BASE}/api/tco/por-veiculo${p}&limit=50`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => ranking.value = Array.isArray(d) ? d : [])
      .catch(e => console.warn('[TCO] Ranking:', e))
      .finally(() => lRanking.value = false),
  ])
}

async function loadFiltros() {
  try {
    // Pega meses disponíveis do FKM
    const r = await fetch(`${BASE}/api/fkm/filtros`)
    const d = await r.json()
    mesesDisponiveis.value = (d.meses || []).sort().reverse()
    if (mesesDisponiveis.value.length) {
      filtroMes.value = mesesDisponiveis.value[0]
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(async () => {
  await loadFiltros()
  loadData()
})
</script>

<style scoped>
.page { background: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; color: #0f172a; }
.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 32px; }

.v-block { display: flex; flex-direction: column; gap: 16px; }
.section-heading {
  font-size: 12px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: .1em;
  display: flex; align-items: center; gap: 16px;
}
.section-heading::after { content: ''; flex: 1; height: 1px; background: #e2e8f0; }
.section-badge {
  font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px;
  background: #f1f5f9; color: #64748b; text-transform: none; letter-spacing: 0;
}

.kpi-pro-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.card { background: linear-gradient(white, white) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
.chart-full { padding: 32px; }

/* Tabela */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 12px;
  border-bottom: 2px solid rgba(0,0,0,0.07); white-space: nowrap;
}
.data-table th.right, .data-table td.right { text-align: right; }
.data-table tbody td {
  font-size: 13px; color: #334155; padding: 10px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.03); white-space: nowrap; vertical-align: middle;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: #f8fafc; }

.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.bold { font-weight: 700; color: #0f172a; }
.dim  { color: #94a3b8; }
.fw-bold { font-weight: 700; }
.orange { color: #C41230; }
.idx { font-size: 11px; font-weight: 700; color: #94a3b8; }

.bold-col { font-weight: 800; }
.grupo-badge {
  display: inline-block; font-size: 10px; font-weight: 600;
  padding: 2px 7px; border-radius: 4px; background: #f1f5f9; color: #475569;
}

/* Barra proporcional */
.prop-bar { display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: #f1f5f9; }
.prop-seg { height: 100%; transition: width 0.4s ease; }
.comb { background: #f97316; }
.man  { background: #3b82f6; }
.ped  { background: #10b981; }

/* Legenda */
.legenda { display: flex; gap: 20px; margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.04); }
.leg-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #64748b; font-weight: 500; }
.leg-dot { width: 10px; height: 10px; border-radius: 2px; }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid rgba(0,0,0,0.07); font-size: 12px; color: #94a3b8; text-align: center; margin-top: auto; }

@media (max-width: 900px) {
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
