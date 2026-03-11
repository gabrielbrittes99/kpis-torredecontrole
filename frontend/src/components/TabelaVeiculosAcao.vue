<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Veículos para ação urgente — Diesel</div>
        <div class="card-hint" v-if="resumo.total_acao != null">
          {{ resumo.total_acao }} de {{ resumo.total_frota }} veículos · economia total possível {{ fmtR(resumo.economia_total_possivel) }}
        </div>
      </div>
      <button class="btn-csv" @click="exportarCSV" v-if="data.length">⬇ CSV</button>
    </div>

    <div v-if="loading" class="skel" style="height:280px" />
    <div v-else-if="!data.length" class="empty">
      <div style="color:var(--green);font-size:20px">✓</div>
      <div>Nenhum veículo acima do limite — frota dentro da meta</div>
    </div>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Flag</th>
            <th>Placa</th>
            <th>Filial</th>
            <th>Motorista</th>
            <th class="right">Custo/km</th>
            <th class="right">km/L</th>
            <th class="right">Vs média</th>
            <th class="right">Economia possível</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in data" :key="v.placa" :class="rowClass(v.flag)">
            <td>
              <span class="flag-badge" :class="flagClass(v.flag)">
                {{ flagLabel(v.flag) }}
              </span>
            </td>
            <td class="mono placa">{{ v.placa }}</td>
            <td class="filial">{{ v.filial }}</td>
            <td class="motorista dim">{{ v.motorista || '—' }}</td>
            <td class="right mono" :class="v.flag !== 'OK' ? 'red' : ''">
              {{ v.custo_km ? `R$ ${v.custo_km.toFixed(4)}` : '—' }}
            </td>
            <td class="right mono dim">{{ v.km_litro?.toFixed(1) ?? '—' }}</td>
            <td class="right mono" :class="v.pct_vs_media > 0 ? 'red' : 'green'">
              {{ v.pct_vs_media != null ? (v.pct_vs_media > 0 ? '+' : '') + v.pct_vs_media.toFixed(1) + '%' : '—' }}
            </td>
            <td class="right mono red">
              {{ v.economia_possivel > 0 ? fmtR(v.economia_possivel) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Médias de referência -->
    <div class="ref-row" v-if="resumo.media_custo_km && !loading">
      <span>Média frota: <b class="mono">R$ {{ resumo.media_custo_km?.toFixed(4) }}/km</b></span>
      <span v-if="resumo.media_km_litro">· <b class="mono">{{ resumo.media_km_litro?.toFixed(1) }} km/L</b></span>
      <span>· Meta: <b class="mono accent">R$ {{ resumo.meta_custo_km?.toFixed(2) }}/km</b></span>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data:    { type: Array,   default: () => [] },
  resumo:  { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'

const flagLabel = flag => ({
  CRITICO: '🚨 Crítico', ALTO_CUSTO: '🚨 Alto custo', BAIXO_RENDIMENTO: '⚠ Baixo km/L', OK: '✓ OK',
}[flag] ?? flag)

const flagClass = flag => ({
  CRITICO: 'flag-critico', ALTO_CUSTO: 'flag-alto', BAIXO_RENDIMENTO: 'flag-baixo', OK: 'flag-ok',
}[flag] ?? '')

const rowClass = flag => ({
  CRITICO: 'row-critico', ALTO_CUSTO: 'row-alto', BAIXO_RENDIMENTO: 'row-baixo',
}[flag] ?? '')

function exportarCSV() {
  const cols = ['placa','filial','motorista','modelo','custo_km','km_litro','pct_vs_media','economia_possivel','flag']
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
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); margin-top: 2px; }

.btn-csv {
  background: transparent; border: 1px solid var(--border); color: var(--text-3);
  font-size: 11px; padding: 5px 10px; border-radius: 6px; cursor: pointer;
  font-family: 'Inter', sans-serif; white-space: nowrap; transition: all 0.15s;
}
.btn-csv:hover { border-color: var(--accent); color: var(--accent); }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 500; color: var(--text-3);
  text-align: left; padding: 0 10px 10px;
  border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
}
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td { font-size: 12px; color: var(--text-2); padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }

tbody tr.row-critico { background: rgba(239,68,68,.05); }
tbody tr.row-alto    { background: rgba(239,68,68,.03); }
tbody tr.row-baixo   { background: rgba(245,158,11,.03); }

.flag-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.flag-critico { background: rgba(239,68,68,.15); color: #ef4444; border: 1px solid rgba(239,68,68,.3); }
.flag-alto    { background: rgba(239,68,68,.10); color: #ef4444; border: 1px solid rgba(239,68,68,.2); }
.flag-baixo   { background: rgba(245,158,11,.12); color: #f59e0b; border: 1px solid rgba(245,158,11,.25); }
.flag-ok      { background: rgba(34,197,94,.10);  color: #22c55e; border: 1px solid rgba(34,197,94,.2); }

.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: var(--text-3); }
.red  { color: var(--red); }
.green { color: var(--green); }
.accent { color: var(--accent); }
.placa { font-weight: 600; color: var(--text); }
.filial { font-size: 12px; color: var(--text-2); }
.motorista { font-size: 11px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; }

.ref-row { margin-top: 14px; font-size: 12px; color: var(--text-3); display: flex; gap: 12px; flex-wrap: wrap; }
.ref-row b { color: var(--text-2); }
.ref-row .accent { color: var(--accent); }

.empty { padding: 48px 0; text-align: center; color: var(--text-3); font-size: 13px; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
