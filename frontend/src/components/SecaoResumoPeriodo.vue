<template>
  <div class="wrap">

    <!-- Cabeçalho com toggle de período -->
    <div class="periodo-header">
      <div class="periodo-toggles">
        <button
          v-for="p in PERIODOS"
          :key="p.meses"
          class="periodo-btn"
          :class="{ active: meses === p.meses }"
          @click="selecionar(p.meses)"
        >{{ p.label }}</button>
      </div>
      <div class="periodo-info" v-if="!loading && data.meses_incluidos?.length">
        {{ data.meses_incluidos[0] }} → {{ data.meses_incluidos.at(-1) }}
        <span v-if="data.meses_comparativo?.length" class="dim">
          · vs {{ data.meses_comparativo[0] }}→{{ data.meses_comparativo.at(-1) }}
        </span>
      </div>
    </div>

    <!-- Banner de totais do período -->
    <div class="total-banner" v-if="!loading && data.total">
      <div class="total-bloco">
        <div class="total-label">Total gasto no período</div>
        <div class="total-valor">{{ fmtR(data.total.total_valor) }}</div>
        <div class="total-sub" v-if="data.total.var_pct != null">
          <span :class="data.total.var_pct > 0 ? 'red' : 'green'">
            {{ data.total.var_pct > 0 ? '↑' : '↓' }} {{ Math.abs(data.total.var_pct).toFixed(1) }}%
          </span>
          vs período anterior
        </div>
      </div>
      <div class="total-sep" />
      <div class="total-bloco">
        <div class="total-label">Total litros</div>
        <div class="total-valor mono">{{ fmtN(data.total.total_litros) }} L</div>
        <div class="total-sub" v-if="data.total.total_litros_ant">
          ant: {{ fmtN(data.total.total_litros_ant) }} L
        </div>
      </div>
      <div class="total-sep" />
      <div class="total-bloco">
        <div class="total-label">Preço médio/L (mix)</div>
        <div class="total-valor mono">R$ {{ data.total.preco_medio?.toFixed(4) ?? '—' }}</div>
        <div class="total-sub dim">todos os combustíveis</div>
      </div>
    </div>
    <div v-else-if="loading" class="total-banner skel" style="height:80px" />

    <!-- Cards por combustível -->
    <div v-if="loading" class="comb-grid">
      <div v-for="i in 4" :key="i" class="comb-card skel" style="height:140px" />
    </div>

    <div v-else-if="!combustiveis.length" class="empty">Sem dados para o período</div>

    <div v-else class="comb-grid">
      <div
        v-for="c in combustiveis"
        :key="c.combustivel"
        class="comb-card"
      >
        <!-- Nome + badge de variação -->
        <div class="comb-top">
          <div class="comb-nome">{{ c.combustivel }}</div>
          <span
            v-if="c.var_pct != null"
            class="var-badge"
            :class="c.var_pct > 0 ? 'var-up' : 'var-down'"
          >
            {{ c.var_pct > 0 ? '↑' : '↓' }} {{ Math.abs(c.var_pct).toFixed(1) }}%
          </span>
        </div>

        <!-- Métricas principais -->
        <div class="comb-metricas">
          <div class="metrica">
            <div class="metrica-label">Litros</div>
            <div class="metrica-valor mono">{{ fmtN(c.total_litros) }}</div>
            <div class="metrica-ant dim" v-if="c.total_litros_ant != null">
              ant: {{ fmtN(c.total_litros_ant) }}
              <span :class="c.var_litros > 0 ? 'red' : 'green'" v-if="c.var_litros != null">
                ({{ c.var_litros > 0 ? '+' : '' }}{{ fmtN(c.var_litros) }})
              </span>
            </div>
          </div>

          <div class="metrica">
            <div class="metrica-label">Valor</div>
            <div class="metrica-valor">{{ fmtR(c.total_valor) }}</div>
            <div class="metrica-ant dim" v-if="c.total_valor_ant != null">
              ant: {{ fmtR(c.total_valor_ant) }}
            </div>
          </div>

          <div class="metrica">
            <div class="metrica-label">R$/L</div>
            <div class="metrica-valor mono" :class="precoClass(c.var_preco)">
              {{ c.preco_litro?.toFixed(4) ?? '—' }}
            </div>
            <div class="metrica-ant dim" v-if="c.preco_litro_ant != null">
              ant: {{ c.preco_litro_ant.toFixed(4) }}
              <span :class="c.var_preco > 0 ? 'red' : 'green'" v-if="c.var_preco != null">
                ({{ c.var_preco > 0 ? '+' : '' }}{{ c.var_preco.toFixed(4) }})
              </span>
            </div>
          </div>

          <div class="metrica">
            <div class="metrica-label">Abastec.</div>
            <div class="metrica-valor mono">{{ c.qtd_abastecimentos }}</div>
          </div>
        </div>

        <!-- Mini barra de proporção -->
        <div class="comb-bar-track">
          <div
            class="comb-bar-fill"
            :style="{ width: propPct(c.total_litros) + '%' }"
          />
        </div>
        <div class="comb-pct dim">{{ propPct(c.total_litros).toFixed(0) }}% dos litros totais</div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { fetchResumoPeriodo } from '../api/combustivel.js'

const props = defineProps({
  filtros: { type: Object, default: () => ({}) },
})

const PERIODOS = [
  { meses: 1, label: 'Mês anterior' },
  { meses: 3, label: 'Últimos 3 meses' },
  { meses: 6, label: 'Últimos 6 meses' },
]

const meses   = ref(1)
const data    = ref({})
const loading = ref(true)

const combustiveis = computed(() => data.value?.combustiveis ?? [])

const totalLitros = computed(() => combustiveis.value.reduce((s, c) => s + (c.total_litros || 0), 0))
const propPct = litros => totalLitros.value > 0 ? Math.max(4, litros / totalLitros.value * 100) : 0

const precoClass = varPreco => varPreco > 0 ? 'red' : varPreco < 0 ? 'green' : ''

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

async function carregar() {
  loading.value = true
  try {
    data.value = await fetchResumoPeriodo({ meses: meses.value, ...props.filtros })
  } finally {
    loading.value = false
  }
}

function selecionar(n) {
  meses.value = n
  carregar()
}

watch(() => props.filtros, carregar, { deep: true })
onMounted(carregar)
</script>

<style scoped>
.wrap { display: flex; flex-direction: column; gap: 16px; }

/* Toggle de período */
.periodo-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.periodo-toggles { display: flex; gap: 6px; }
.periodo-btn {
  background: transparent; border: 1px solid var(--border); color: var(--text-3);
  font-size: 12px; font-weight: 500; padding: 6px 14px; border-radius: 8px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all 0.15s;
}
.periodo-btn:hover { border-color: var(--text-3); color: var(--text-2); }
.periodo-btn.active { border-color: var(--accent); color: var(--accent); background: rgba(249,115,22,0.08); font-weight: 600; }
.periodo-info { font-size: 11px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }

/* Banner de totais */
.total-banner {
  display: flex; align-items: center; gap: 0;
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 18px 28px; flex-wrap: wrap; gap: 24px;
}
.total-bloco { display: flex; flex-direction: column; gap: 4px; }
.total-sep { width: 1px; background: var(--border-subtle); align-self: stretch; flex-shrink: 0; }
.total-label { font-size: 11px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.total-valor { font-size: 22px; font-weight: 700; color: var(--text); letter-spacing: -0.02em; }
.total-valor.mono { font-family: 'JetBrains Mono', monospace; font-size: 20px; }
.total-sub { font-size: 12px; color: var(--text-3); }

/* Grid de combustíveis */
.comb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }

.comb-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 18px 20px; display: flex; flex-direction: column; gap: 12px;
  transition: border-color 0.15s;
}
.comb-card:hover { border-color: var(--accent); }

.comb-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.comb-nome { font-size: 13px; font-weight: 600; color: var(--text); line-height: 1.3; }

.var-badge {
  display: inline-flex; align-items: center;
  font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px;
  white-space: nowrap; flex-shrink: 0;
}
.var-up   { background: rgba(239,68,68,.12);  color: var(--red);   border: 1px solid rgba(239,68,68,.25); }
.var-down { background: rgba(34,197,94,.12);  color: var(--green); border: 1px solid rgba(34,197,94,.25); }

/* Métricas em grid 2×2 */
.comb-metricas { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 12px; }
.metrica { display: flex; flex-direction: column; gap: 2px; }
.metrica-label { font-size: 10px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.metrica-valor { font-size: 15px; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }
.metrica-valor.mono { font-family: 'JetBrains Mono', monospace; font-size: 14px; }
.metrica-ant { font-size: 10px; margin-top: 1px; }

/* Barra de proporção */
.comb-bar-track { height: 3px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.comb-bar-fill  { height: 100%; background: var(--accent); border-radius: 2px; opacity: .7; transition: width .6s ease; }
.comb-pct { font-size: 10px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }

.dim   { color: var(--text-3); }
.red   { color: var(--red); }
.green { color: var(--green); }
.mono  { font-family: 'JetBrains Mono', monospace; }

.empty { height: 120px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel  { background: var(--border); border-radius: 10px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
