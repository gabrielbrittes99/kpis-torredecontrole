<template>
  <div class="variacao-wrap">
    <div v-if="loading" class="skel" style="height:220px" />
    <div v-else-if="!matrix.length" class="empty">Sem dados suficientes para análise</div>
    <div v-else class="matrix">
      <!-- Cabeçalho -->
      <div class="matrix-head">
        <div class="cell-comb">Combustível</div>
        <div class="cell-avg">Preço Médio</div>
        <template v-for="mes in meses" :key="mes">
          <div class="cell-mes">{{ mes }}</div>
        </template>
      </div>

      <!-- Linhas por combustível -->
      <div
        v-for="row in matrix"
        :key="row.combustivel"
        class="matrix-row"
      >
        <!-- Nome + dot -->
        <div class="cell-comb">
          <span class="comb-dot" :style="{ background: combColor(row.combustivel) }"></span>
          <span class="comb-nome">{{ row.combustivel }}</span>
        </div>

        <!-- Preço médio geral do período -->
        <div class="cell-avg mono">
          <span v-if="row.preco_medio_geral">R$ {{ row.preco_medio_geral.toFixed(3) }}</span>
          <span v-else class="dim">—</span>
        </div>

        <!-- Célula por mês -->
        <template v-for="mes in meses" :key="mes">
          <div class="cell-mes-data">
            <template v-if="row.meses[mes]">
              <span class="preco mono">R$ {{ row.meses[mes].preco.toFixed(3) }}</span>
              <span
                v-if="row.meses[mes].var != null"
                class="var-badge"
                :class="varClass(row.meses[mes].var)"
              >
                {{ row.meses[mes].var > 0 ? '+' : '' }}{{ row.meses[mes].var.toFixed(1) }}%
              </span>
              <span v-else class="var-badge neutral">—</span>
            </template>
            <span v-else class="dim">—</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const FUEL_ORDER = ['Diesel', 'Gasolina', 'Álcool', 'Arla']
const FUEL_COLORS = {
  'Diesel': '#C41230', 'Gasolina': '#3b82f6',
  'Álcool': '#10b981', 'Arla': '#8b5cf6',
}
const combColor = c => FUEL_COLORS[c] ?? '#94a3b8'

const MES_LABEL = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES_LABEL[+m-1]}/${y.slice(2)}` }

// Últimos N meses únicos presentes nos dados
const meses = computed(() => {
  const all = [...new Set(props.data.map(r => r.ano_mes))].sort()
  return all.slice(-4).map(fmtMes)
})

const mesesRaw = computed(() => {
  const all = [...new Set(props.data.map(r => r.ano_mes))].sort()
  return all.slice(-4)
})

// Monta a matrix: { combustivel, preco_medio_geral, meses: { 'Jan/25': { preco, var } } }
const matrix = computed(() => {
  // Agrupa por combustivel
  const byFuel = {}
  for (const r of props.data) {
    if (!byFuel[r.combustivel]) byFuel[r.combustivel] = []
    byFuel[r.combustivel].push(r)
  }

  const result = []
  const fuels = FUEL_ORDER.filter(f => byFuel[f]).concat(
    Object.keys(byFuel).filter(f => !FUEL_ORDER.includes(f))
  )

  for (const fuel of fuels) {
    const arr = byFuel[fuel] ?? []
    // Preço médio geral = média dos preços do período
    const precos = arr.map(r => r.preco_medio).filter(Boolean)
    const preco_medio_geral = precos.length ? precos.reduce((s, v) => s + v, 0) / precos.length : null

    // Mapa de mes → { preco, var }
    const mesMap = {}
    for (const r of arr) {
      mesMap[r.ano_mes] = { preco: r.preco_medio, var: r.variacao_pct }
    }

    const mesesObj = {}
    for (const m of mesesRaw.value) {
      const label = fmtMes(m)
      mesesObj[label] = mesMap[m] ? { preco: mesMap[m].preco, var: mesMap[m].var } : null
    }

    result.push({ combustivel: fuel, preco_medio_geral, meses: mesesObj })
  }
  return result
})

const varClass = pct => {
  if (pct > 1)  return 'up'
  if (pct < -1) return 'down'
  return 'neutral'
}
</script>

<style scoped>
.variacao-wrap { width: 100%; overflow-x: auto; }

.matrix { display: flex; flex-direction: column; gap: 0; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }

.matrix-head {
  display: grid;
  grid-template-columns: 160px 120px repeat(4, 1fr);
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}
.matrix-row {
  display: grid;
  grid-template-columns: 160px 120px repeat(4, 1fr);
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.1s;
}
.matrix-row:last-child { border-bottom: none; }
.matrix-row:hover { background: #fafafa; }

/* células cabeçalho */
.matrix-head > div {
  padding: 10px 14px;
  font-size: 10px; font-weight: 800; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.07em;
  text-align: center;
}
.matrix-head .cell-comb { text-align: left; }
.matrix-head .cell-avg  { text-align: center; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }

/* células dados */
.cell-comb {
  padding: 14px; display: flex; align-items: center; gap: 8px;
}
.comb-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.comb-nome {
  font-size: 13px; font-weight: 700; color: #1e293b;
}

.cell-avg {
  padding: 14px; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #0f172a;
  border-left: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9;
}

.cell-mes {
  padding: 10px 14px; text-align: center;
}

.cell-mes-data {
  padding: 12px 14px;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  border-left: 1px solid #f8fafc;
}

.preco {
  font-size: 13px; font-weight: 600; color: #1e293b;
  font-family: 'JetBrains Mono', monospace;
}

.var-badge {
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 10px;
  font-family: 'JetBrains Mono', monospace; white-space: nowrap;
}
.var-badge.up      { background: #fef2f2; color: #dc2626; border: 1px solid rgba(220,38,38,.12); }
.var-badge.down    { background: #ecfdf5; color: #059669; border: 1px solid rgba(5,150,105,.12); }
.var-badge.neutral { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }

.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: #94a3b8; font-size: 12px; }

.empty { height: 160px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
