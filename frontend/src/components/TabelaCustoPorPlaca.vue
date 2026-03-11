<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Top veículos por custo</div>
      <div class="card-hint">por valor total gasto</div>
    </div>
    <div v-if="loading" class="skel" style="height:280px" />
    <table v-else-if="data.length">
      <thead>
        <tr>
          <th style="width:28px">#</th>
          <th>Placa</th>
          <th>Modelo</th>
          <th class="right">Total R$</th>
          <th class="right">Litros</th>
          <th class="right">R$/L</th>
          <th style="width:80px"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(p, i) in data" :key="p.placa">
          <td class="rank mono">{{ i + 1 }}</td>
          <td class="placa mono">{{ p.placa }}</td>
          <td class="model">{{ p.marca ? `${p.marca} ${p.modelo}` : p.modelo || '—' }}</td>
          <td class="right mono val">{{ fmtR(p.total_valor) }}</td>
          <td class="right mono dim">{{ fmtN(p.total_litros) }}</td>
          <td class="right mono dim">{{ p.preco_medio.toFixed(3) }}</td>
          <td>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: (p.total_valor / maxVal * 100) + '%' }" />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">Sem dados</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const maxVal = computed(() => props.data.length ? Math.max(...props.data.map(d => d.total_valor)) : 1)
const fmtR = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const fmtN = v => Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; overflow-x: auto; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 200px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

table { width: 100%; border-collapse: collapse; }
thead th { font-size: 11px; font-weight: 500; color: var(--text-3); text-align: left; padding: 0 10px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td { font-size: 12px; color: var(--text-2); padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }

.rank  { color: var(--text-3); font-size: 11px; }
.placa { color: var(--text); font-weight: 600; letter-spacing: .04em; }
.model { color: var(--text-3); font-size: 12px; max-width: 120px; overflow: hidden; text-overflow: ellipsis; }
.val   { color: var(--text); font-weight: 600; }
.dim   { color: var(--text-3); }
.mono  { font-family: 'JetBrains Mono', monospace; }

.bar-track { height: 3px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.bar-fill  { height: 100%; background: var(--accent); border-radius: 2px; opacity: .7; transition: width .6s ease; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
