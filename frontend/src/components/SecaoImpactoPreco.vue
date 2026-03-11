<template>
  <div class="wrap">

    <!-- ══ BLOCO 1: histórico real (meses fechados) ══════════════════ -->
    <div class="bloco-header">
      <div class="bloco-title">Meses fechados · custo real por combustível</div>
    </div>

    <div v-if="lHist" class="skel" style="height:120px" />
    <div v-else-if="!histMeses.length" class="empty-sm">Sem histórico disponível</div>
    <div v-else class="table-wrap">
      <table class="hist-table">
        <thead>
          <tr>
            <th>Combustível</th>
            <th v-for="m in histMeses" :key="m" class="right">{{ fmtMes(m) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in histTop" :key="s.combustivel">
            <td class="comb-nome">{{ s.combustivel }}</td>
            <td v-for="m in histMeses" :key="m" class="right">
              <template v-if="getDado(s, m)">
                <div class="cell-main">{{ fmtR(getDado(s, m).total_valor) }}</div>
                <div class="cell-sub">{{ fmtN(getDado(s, m).total_litros) }} L · R$ {{ getDado(s, m).preco_medio_litro?.toFixed(3) }}/L</div>
              </template>
              <span v-else class="dim">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══ BLOCO 2: simulador (mês atual) ════════════════════════════ -->
    <div class="bloco-header">
      <div>
        <div class="bloco-title">{{ mesAtualLabel }} · projeção de gasto</div>
        <div class="bloco-hint">Altere o preço e veja quanto vai gastar, baseado na média de litros abaixo</div>
      </div>
      <div class="toggle-wrap">
        <span class="toggle-label">Média dos últimos</span>
        <div class="toggle-group">
          <button v-for="n in [3,6,12]" :key="n" class="toggle-btn" :class="{active: mesesHist===n}" @click="mesesHist=n; carregarSim()">{{ n }}m</button>
        </div>
      </div>
    </div>

    <div v-if="lSim" class="cards-grid">
      <div v-for="i in 3" :key="i" class="skel" style="height:150px" />
    </div>
    <div v-else-if="!rows.length" class="empty-sm">Sem dados para projeção</div>
    <template v-else>
      <!-- Banner de impacto total -->
      <div class="banner-total" v-if="totalDelta !== 0" :class="totalDelta > 0 ? 'red' : 'green'">
        <span class="banner-label">Impacto total simulado:</span>
        <span class="banner-valor">{{ totalDelta > 0 ? '+' : '' }}{{ fmtR(totalDelta) }}/mês</span>
        <span class="banner-pct">({{ totalDeltaPct > 0 ? '+' : '' }}{{ totalDeltaPct.toFixed(1) }}% vs média histórica)</span>
      </div>

      <!-- Cards por combustível -->
      <div class="cards-grid">
        <div v-for="(row, idx) in rows" :key="row.combustivel" class="fuel-card">
          <div class="fuel-header">
            <div class="fuel-nome">{{ row.combustivel }}</div>
            <div class="fuel-volume mono">{{ fmtN(row.media_litros_mes) }} L/mês médio</div>
          </div>

          <div class="preco-row">
            <div class="preco-bloco">
              <div class="preco-label">Preço atual</div>
              <div class="preco-valor mono">R$ {{ row.preco_atual?.toFixed(4) }}</div>
            </div>
            <div class="preco-seta">→</div>
            <div class="preco-bloco">
              <div class="preco-label">Simular</div>
              <div class="input-wrap">
                <span class="input-prefix">R$</span>
                <input
                  type="number" step="0.01" min="0"
                  v-model.number="precosSim[idx]"
                  class="price-input"
                />
                <span class="input-suffix">/L</span>
              </div>
            </div>
          </div>

          <div class="impacto-box" :class="delta(idx) > 0 ? 'red' : delta(idx) < 0 ? 'green' : 'neutral'">
            <div class="impacto-conta mono" v-if="delta(idx) !== 0">
              {{ deltaPreco(idx) > 0 ? '+' : '' }}R$ {{ Math.abs(deltaPreco(idx)).toFixed(4) }}/L
              × {{ fmtN(row.media_litros_mes) }} L
              = <strong>{{ delta(idx) > 0 ? '+' : '' }}{{ fmtR(delta(idx)) }}/mês</strong>
            </div>
            <div class="impacto-conta dim" v-else>Sem variação · altere o preço acima</div>
          </div>
        </div>
      </div>

      <div class="base-info">Base: {{ simData.meses_base?.join(' · ') }}</div>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { fetchImpactoPreco, fetchHistoricoMensal } from '../api/combustivel.js'

const props = defineProps({
  filtros: { type: Object, default: () => ({}) },
})

// ── Histórico real ─────────────────────────────────────────
const hist    = ref({})
const lHist   = ref(true)

const MES_LABEL = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
const fmtMes = s => { const [y, m] = s.split('-'); return `${MES_LABEL[+m-1]}/${y.slice(2)}` }

const hoje = new Date()
const mesAtualStr = `${hoje.getFullYear()}-${String(hoje.getMonth()+1).padStart(2,'0')}`
const mesAtualLabel = computed(() => `${MES_LABEL[hoje.getMonth()]}/${String(hoje.getFullYear()).slice(2)}`)

// Últimos 3 meses fechados (exclui o mês atual)
const histMeses = computed(() =>
  (hist.value.meses ?? []).filter(m => m < mesAtualStr).slice(-3)
)

// Top 5 combustíveis por volume total nos meses exibidos
const histTop = computed(() => {
  const series = hist.value.series ?? []
  return [...series]
    .map(s => ({
      ...s,
      _total: s.dados.filter(d => histMeses.value.includes(d.ano_mes))
                     .reduce((acc, d) => acc + (d.total_litros ?? 0), 0),
    }))
    .filter(s => s._total > 0)
    .sort((a, b) => b._total - a._total)
    .slice(0, 5)
})

const getDado = (serie, mes) => serie.dados.find(d => d.ano_mes === mes)

async function carregarHist() {
  lHist.value = true
  try {
    hist.value = await fetchHistoricoMensal(props.filtros, true)
  } finally {
    lHist.value = false
  }
}

// ── Simulador mês atual ─────────────────────────────────────
const simData   = ref({})
const lSim      = ref(true)
const mesesHist = ref(3)
const precosSim = ref([])

const rows = computed(() => simData.value?.combustiveis ?? [])

watch(rows, (newRows) => {
  precosSim.value = newRows.map(r => +r.preco_atual.toFixed(4))
}, { immediate: true })

const deltaPreco   = idx => (precosSim.value[idx] ?? 0) - (rows.value[idx]?.preco_atual ?? 0)
const delta        = idx => deltaPreco(idx) * (rows.value[idx]?.media_litros_mes ?? 0)
const totalDelta   = computed(() => rows.value.reduce((s, _, i) => s + delta(i), 0))
const totalDeltaPct = computed(() => {
  const base = simData.value.total?.custo_hist_mensal ?? 0
  return base > 0 ? totalDelta.value / base * 100 : 0
})

async function carregarSim() {
  lSim.value = true
  try {
    simData.value = await fetchImpactoPreco({ meses_historico: mesesHist.value, ...props.filtros })
  } finally {
    lSim.value = false
  }
}

// ── Formatação ──────────────────────────────────────────────
const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

// ── Watchers ────────────────────────────────────────────────
watch(() => props.filtros, () => { carregarHist(); carregarSim() }, { deep: true })

onMounted(() => { carregarHist(); carregarSim() })
</script>

<style scoped>
.wrap { display: flex; flex-direction: column; gap: 16px; }

/* Cabeçalhos de bloco */
.bloco-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
  padding-top: 8px; border-top: 1px solid var(--border-subtle);
}
.bloco-header:first-child { border-top: none; padding-top: 0; }
.bloco-title { font-size: 13px; font-weight: 600; color: var(--text-2); }
.bloco-hint  { font-size: 11px; color: var(--text-3); margin-top: 3px; }

.toggle-wrap { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.toggle-label { font-size: 11px; color: var(--text-3); }
.toggle-group { display: flex; gap: 4px; }
.toggle-btn {
  background: transparent; border: 1px solid var(--border); color: var(--text-3);
  font-size: 11px; font-weight: 500; padding: 4px 10px; border-radius: 6px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.15s;
}
.toggle-btn:hover { border-color: var(--text-3); color: var(--text-2); }
.toggle-btn.active { border-color: var(--accent); color: var(--accent); background: rgba(249,115,22,.08); }

/* Tabela histórica */
.table-wrap { overflow-x: auto; }
.hist-table { width: 100%; border-collapse: collapse; }
.hist-table thead th {
  font-size: 11px; font-weight: 500; color: var(--text-3);
  text-align: left; padding: 0 12px 10px;
  border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
}
.hist-table th.right, .hist-table td.right { text-align: right; }
.hist-table tbody tr:hover { background: var(--surface-hover); }
.hist-table tbody td {
  padding: 10px 12px; border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle; white-space: nowrap;
}
.hist-table tbody tr:last-child td { border-bottom: none; }
.comb-nome { font-size: 13px; font-weight: 500; color: var(--text); }
.cell-main { font-size: 13px; font-weight: 600; color: var(--text); font-family: 'JetBrains Mono', monospace; }
.cell-sub  { font-size: 10px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }

/* Banner total simulação */
.banner-total {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 20px; border-radius: 10px; border: 1px solid; flex-wrap: wrap;
}
.banner-total.red   { background: rgba(239,68,68,.06); border-color: rgba(239,68,68,.25); }
.banner-total.green { background: rgba(34,197,94,.06); border-color: rgba(34,197,94,.25); }
.banner-label { font-size: 12px; color: var(--text-3); }
.banner-valor { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.banner-total.red   .banner-valor { color: var(--red); }
.banner-total.green .banner-valor { color: var(--green); }
.banner-pct { font-size: 12px; color: var(--text-3); }

/* Cards do simulador */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.fuel-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 18px; display: flex; flex-direction: column; gap: 14px;
}

.fuel-header { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.fuel-nome   { font-size: 14px; font-weight: 600; color: var(--text); }
.fuel-volume { font-size: 11px; color: var(--text-3); }

.preco-row   { display: flex; align-items: flex-end; gap: 12px; }
.preco-bloco { display: flex; flex-direction: column; gap: 4px; }
.preco-label { font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.preco-valor { font-size: 15px; font-weight: 600; color: var(--text-2); font-family: 'JetBrains Mono', monospace; }
.preco-seta  { font-size: 14px; color: var(--text-3); padding-bottom: 4px; }

.input-wrap   { display: flex; align-items: center; gap: 4px; }
.input-prefix { font-size: 12px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }
.input-suffix { font-size: 11px; color: var(--text-3); }
.price-input {
  width: 80px; text-align: right;
  background: var(--bg); border: 1px solid var(--border); color: var(--text);
  font-size: 14px; font-weight: 600; font-family: 'JetBrains Mono', monospace;
  padding: 5px 8px; border-radius: 7px; outline: none; transition: border-color 0.15s;
}
.price-input:focus { border-color: var(--accent); }
.price-input::-webkit-inner-spin-button,
.price-input::-webkit-outer-spin-button { opacity: 0.4; }

.impacto-box { padding: 12px 14px; border-radius: 8px; border: 1px solid; }
.impacto-box.red     { background: rgba(239,68,68,.06);  border-color: rgba(239,68,68,.2); }
.impacto-box.green   { background: rgba(34,197,94,.06);  border-color: rgba(34,197,94,.2); }
.impacto-box.neutral { background: var(--bg);            border-color: var(--border); }
.impacto-conta { font-size: 12px; line-height: 1.5; }
.impacto-box.red   .impacto-conta { color: var(--red); }
.impacto-box.green .impacto-conta { color: var(--green); }
.impacto-conta strong { font-size: 15px; font-weight: 700; }
.impacto-conta.dim { color: var(--text-3); font-family: 'Inter', sans-serif; font-size: 12px; }

.base-info { font-size: 11px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }

.mono  { font-family: 'JetBrains Mono', monospace; }
.dim   { color: var(--text-3); }
.empty-sm { height: 80px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 12px; }
.skel  { background: var(--border); border-radius: 10px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
