<template>
  <div class="card card-acao">
    <div class="card-header">
      <div>
        <div class="card-title">Monitoramento de Frota</div>
        <div class="card-hint" v-if="resumo.total_acao != null">
          {{ resumo.total_acao }} veículos fora do padrão do seu grupo · economia possível {{ fmtR(resumo.economia_total_possivel) }}
        </div>
      </div>
      <button class="btn-csv" @click="exportarCSV" v-if="data.length">Exportar CSV</button>
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
            <th>Grupo</th>
            <th>Filial</th>
            <th class="right">Custo/km</th>
            <th class="right">Média grupo</th>
            <th class="right">vs Grupo</th>
            <th class="right">Economia</th>
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
            <td class="grupo-td">{{ formatGrupo(v.grupo) }}</td>
            <td class="filial-td">{{ v.filial }}</td>
            <td class="right mono" :class="v.flag !== 'OK' ? 'red' : ''">
              {{ v.custo_km ? `R$ ${v.custo_km.toFixed(4)}` : '—' }}
            </td>
            <td class="right mono dim">
              {{ v.media_grupo_custo_km ? `R$ ${v.media_grupo_custo_km.toFixed(4)}` : '—' }}
            </td>
            <td class="right mono" :class="v.pct_vs_grupo > 0 ? 'red' : 'green'">
              {{ v.pct_vs_grupo != null ? (v.pct_vs_grupo > 0 ? '+' : '') + v.pct_vs_grupo.toFixed(1) + '%' : '—' }}
            </td>
            <td class="right mono red semibold">
              {{ v.economia_possivel > 0 ? fmtR(v.economia_possivel) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Resumo -->
    <div class="ref-row" v-if="resumo.total_frota && !loading">
      <div class="ref-item">Frota analisada: <b class="mono">{{ resumo.total_frota }} veículos</b></div>
      <div class="ref-item">Grupos monitorados: <b class="mono">{{ resumo.grupos_monitorados }}</b></div>
      <div class="ref-item" v-if="resumo.media_custo_km_geral">Custo/km geral: <b class="mono">R$ {{ resumo.media_custo_km_geral?.toFixed(4) }}</b></div>
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

function formatGrupo(g) {
  if (!g) return '—'
  return g.replace('Caminhão', 'Cam.').replace('Ton', 'T').replace('10.5', '10,5').replace('4.2', '4,2').replace('5.5', '5,5').replace('7.5', '7,5')
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
  const cols = ['placa','grupo','filial','motorista','modelo','custo_km','media_grupo_custo_km','km_litro','pct_vs_grupo','economia_possivel','flag']
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
.card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.card-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.card-hint { font-size: 12px; color: #94a3b8; margin-top: 2px; }

.btn-csv {
  background: white; border: 1px solid #e2e8f0; color: #64748b;
  font-size: 11px; font-weight: 600; padding: 6px 12px; border-radius: 8px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.2s;
}
.btn-csv:hover { border-color: #f97316; color: #f97316; }

.table-wrap { overflow-x: auto; margin: 0 -24px; padding: 0 24px; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9; white-space: nowrap;
}
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: #fcfcfc; }
tbody td { font-size: 13px; color: #334155; padding: 12px 10px; border-bottom: 1px solid #f8fafc; white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }

tbody tr.row-critico { background: rgba(239,68,68,0.02); }
tbody tr.row-alto    { background: rgba(239,68,68,0.01); }
tbody tr.row-baixo   { background: rgba(245,158,11,0.01); }

.flag-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.02em; }
.flag-critico { background: #fef2f2; color: #ef4444; border: 1px solid rgba(239,68,68,0.2); }
.flag-alto    { background: #fff1f2; color: #ef4444; border: 1px solid rgba(239,68,68,0.1); }
.flag-baixo   { background: #fffbeb; color: #f59e0b; border: 1px solid rgba(245,158,11,0.15); }
.flag-ok      { background: #ecfdf5; color: #10b981; border: 1px solid rgba(34,197,94,0.1); }

.mono { font-family: 'JetBrains Mono', monospace; }
.dim { color: #94a3b8; }
.red { color: #ef4444; font-weight: 600; }
.green { color: #10b981; font-weight: 600; }
.semibold { font-weight: 600; }
.placa { font-weight: 700; color: #0f172a; }
.grupo-td { font-size: 11px; font-weight: 600; color: #64748b; }
.filial-td { font-weight: 500; font-size: 12px; color: #64748b; max-width: 130px; overflow: hidden; text-overflow: ellipsis; }

.ref-row { margin-top: 24px; padding-top: 16px; border-top: 1px dashed #e2e8f0; display: flex; gap: 20px; flex-wrap: wrap; }
.ref-item { font-size: 12px; color: #64748b; }
.ref-item b { color: #0f172a; }

.empty { padding: 48px 0; text-align: center; color: #94a3b8; font-size: 13px; display: flex; flex-direction: column; align-items: center; gap: 12px; }

.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
