<template>
  <div class="page">
    <GlobalTopbar
      title="Monitoramento de Transações"
      subtitle="Visão em tempo real das transações recusadas na TruckPag"
    />

    <div class="page-body">

      <!-- ━━━━━ KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores do Dia</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro title="Volume Movimentado" :value="kpis.valor_total || 0" format="currency" />
          <KpiCardPro title="Aprovadas" :value="kpis.qtd_aprovadas || 0" format="number"
            :description="(kpis.taxa_aprovacao || 0) + '% de aprovação'" />
          <KpiCardPro title="Recusadas" :value="kpis.qtd_recusadas || 0" format="number"
            theme="primary"
            :description="(kpis.taxa_recusa || 0) + '% de recusa'" />
          <KpiCardPro title="Placas Distintas" :value="kpis.veiculos_unicos || 0" format="number" />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- ━━━━━ ÁREA PRINCIPAL ━━━━━ -->
      <div class="main-grid">

        <!-- FEED DE RECUSADAS -->
        <section class="v-block">
          <div class="section-heading">
            Últimas Transações Recusadas
            <span class="live-badge">● AO VIVO</span>
          </div>

          <div class="card chart-full">
            <div v-if="lRecusadas" class="skel" style="height:300px" />
            <div v-else-if="recusadas.length === 0" class="empty">
              Nenhuma transação recusada hoje 🎉
            </div>
            <template v-else>
              <div class="grupo-table-wrap">
                <table class="grupo-table">
                  <thead>
                    <tr>
                      <th>Hora</th>
                      <th>Placa</th>
                      <th>Motorista</th>
                      <th>Posto</th>
                      <th class="right">Valor</th>
                      <th>Motivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in recusadas" :key="t.transacao_id" class="recusa-row">
                      <td class="mono dim">{{ formatTime(t.transacao_data) }}</td>
                      <td class="mono bold">{{ t.veiculo_placa || '—' }}</td>
                      <td>{{ t.motorista_nome || '—' }}</td>
                      <td class="dim">
                        {{ t.estabelecimento_nome || '—' }}
                        <span v-if="t.combustivel_nome" class="tag-combustivel">{{ t.combustivel_nome }}</span>
                      </td>
                      <td class="right mono red bold">{{ fmtR(t.transacao_valor) }}</td>
                      <td>
                        <span class="motivo-badge">{{ t.motivo_descricao }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </div>
        </section>

        <!-- SIDEBAR: RANKING DE MOTIVOS -->
        <section class="v-block side-panel">
          <div class="section-heading">Motivos de Recusa</div>
          <div class="card" style="padding: 24px;">
            <div v-if="lMotivos" class="skel" style="height:200px" />
            <div v-else-if="motivos.length === 0" class="empty" style="height:100px">Sem dados</div>
            <div v-else class="motivos-list">
              <div v-for="m in motivos" :key="m.motivo" class="motivo-item">
                <div class="motivo-header">
                  <span class="motivo-nome">{{ m.motivo }}</span>
                  <span class="motivo-qtd">{{ m.qtd }}x</span>
                </div>
                <div class="motivo-bar-track">
                  <div class="motivo-bar-fill" :style="{ width: m.pct + '%' }" />
                </div>
                <span class="motivo-pct">{{ m.pct }}%</span>
              </div>
            </div>
          </div>

          <!-- Controle de atualização -->
          <div class="card" style="padding: 20px; margin-top: 0;">
            <div class="status-row">
              <span class="status-dot" :class="{ active: !lKpis }"></span>
              <span class="dim" style="font-size:12px;">
                {{ ultimaAtualizacao ? 'Atualizado ' + formatTime(ultimaAtualizacao) : 'Aguardando...' }}
              </span>
            </div>
            <div style="margin-top: 12px; display: flex; gap: 8px; align-items: center;">
              <span style="font-size:12px; color:#94a3b8;">Intervalo:</span>
              <select v-model="intervalo" class="select-intervalo" @change="resetPolling">
                <option :value="15000">15s</option>
                <option :value="30000">30s</option>
                <option :value="60000">1 min</option>
                <option :value="120000">2 min</option>
              </select>
            </div>
            <button @click="loadAll" class="btn-atualizar" :disabled="lKpis">
              {{ lKpis ? 'Atualizando...' : 'Atualizar Agora' }}
            </button>
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
import { ref, onMounted, onUnmounted } from 'vue'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { GRITSCH_CONFIG } from '../gritsch.config.js'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

const kpis     = ref({})
const recusadas = ref([])
const motivos  = ref([])
const ultimaAtualizacao = ref(null)
const intervalo = ref(30000)

const lKpis     = ref(true)
const lRecusadas = ref(true)
const lMotivos  = ref(true)

let pollingTimer = null

const fmtR = v => v != null
  ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  : '—'

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function loadAll() {
  lKpis.value = lRecusadas.value = lMotivos.value = true
  await Promise.allSettled([
    fetch(`${BASE}/api/gestao-transacoes/kpis-dia`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => kpis.value = d ?? {})
      .catch(e => console.warn('[Transações] KPIs:', e))
      .finally(() => lKpis.value = false),
    fetch(`${BASE}/api/gestao-transacoes/recusadas?limit=50`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => recusadas.value = d ?? [])
      .catch(e => console.warn('[Transações] Recusadas:', e))
      .finally(() => lRecusadas.value = false),
    fetch(`${BASE}/api/gestao-transacoes/motivos-ranking`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(d => motivos.value = d ?? [])
      .catch(e => console.warn('[Transações] Motivos:', e))
      .finally(() => lMotivos.value = false),
  ])
  ultimaAtualizacao.value = new Date().toISOString()
}

function resetPolling() {
  if (pollingTimer) clearInterval(pollingTimer)
  pollingTimer = setInterval(loadAll, intervalo.value)
}

onMounted(() => {
  loadAll()
  pollingTimer = setInterval(loadAll, intervalo.value)
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
})
</script>

<style scoped>
.page { background-color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; color: #0f172a; }
.page-body { padding: 24px 32px; display: flex; flex-direction: column; gap: 32px; }

.v-block { display: flex; flex-direction: column; gap: 16px; }
.section-heading {
  font-size: 12px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: .1em;
  display: flex; align-items: center; gap: 16px;
}
.section-heading::after { content: ''; flex: 1; height: 1px; background: #e2e8f0; }

.kpi-pro-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.card { background: linear-gradient(white, white) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
.chart-full { padding: 32px; }

/* Grid principal */
.main-grid { display: grid; grid-template-columns: 1fr 320px; gap: 24px; align-items: start; }
.side-panel { gap: 16px; }

/* Live badge */
.live-badge {
  font-size: 10px; font-weight: 700; color: #dc2626;
  background: #fef2f2; padding: 3px 8px; border-radius: 20px;
  animation: pulse-red 2s infinite;
}
@keyframes pulse-red { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Tabela */
.grupo-table-wrap { overflow-x: auto; }
.grupo-table { width: 100%; border-collapse: collapse; }
.grupo-table thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 12px;
  border-bottom: 2px solid rgba(0,0,0,0.07); white-space: nowrap;
}
.grupo-table th.right, .grupo-table td.right { text-align: right; }
.grupo-table tbody td {
  font-size: 13px; color: #334155; padding: 12px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.03); white-space: nowrap; vertical-align: middle;
}
.grupo-table tbody tr:last-child td { border-bottom: none; }
.recusa-row:hover { background: #fff5f5; }

.mono  { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.bold  { font-weight: 700; color: #0f172a; }
.dim   { color: #94a3b8; }
.red   { color: #dc2626; }

.tag-combustivel {
  display: inline-block; margin-left: 6px;
  font-size: 10px; background: #f1f5f9; color: #64748b;
  padding: 1px 6px; border-radius: 4px;
}

.motivo-badge {
  display: inline-flex; align-items: center;
  font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 20px;
  background: #fef2f2; color: #dc2626; border: 1px solid rgba(220,38,38,.15);
  white-space: nowrap;
}

/* Motivos sidebar */
.motivos-list { display: flex; flex-direction: column; gap: 14px; }
.motivo-item { display: flex; flex-direction: column; gap: 4px; }
.motivo-header { display: flex; justify-content: space-between; align-items: center; }
.motivo-nome { font-size: 12px; font-weight: 600; color: #334155; }
.motivo-qtd  { font-size: 12px; font-weight: 700; color: #dc2626; font-family: 'JetBrains Mono', monospace; }
.motivo-bar-track { height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.motivo-bar-fill  { height: 100%; background: linear-gradient(90deg, #dc2626, #f87171); border-radius: 3px; transition: width 0.5s ease; }
.motivo-pct { font-size: 10px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; }

/* Status e controles */
.status-row { display: flex; align-items: center; gap: 8px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; }
.status-dot.active { background: #10b981; animation: pulse-green 2s infinite; }
@keyframes pulse-green { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.select-intervalo {
  font-size: 12px; padding: 4px 8px; border: 1px solid #e2e8f0;
  border-radius: 6px; background: white; color: #334155; cursor: pointer;
}

.btn-atualizar {
  margin-top: 12px; width: 100%; padding: 8px;
  background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 12px; font-weight: 700; color: #475569; cursor: pointer;
  transition: background 0.2s;
}
.btn-atualizar:hover:not(:disabled) { background: #e2e8f0; }
.btn-atualizar:disabled { opacity: 0.5; cursor: not-allowed; }

.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.5s infinite; }
.kpi-skel { height: 130px; }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

.footer { padding: 32px; border-top: 1px solid rgba(0,0,0,0.07); font-size: 12px; color: #94a3b8; text-align: center; }

@media (max-width: 1100px) {
  .main-grid { grid-template-columns: 1fr; }
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
