<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Variação mensal de preço</div>
      <div class="card-hint">% mês a mês por combustível</div>
    </div>
    <div v-if="loading" class="skel" style="height:260px" />
    <div v-else-if="!rows.length" class="empty">Sem dados suficientes</div>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Combustível</th>
            <th>Mês</th>
            <th class="right">R$/L</th>
            <th class="right">Var. %</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.combustivel + row.ano_mes">
            <td class="name">{{ row.combustivel }}</td>
            <td class="mono dim">{{ fmtMes(row.ano_mes) }}</td>
            <td class="right mono">{{ row.preco_medio.toFixed(3) }}</td>
            <td class="right">
              <span v-if="row.variacao_pct !== null" :class="varClass(row.variacao_pct)" class="badge">
                {{ row.variacao_pct > 0 ? '+' : '' }}{{ row.variacao_pct.toFixed(1) }}%
              </span>
              <span v-else class="dim">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const MES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES[+m-1]} ${y.slice(2)}` }

// Últimas 2 entradas por combustível
const rows = computed(() => {
  const grouped = {}
  for (const r of props.data) {
    if (!grouped[r.combustivel]) grouped[r.combustivel] = []
    grouped[r.combustivel].push(r)
  }
  const result = []
  for (const [comb, arr] of Object.entries(grouped)) {
    const last2 = arr.slice(-3)
    for (const r of last2) result.push(r)
  }
  return result.sort((a, b) => b.ano_mes.localeCompare(a.ano_mes))
})

const varClass = pct => {
  if (pct > 2) return 'red'
  if (pct < -2) return 'green'
  return 'neutral'
}
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; overflow: auto; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 500; color: var(--text-3);
  text-align: left; padding: 0 10px 10px;
  border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
}
th.right, td.right { text-align: right; }
tbody td { font-size: 12px; color: var(--text-2); padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }

.name { color: var(--text); font-weight: 500; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim { color: var(--text-3); }

.badge {
  display: inline-block; font-size: 11px; font-weight: 600;
  padding: 2px 7px; border-radius: 20px;
  font-family: 'JetBrains Mono', monospace;
}
.badge.green { color: var(--green); background: rgba(34,197,94,.1); }
.badge.red   { color: var(--red);   background: rgba(239,68,68,.1);  }
.badge.neutral { color: var(--text-3); background: var(--border-subtle); }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
