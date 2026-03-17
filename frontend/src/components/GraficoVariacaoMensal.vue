<template>
  <div class="card card-variacao">
    <div class="card-header">
      <div class="card-title">Variação Mensal de Preço</div>
      <div class="card-hint">% mês a mês por combustível</div>
    </div>
    <div v-if="loading" class="skel" style="height:260px" />
    <div v-else-if="!rows.length" class="empty">Sem dados suficientes para análise</div>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Combustível</th>
            <th>Mês</th>
            <th class="right">Preço Médio</th>
            <th class="right">Variação</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.combustivel + row.ano_mes">
            <td class="name-col">{{ row.combustivel }}</td>
            <td class="mono dim">{{ fmtMes(row.ano_mes) }}</td>
            <td class="right mono medium">R$ {{ row.preco_medio.toFixed(3) }}</td>
            <td class="right">
              <span v-if="row.variacao_pct !== null" :class="varClass(row.variacao_pct)" class="badge">
                {{ row.variacao_pct > 0 ? '+' : '' }}{{ row.variacao_pct.toFixed(2) }}%
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
  if (pct > 1) return 'red'
  if (pct < -1) return 'green'
  return 'neutral'
}
</script>

<style scoped>
.card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 24px; }
.card-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.card-hint { font-size: 11px; color: #94a3b8; }

.table-wrap { overflow-x: auto; margin: 0 -24px; padding: 0 24px; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9; white-space: nowrap;
}
th.right, td.right { text-align: right; }
tbody td { font-size: 13px; color: #334155; padding: 12px 10px; border-bottom: 1px solid #f8fafc; white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }

.name-col { font-weight: 600; color: #0f172a; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.medium { font-weight: 500; }
.dim { color: #94a3b8; }

.badge {
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; min-width: 54px;
  padding: 3px 8px; border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
}
.badge.green { color: #10b981; background: #ecfdf5; border: 1px solid rgba(16,185,129,0.1); }
.badge.red   { color: #ef4444; background: #fef2f2; border: 1px solid rgba(239,68,68,0.1); }
.badge.neutral { color: #64748b; background: #f1f5f9; border: 1px solid #e2e8f0; }

.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
