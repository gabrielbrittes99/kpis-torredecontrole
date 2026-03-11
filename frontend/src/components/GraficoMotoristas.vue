<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Preço médio pago por motorista</div>
      <div class="card-hint">do mais econômico ao mais caro · mín. 3 abastecimentos</div>
    </div>
    <div v-if="loading" class="skel" style="height:260px" />
    <div v-else-if="!data.length" class="empty">Dados de motorista não disponíveis</div>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:28px">#</th>
            <th>Motorista</th>
            <th class="right">R$/L médio</th>
            <th class="right">Total R$</th>
            <th class="right">Abast.</th>
            <th style="width:100px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(m, i) in data" :key="m.motorista">
            <td class="rank mono">{{ i + 1 }}</td>
            <td class="name">{{ m.motorista || '—' }}</td>
            <td class="right">
              <span class="preco mono" :class="i === 0 ? 'green' : i === data.length - 1 ? 'red' : ''">
                R$ {{ m.preco_medio.toFixed(3) }}
              </span>
            </td>
            <td class="right mono dim">{{ fmtR(m.total_valor) }}</td>
            <td class="right mono dim">{{ m.qtd_abastecimentos }}</td>
            <td>
              <div class="bar-track">
                <div class="bar-fill" :class="i === 0 ? 'green' : i === data.length - 1 ? 'red' : 'neutral'"
                  :style="{ width: barW(m.preco_medio) + '%' }" />
              </div>
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

const minP = computed(() => props.data.length ? Math.min(...props.data.map(d => d.preco_medio)) : 0)
const maxP = computed(() => props.data.length ? Math.max(...props.data.map(d => d.preco_medio)) : 1)

function barW(preco) {
  const range = maxP.value - minP.value
  if (!range) return 50
  return Math.max(5, (preco - minP.value) / range * 100)
}

const fmtR = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead th { font-size: 11px; font-weight: 500; color: var(--text-3); text-align: left; padding: 0 10px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td { font-size: 12px; color: var(--text-2); padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }

.rank { color: var(--text-3); font-size: 11px; }
.name { color: var(--text); font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
.preco { font-size: 13px; font-weight: 600; color: var(--text); }
.preco.green { color: var(--green); }
.preco.red   { color: var(--red); }
.dim  { color: var(--text-3); }
.mono { font-family: 'JetBrains Mono', monospace; }

.bar-track { height: 3px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; opacity: .8; transition: width .6s ease; }
.bar-fill.green   { background: var(--green); }
.bar-fill.red     { background: var(--red); }
.bar-fill.neutral { background: var(--accent); }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
