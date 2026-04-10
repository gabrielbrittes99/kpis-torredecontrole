<template>
  <div class="page">
    <GlobalTopbar
      title="Auditoria de Estornos"
      subtitle="Trilha de auditoria das transações canceladas ou substituídas"
      :showPeriod="false" :showFilters="false"
    >
      <template #center>
        <div class="topbar-filters">
          <div class="filter-group">
            <label>Período</label>
            <select v-model="modo" @change="loadData">
              <option value="mes">Mês Atual</option>
              <option value="ano">Ano Atual</option>
            </select>
          </div>
        </div>
      </template>
    </GlobalTopbar>

    <div class="page-body">

      <!-- ━━━━━ KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores de Estornos</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Valor Total Estornado"
            :value="kpis.total_estornado || 0"
            format="currency"
            theme="primary"
            :trendInvert="true"
          />
          <KpiCardPro
            title="Ocorrências"
            :value="kpis.quantidade_estornos || 0"
            format="number"
            :description="`de ${kpis.total_transacoes || 0} transações no período`"
          />
          <KpiCardPro
            title="Taxa de Estorno"
            :value="kpis.pct_estornos || 0"
            format="percent"
            :decimals="2"
          />
          <KpiCardPro
            title="Ticket Médio"
            :value="kpis.ticket_medio || 0"
            format="currency"
            :description="`por ocorrência de estorno`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ LAYOUT PRINCIPAL ━━━━━ -->
      <div class="main-grid">

        <!-- RANKING POR FILIAL -->
        <section class="v-block">
          <div class="section-heading">Ranking por Filial</div>
          <div class="card">
            <div v-if="lRanking" class="skel" style="height:200px" />
            <div v-else-if="!rankingFiliais.length" class="empty">Sem dados</div>
            <div v-else class="ranking-list">
              <div v-for="(f, idx) in rankingFiliais" :key="f.filial" class="ranking-item">
                <span class="rank-idx">{{ idx + 1 }}</span>
                <div class="rank-info">
                  <span class="rank-name">{{ f.filial || 'Não informada' }}</span>
                  <span class="rank-sub">{{ f.qtd }} ocorrências</span>
                </div>
                <span class="rank-val">{{ fmtR(f.total_valor) }}</span>
              </div>
            </div>
          </div>

          <!-- Por tipo -->
          <div class="section-heading" style="margin-top:8px">Por Tipo de Transação</div>
          <div class="card">
            <div v-if="lKpis" class="skel" style="height:80px" />
            <div v-else-if="!resumo?.por_tipo?.length" class="empty" style="height:60px">Sem dados</div>
            <div v-else class="tipo-list">
              <div v-for="t in resumo.por_tipo" :key="t.tipo" class="tipo-item">
                <span class="tipo-nome">{{ t.tipo }}</span>
                <div class="tipo-right">
                  <span class="tipo-qtd mono">{{ t.quantidade }}x</span>
                  <span class="tipo-val">{{ fmtR(t.valor) }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- TRILHA ANALÍTICA -->
        <section class="v-block">
          <div class="section-heading">
            Trilha Analítica
            <span class="section-badge" v-if="analitico.length">{{ analitico.length }} registros</span>
          </div>
          <div class="card chart-full">
            <div v-if="lAnalitico" class="skel" style="height:360px" />
            <div v-else-if="!analitico.length" class="empty">Sem estornos no período</div>
            <template v-else>
              <div class="table-wrap">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Data/Hora</th>
                      <th>Tipo</th>
                      <th>Placa</th>
                      <th>Filial</th>
                      <th class="right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in analitico" :key="item.id">
                      <td class="mono dim">{{ item.data_transacao }}</td>
                      <td>
                        <span class="tipo-badge" :class="item.tipo_abastecimento?.toLowerCase().includes('ped') ? 'badge-blue' : 'badge-red'">
                          {{ item.tipo_abastecimento || 'Outro' }}
                        </span>
                      </td>
                      <td class="mono bold">{{ item.placa }}</td>
                      <td class="dim">{{ item.filial_nome || item.filial || '—' }}</td>
                      <td class="right mono bold">{{ fmtR(item.valor) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </div>
        </section>

      </div>
    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { GRITSCH_CONFIG } from '../gritsch.config.js'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

const modo    = ref('mes')
const kpis    = ref({})
const resumo  = ref(null)
const rankingFiliais = ref([])
const analitico = ref([])

const lKpis    = ref(true)
const lRanking = ref(true)
const lAnalitico = ref(true)

const fmtR = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

function buildParams() {
  const now = new Date()
  if (modo.value === 'mes') return `?mes=${now.getMonth() + 1}&ano=${now.getFullYear()}`
  return `?ano=${now.getFullYear()}`
}

async function loadData() {
  lKpis.value = lRanking.value = lAnalitico.value = true
  const p = buildParams()
  await Promise.allSettled([
    fetch(`${BASE}/api/estornos/kpis${p}`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => { kpis.value = d; resumo.value = d })
      .catch(e => console.warn('[Estornos] KPIs:', e))
      .finally(() => lKpis.value = false),
    fetch(`${BASE}/api/estornos/ranking-filiais${p}`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => rankingFiliais.value = d ?? [])
      .catch(e => console.warn('[Estornos] Ranking:', e))
      .finally(() => lRanking.value = false),
    fetch(`${BASE}/api/estornos/analitico${p}&limit=100`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => analitico.value = d ?? [])
      .catch(e => console.warn('[Estornos] Analítico:', e))
      .finally(() => lAnalitico.value = false),
    fetch(`${BASE}/api/estornos/resumo${p}`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => resumo.value = { ...kpis.value, ...d })
      .catch(e => console.warn('[Estornos] Resumo:', e)),
  ])
}

onMounted(loadData)
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

.main-grid { display: grid; grid-template-columns: 320px 1fr; gap: 24px; align-items: start; }

/* Ranking */
.ranking-list { display: flex; flex-direction: column; gap: 12px; }
.ranking-item { display: flex; align-items: center; gap: 12px; }
.rank-idx { font-size: 11px; font-weight: 700; color: #94a3b8; width: 20px; text-align: center; }
.rank-info { flex: 1; display: flex; flex-direction: column; gap: 1px; }
.rank-name { font-size: 13px; font-weight: 600; color: #334155; }
.rank-sub  { font-size: 11px; color: #94a3b8; }
.rank-val  { font-size: 13px; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace; }

/* Tipo */
.tipo-list { display: flex; flex-direction: column; gap: 10px; }
.tipo-item { display: flex; justify-content: space-between; align-items: center; }
.tipo-nome { font-size: 13px; font-weight: 500; color: #334155; }
.tipo-right { display: flex; gap: 12px; align-items: center; }
.tipo-qtd { font-size: 12px; color: #94a3b8; }
.tipo-val { font-size: 13px; font-weight: 700; color: #0f172a; }

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

.tipo-badge {
  display: inline-flex; align-items: center; font-size: 11px; font-weight: 600;
  padding: 2px 8px; border-radius: 4px;
}
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-red  { background: #fee2e2; color: #991b1b; }

.empty { height: 160px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid rgba(0,0,0,0.07); font-size: 12px; color: #94a3b8; text-align: center; margin-top: auto; }

@media (max-width: 1100px) {
  .main-grid { grid-template-columns: 1fr; }
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
