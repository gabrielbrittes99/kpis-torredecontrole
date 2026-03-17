<template>
  <div class="card card-posto">
    <div class="card-header">
      <div class="card-title">{{ ordem === 'mais_barato' ? 'Melhores Oportunidades' : 'Maiores Custos por Posto' }}</div>
      <div class="card-hint">mínimo 3 abastecimentos · por preço médio/L</div>
    </div>
    <div v-if="loading" class="skel" style="height:280px" />
    <div v-else-if="data.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:32px">#</th>
            <th>Posto</th>
            <th>Cidade</th>
            <th class="right">R$/L médio</th>
            <th class="right">Total R$</th>
            <th class="right">Litros</th>
            <th style="width:70px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in data" :key="p.razao_social_posto + i">
            <td class="rank mono">{{ i + 1 }}</td>
            <td class="name-col">
              <span class="name">{{ p.razao_social_posto || '—' }}</span>
            </td>
            <td class="city-col">
              <span class="city">{{ p.cidade_posto }}</span>
              <span class="uf-tag">{{ p.uf_posto }}</span>
            </td>
            <td class="right mono" :class="i === 0 ? (ordem === 'mais_barato' ? 'green' : 'red') : 'val'">
              R$ {{ p.preco_medio.toFixed(3) }}
            </td>
            <td class="right mono dim">{{ fmtR(p.total_valor) }}</td>
            <td class="right mono dim">{{ fmtN(p.total_litros) }}</td>
            <td>
              <div class="bar-track">
                <div class="bar-fill" :class="ordem === 'mais_barato' ? 'green-fill' : 'red-fill'"
                  :style="{ width: barWidth(p.preco_medio) + '%' }" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="empty">Sem dados de postos suficientes</div>
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

.rank { color: #94a3b8; font-size: 12px; }
.name-col { max-width: 180px; }
.name { display: block; font-weight: 600; color: #0f172a; overflow: hidden; text-overflow: ellipsis; }
.city-col { font-size: 12px; }
.city { color: #64748b; margin-right: 4px; }
.uf-tag { font-size: 10px; font-weight: 700; color: #94a3b8; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }

.val { font-weight: 600; color: #0f172a; }
.dim { color: #94a3b8; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.green { color: #10b981; font-weight: 700; }
.red   { color: #ef4444; font-weight: 700; }

.bar-track { height: 4px; background: #f1f5f9; border-radius: 2px; overflow: hidden; width: 60px; margin-left: auto; }
.bar-fill { height: 100%; border-radius: 2px; transition: width .6s ease; }
.green-fill { background: #10b981; }
.red-fill   { background: #ef4444; }

.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
