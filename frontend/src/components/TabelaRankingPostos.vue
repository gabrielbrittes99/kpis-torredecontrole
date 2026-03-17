<template>
  <div class="table-wrap-inner">
    <div v-if="loading" class="skel" style="height:280px" />
    <div v-else-if="data.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:32px">#</th>
            <th>Posto</th>
            <th>Cidade / UF</th>
            <th class="right">R$/L médio</th>
            <th class="right" :class="ordem === 'maior_custo' ? 'col-highlight' : ''">Total R$</th>
            <th class="right" :class="ordem === 'maior_volume' ? 'col-highlight' : ''">Litros</th>
            <th class="right">Abast.</th>
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
            <td class="right mono" :class="ordem === 'mais_caro' && i === 0 ? 'red' : 'val'">
              R$ {{ p.preco_medio.toFixed(3) }}
            </td>
            <td class="right mono" :class="ordem === 'maior_custo' ? (i === 0 ? 'red bold' : 'val') : 'dim'">
              {{ fmtR(p.total_valor) }}
            </td>
            <td class="right mono" :class="ordem === 'maior_volume' ? (i === 0 ? 'blue bold' : 'val') : 'dim'">
              {{ fmtN(p.total_litros) }}
            </td>
            <td class="right mono dim">{{ p.qtd_abastecimentos }}</td>
            <td>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :class="barFillClass"
                  :style="{ width: barWidth(p) + '%' }"
                />
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

// Valor que determina o tamanho da barra conforme o tipo de ordenação
function metricValue(p) {
  if (props.ordem === 'maior_volume') return p.total_litros
  if (props.ordem === 'maior_custo')  return p.total_valor
  return p.preco_medio
}

const maxMetric = computed(() => props.data.length ? Math.max(...props.data.map(metricValue)) : 1)

function barWidth(p) {
  const m = metricValue(p)
  return maxMetric.value > 0 ? Math.round(m / maxMetric.value * 100) : 0
}

const barFillClass = computed(() => {
  if (props.ordem === 'mais_barato') return 'green-fill'
  if (props.ordem === 'maior_volume') return 'blue-fill'
  return 'red-fill'
})

const fmtR = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const fmtN = v => Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
</script>

<style scoped>
.table-wrap-inner { width: 100%; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 10px;
  border-bottom: 1px solid #f1f5f9; white-space: nowrap;
}
.col-highlight { color: #1e293b; }
th.right, td.right { text-align: right; }
tbody td { font-size: 13px; color: #334155; padding: 10px 10px; border-bottom: 1px solid #f8fafc; white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: #fafafa; }

.rank { color: #94a3b8; font-size: 12px; }
.name-col { max-width: 200px; }
.name { display: block; font-weight: 600; color: #0f172a; overflow: hidden; text-overflow: ellipsis; }
.city-col { font-size: 12px; }
.city { color: #64748b; margin-right: 4px; }
.uf-tag { font-size: 10px; font-weight: 700; color: #94a3b8; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }

.val  { font-weight: 600; color: #1e293b; }
.bold { font-weight: 700; }
.dim  { color: #94a3b8; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.green { color: #10b981; font-weight: 700; }
.blue  { color: #2563eb; font-weight: 700; }
.red   { color: #ef4444; font-weight: 700; }

.bar-track { height: 5px; background: #f1f5f9; border-radius: 3px; overflow: hidden; width: 60px; margin-left: auto; }
.bar-fill { height: 100%; border-radius: 3px; transition: width .6s ease; }
.green-fill { background: #10b981; }
.blue-fill  { background: #3b82f6; }
.red-fill   { background: #ef4444; }

.empty { height: 120px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
