<template>
  <div class="card">
    <div v-if="loading" class="skel" style="height:160px" />
    <div v-else-if="data.mes_atual" class="comp-grid">

      <!-- Mês atual -->
      <div class="comp-col">
        <div class="col-label">{{ MESES[(data.mes_atual.mes||1)-1] }} {{ data.mes_atual.ano }}</div>
        <div class="col-valor">{{ fmtR(data.mes_atual.total_valor) }}</div>
        <div class="col-stats">
          <div class="stat"><span class="stat-l">Litros</span><span class="stat-v mono">{{ fmtN(data.mes_atual.total_litros) }} L</span></div>
          <div class="stat"><span class="stat-l">R$/L</span><span class="stat-v mono">{{ data.mes_atual.preco_medio?.toFixed(3) }}</span></div>
          <div class="stat"><span class="stat-l">Veículos</span><span class="stat-v mono">{{ data.mes_atual.qtd_veiculos }}</span></div>
          <div class="stat"><span class="stat-l">Abast.</span><span class="stat-v mono">{{ data.mes_atual.qtd_abastecimentos }}</span></div>
          <div class="stat"><span class="stat-l">Dias</span><span class="stat-v mono">{{ data.mes_atual.dias_com_dados }}</span></div>
        </div>
      </div>

      <!-- Variação -->
      <div class="comp-center" v-if="data.variacao">
        <div class="var-arrow" :class="varClass">{{ varIcon }}</div>
        <div class="var-pct" :class="varClass">
          {{ data.variacao.valor_pct > 0 ? '+' : '' }}{{ data.variacao.valor_pct?.toFixed(1) }}%
        </div>
        <div class="var-abs" :class="varClass">
          {{ data.variacao.valor_abs > 0 ? '+' : '' }}{{ fmtR(data.variacao.valor_abs) }}
        </div>
        <div class="var-label">vs mês anterior</div>
        <div class="var-preco" v-if="data.variacao.preco_abs != null">
          Preço: {{ data.variacao.preco_abs > 0 ? '+' : '' }}R$ {{ data.variacao.preco_abs?.toFixed(4) }}/L
        </div>
      </div>

      <!-- Mês anterior -->
      <div class="comp-col dim" v-if="data.mes_anterior">
        <div class="col-label">{{ MESES[(data.mes_anterior.mes||1)-1] }} {{ data.mes_anterior.ano }}</div>
        <div class="col-valor dim">{{ fmtR(data.mes_anterior.total_valor) }}</div>
        <div class="col-stats">
          <div class="stat"><span class="stat-l">Litros</span><span class="stat-v mono">{{ fmtN(data.mes_anterior.total_litros) }} L</span></div>
          <div class="stat"><span class="stat-l">R$/L</span><span class="stat-v mono">{{ data.mes_anterior.preco_medio?.toFixed(3) }}</span></div>
          <div class="stat"><span class="stat-l">Veículos</span><span class="stat-v mono">{{ data.mes_anterior.qtd_veiculos }}</span></div>
          <div class="stat"><span class="stat-l">Abast.</span><span class="stat-v mono">{{ data.mes_anterior.qtd_abastecimentos }}</span></div>
          <div class="stat"><span class="stat-l">Dias</span><span class="stat-v mono">{{ data.mes_anterior.dias_com_dados }}</span></div>
        </div>
      </div>

    </div>
    <div v-else class="empty">Sem dados para comparação</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

const varClass = computed(() => {
  const pct = props.data?.variacao?.valor_pct
  if (pct == null) return 'neutral'
  if (pct > 2) return 'red'
  if (pct < -2) return 'green'
  return 'neutral'
})

const varIcon = computed(() => {
  const pct = props.data?.variacao?.valor_pct
  if (pct == null) return '→'
  if (pct > 2) return '↑'
  if (pct < -2) return '↓'
  return '→'
})

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.empty { height: 160px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

.comp-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 32px;
  align-items: start;
}

.comp-col { display: flex; flex-direction: column; gap: 8px; }
.comp-col.dim .col-valor { color: var(--text-2); }

.col-label { font-size: 12px; font-weight: 600; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.col-valor { font-size: 28px; font-weight: 700; color: var(--text); letter-spacing: -0.02em; }

.col-stats { display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
.stat { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.stat-l { font-size: 12px; color: var(--text-3); }
.stat-v { font-size: 12px; color: var(--text-2); font-family: 'JetBrains Mono', monospace; }

.comp-center {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 0 8px; min-width: 90px;
}
.var-arrow { font-size: 28px; font-weight: 700; }
.var-pct   { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.var-abs   { font-size: 13px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
.var-label { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; margin-top: 4px; }
.var-preco { font-size: 11px; color: var(--text-3); font-family: 'JetBrains Mono', monospace; }

.green   { color: var(--green); }
.red     { color: var(--red); }
.neutral { color: var(--text-2); }

.mono { font-family: 'JetBrains Mono', monospace; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

@media (max-width: 700px) {
  .comp-grid { grid-template-columns: 1fr; }
  .comp-center { flex-direction: row; gap: 12px; padding: 8px 0; }
}
</style>
