<template>
  <div class="card card-acao">
    <div class="card-header">
      <div>
        <div class="card-title">Monitoramento de Frota</div>
        <div class="card-hint" v-if="resumo.total_acao != null">
          Top {{ dataLimitada.length }} de {{ data.length }} veículos fora do padrão · economia possível {{ fmtR(resumo.economia_total_possivel) }}
        </div>
      </div>
      <div class="header-actions">
        <div class="tab-switch">
          <button class="tab-btn" :class="{ active: viewMode === 'ambos' }" @click="viewMode = 'ambos'">Completo</button>
          <button class="tab-btn" :class="{ active: viewMode === 'kml' }" @click="viewMode = 'kml'">km/L</button>
          <button class="tab-btn" :class="{ active: viewMode === 'custo' }" @click="viewMode = 'custo'">R$/km</button>
        </div>
        <button class="btn-csv" @click="exportarCSV" v-if="data.length">Exportar CSV</button>
      </div>
    </div>

    <div v-if="loading" class="skel" style="height:280px" />
    <div v-else-if="!data.length" class="empty">
      <div>Todos os veículos estão dentro do padrão do seu grupo</div>
    </div>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Placa</th>
            <th>Modelo</th>
            <th>Grupo</th>
            <th>Filial</th>
            <!-- Colunas km/L -->
            <th v-if="showKml" class="right col-kml">km/L</th>
            <th v-if="showKml" class="right col-kml">Média Grp</th>
            <th v-if="showKml" class="right col-kml">Δ km/L</th>
            <!-- Colunas custo/km -->
            <th v-if="showCusto" class="right col-custo">R$/km</th>
            <th v-if="showCusto" class="right col-custo">Média Grp</th>
            <th v-if="showCusto" class="right col-custo">vs Grupo</th>
            <!-- Economia -->
            <th class="right">Economia</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in dataLimitada" :key="v.placa" :class="rowClass(v.flag)">
            <td>
              <span class="flag-badge" :class="flagClass(v.flag)">
                {{ flagLabel(v.flag) }}
              </span>
            </td>
            <td class="mono placa">{{ v.placa }}</td>
            <td class="modelo-td">{{ v.modelo || '—' }}</td>
            <td class="grupo-td">{{ formatGrupo(v.grupo) }}</td>
            <td class="filial-td">{{ v.filial || '—' }}</td>

            <!-- km/L do veículo -->
            <td v-if="showKml" class="right mono" :class="kmlClass(v)">
              {{ v.km_litro ? v.km_litro.toFixed(2) : '—' }}
            </td>
            <!-- Média km/L do grupo -->
            <td v-if="showKml" class="right mono dim">
              {{ v.media_grupo_km_litro ? v.media_grupo_km_litro.toFixed(2) : '—' }}
            </td>
            <!-- Delta km/L -->
            <td v-if="showKml" class="right mono" :class="deltaKmlClass(v)">
              <template v-if="v.km_litro && v.media_grupo_km_litro">
                {{ deltaKml(v) > 0 ? '+' : '' }}{{ deltaKml(v).toFixed(2) }}
                <span class="delta-pct">({{ deltaKmlPct(v) > 0 ? '+' : '' }}{{ deltaKmlPct(v).toFixed(0) }}%)</span>
              </template>
              <template v-else>—</template>
            </td>

            <!-- Custo/km do veículo -->
            <td v-if="showCusto" class="right mono" :class="v.flag !== 'OK' ? 'red' : ''">
              {{ v.custo_km ? `R$ ${v.custo_km.toFixed(4)}` : '—' }}
            </td>
            <!-- Média custo/km do grupo -->
            <td v-if="showCusto" class="right mono dim">
              {{ v.media_grupo_custo_km ? `R$ ${v.media_grupo_custo_km.toFixed(4)}` : '—' }}
            </td>
            <!-- % vs grupo (custo) -->
            <td v-if="showCusto" class="right mono" :class="v.pct_vs_grupo > 0 ? 'red' : 'green'">
              {{ v.pct_vs_grupo != null ? (v.pct_vs_grupo > 0 ? '+' : '') + v.pct_vs_grupo.toFixed(1) + '%' : '—' }}
            </td>

            <!-- Economia -->
            <td class="right mono red semibold">
              {{ v.economia_possivel > 0 ? fmtR(v.economia_possivel) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="data.length > TOP_LIMIT" class="ver-mais-hint">
        Exibindo os {{ TOP_LIMIT }} piores · <b>{{ data.length - TOP_LIMIT }}</b> outros no CSV
      </div>
    </div>

    <!-- Resumo -->
    <div class="ref-row" v-if="resumo.total_frota && !loading">
      <div class="ref-item">Frota analisada: <b class="mono">{{ resumo.total_frota }} veículos</b></div>
      <div class="ref-item">Grupos monitorados: <b class="mono">{{ resumo.grupos_monitorados }}</b></div>
      <div class="ref-item" v-if="resumo.media_km_litro_geral">
        Média km/L geral: <b class="mono">{{ resumo.media_km_litro_geral?.toFixed(2) }} km/L</b>
      </div>
      <div class="ref-item" v-if="resumo.media_custo_km_geral">
        Custo/km geral: <b class="mono">R$ {{ resumo.media_custo_km_geral?.toFixed(4) }}</b>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  resumo:  { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const TOP_LIMIT = 10
const viewMode = ref('ambos') // 'ambos' | 'kml' | 'custo'
const dataLimitada = computed(() => props.data.slice(0, TOP_LIMIT))

const showKml = computed(() => viewMode.value === 'ambos' || viewMode.value === 'kml')
const showCusto = computed(() => viewMode.value === 'ambos' || viewMode.value === 'custo')

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'

function formatGrupo(g) {
  if (!g) return '—'
  return g
}

// km/L helpers
function deltaKml(v) {
  return v.km_litro - v.media_grupo_km_litro
}
function deltaKmlPct(v) {
  return ((v.km_litro - v.media_grupo_km_litro) / v.media_grupo_km_litro) * 100
}
function kmlClass(v) {
  if (!v.km_litro || !v.media_grupo_km_litro) return ''
  const delta = deltaKml(v)
  if (delta < -v.media_grupo_km_litro * 0.15) return 'red'
  if (delta < 0) return 'orange'
  return 'green'
}
function deltaKmlClass(v) {
  if (!v.km_litro || !v.media_grupo_km_litro) return ''
  const pct = deltaKmlPct(v)
  if (pct < -15) return 'red'
  if (pct < 0) return 'orange'
  return 'green'
}

const flagLabel = flag => ({
  CRITICO: 'Crítico', ALTO_CUSTO: 'Alto custo', BAIXO_RENDIMENTO: 'Baixo rend.', OK: 'Normal',
}[flag] ?? flag)

const flagClass = flag => ({
  CRITICO: 'flag-critico', ALTO_CUSTO: 'flag-alto', BAIXO_RENDIMENTO: 'flag-baixo', OK: 'flag-ok',
}[flag] ?? '')

const rowClass = flag => ({
  CRITICO: 'row-critico', ALTO_CUSTO: 'row-alto', BAIXO_RENDIMENTO: 'row-baixo',
}[flag] ?? '')

function exportarCSV() {
  const cols = ['placa','grupo','filial','motorista','modelo','km_litro','media_grupo_km_litro','custo_km','media_grupo_custo_km','pct_vs_grupo','economia_possivel','flag']
  const header = cols.join(';')
  const rows = props.data.map(v => cols.map(c => v[c] ?? '').join(';'))
  const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `veiculos-acao-${new Date().toISOString().slice(0,10)}.csv`
  a.click()
}
</script>

<style scoped>
.card { background: linear-gradient(white, white) padding-box, linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box; border: 1px solid transparent; border-radius: 16px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.card-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.card-hint { font-size: 12px; color: #94a3b8; margin-top: 2px; }

.header-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* ── Tab Switch ── */
.tab-switch {
  display: flex; gap: 2px;
  background: #f1f5f9; padding: 3px; border-radius: 8px;
}
.tab-btn {
  background: transparent; border: none;
  padding: 5px 12px; border-radius: 6px;
  font-size: 11px; font-weight: 600; color: #64748b;
  cursor: pointer; transition: all 0.2s;
  font-family: 'Inter', sans-serif;
}
.tab-btn:hover { color: #334155; }
.tab-btn.active {
  background: white; color: #0f172a;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.btn-csv {
  background: white; border: 1px solid #e2e8f0; color: #64748b;
  font-size: 11px; font-weight: 600; padding: 6px 12px; border-radius: 8px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.2s;
}
.btn-csv:hover { border-color: #C41230; color: #C41230; }

.table-wrap { overflow-x: auto; margin: 0 -24px; padding: 0 24px; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 12px 10px;
  border-bottom: 1px solid rgba(0,0,0,0.07); white-space: nowrap;
}
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: #fcfcfc; }
tbody td { font-size: 13px; color: #334155; padding: 12px 10px; border-bottom: 1px solid rgba(0,0,0,0.03); white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }

tbody tr.row-critico { background: rgba(239,68,68,0.02); }
tbody tr.row-alto    { background: rgba(239,68,68,0.01); }
tbody tr.row-baixo   { background: rgba(245,158,11,0.01); }

/* ── Column highlights ── */
.col-kml { color: #0369a1; }
.col-custo { color: #7c3aed; }

.flag-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.02em; }
.flag-critico { background: #fef2f2; color: #ef4444; border: 1px solid rgba(239,68,68,0.2); }
.flag-alto    { background: #fff1f2; color: #ef4444; border: 1px solid rgba(239,68,68,0.1); }
.flag-baixo   { background: #fffbeb; color: #f59e0b; border: 1px solid rgba(245,158,11,0.15); }
.flag-ok      { background: #ecfdf5; color: #10b981; border: 1px solid rgba(34,197,94,0.1); }

.mono { font-family: 'JetBrains Mono', monospace; }
.dim { color: #94a3b8; }
.red { color: #ef4444; font-weight: 600; }
.orange { color: #d97706; font-weight: 600; }
.green { color: #10b981; font-weight: 600; }
.semibold { font-weight: 600; }
.placa { font-weight: 700; color: #0f172a; }
.modelo-td { font-size: 11px; font-weight: 500; color: #475569; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.grupo-td { font-size: 11px; font-weight: 600; color: #64748b; }
.filial-td { font-weight: 500; font-size: 12px; color: #64748b; max-width: 130px; overflow: hidden; text-overflow: ellipsis; }

.delta-pct { font-size: 10px; opacity: 0.75; margin-left: 2px; }

.ref-row { margin-top: 24px; padding-top: 16px; border-top: 1px dashed #e2e8f0; display: flex; gap: 20px; flex-wrap: wrap; }
.ref-item { font-size: 12px; color: #64748b; }
.ref-item b { color: #0f172a; }

.ver-mais-hint {
  text-align: center; padding: 12px 0 4px; font-size: 11px; color: #94a3b8;
  border-top: 1px dashed #e2e8f0; margin-top: 4px;
}
.ver-mais-hint b { color: #64748b; }

.empty { padding: 48px 0; text-align: center; color: #94a3b8; font-size: 13px; display: flex; flex-direction: column; align-items: center; gap: 12px; }

.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
