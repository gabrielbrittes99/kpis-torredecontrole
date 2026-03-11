<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">{{ ordem === 'mais_barato' ? 'Postos mais baratos' : 'Postos mais caros' }}</div>
      <div class="card-hint">mínimo 3 abastecimentos · por preço médio/L</div>
    </div>
    <div v-if="loading" class="skel" style="height:280px" />
    <table v-else-if="data.length">
      <thead>
        <tr>
          <th style="width:32px">#</th>
          <th>Posto</th>
          <th>Cidade</th>
          <th class="right">R$/L</th>
          <th class="right">Total R$</th>
          <th class="right">Litros</th>
          <th class="right">Abast.</th>
          <th style="width:80px"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(p, i) in data" :key="p.razao_social_posto + i">
          <td class="rank mono">{{ i + 1 }}</td>
          <td class="name">{{ p.razao_social_posto || '—' }}</td>
          <td class="city">{{ p.cidade_posto }}<span class="uf"> · {{ p.uf_posto }}</span></td>
          <td class="right mono" :class="i === 0 ? (ordem === 'mais_barato' ? 'green' : 'red') : 'val'">
            R$ {{ p.preco_medio.toFixed(4) }}
          </td>
          <td class="right mono dim">{{ fmtR(p.total_valor) }}</td>
          <td class="right mono dim">{{ fmtN(p.total_litros) }}</td>
          <td class="right mono dim">{{ p.qtd_abastecimentos }}</td>
          <td>
            <div class="bar-track">
              <div class="bar-fill" :class="ordem === 'mais_barato' ? 'green-fill' : 'red-fill'"
                :style="{ width: barWidth(p.preco_medio) + '%' }" />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">Sem dados suficientes</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
  ordem:   { type: String,  default: 'mais_barato' },
})

const minP = computed(() => props.data.length ? Math.min(...props.data.map(d => d.preco_medio)) : 0)
const maxP = computed(() => props.data.length ? Math.max(...props.data.map(d => d.preco_medio)) : 1)

function barWidth(preco) {
  const range = maxP.value - minP.value
  if (range === 0) return 50
  if (props.ordem === 'mais_barato') return ((maxP.value - preco) / range * 100)
  return ((preco - minP.value) / range * 100)
}

const fmtR = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const fmtN = v => Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; overflow-x: auto; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

table { width: 100%; border-collapse: collapse; }
thead th { font-size: 11px; font-weight: 500; color: var(--text-3); text-align: left; padding: 0 12px 12px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td { font-size: 13px; color: var(--text-2); padding: 10px 12px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }

.rank { color: var(--text-3); font-size: 12px; }
.name { color: var(--text); font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
.city { color: var(--text-3); font-size: 12px; }
.uf { opacity: .6; }
.val { color: var(--text); font-weight: 600; }
.dim { color: var(--text-3); }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.green { color: var(--green); font-weight: 700; }
.red   { color: var(--red);   font-weight: 700; }

.bar-track { height: 4px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; opacity: .7; transition: width .6s ease; }
.green-fill { background: var(--green); }
.red-fill   { background: var(--red); }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
