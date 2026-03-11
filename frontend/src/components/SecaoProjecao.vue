<template>
  <div class="proj-grid">

    <!-- Mês anterior -->
    <div class="card">
      <div class="card-label">Mês anterior</div>
      <div class="card-value">
        <span v-if="loading" class="skel" style="width:130px;height:32px;display:block" />
        <span v-else>{{ fmt(kpis.valor_mes_anterior) }}</span>
      </div>
      <div class="card-sub" v-if="!loading">{{ fmtL(kpis.litros_mes_anterior) }} L consumidos</div>
    </div>

    <!-- Realizado -->
    <div class="card">
      <div class="card-label">Realizado no mês</div>
      <div class="card-value">
        <span v-if="loading" class="skel" style="width:130px;height:32px;display:block" />
        <span v-else>{{ fmt(kpis.valor_mes_atual) }}</span>
      </div>
      <div class="card-sub" v-if="!loading">
        até dia {{ kpis.dia_calendario }} · {{ fmtL(kpis.litros_mes_atual) }} L
      </div>
    </div>

    <!-- Projeção -->
    <div class="card accent-card">
      <div class="card-label">Projeção de fechamento</div>
      <div class="card-value accent">
        <span v-if="loading" class="skel" style="width:130px;height:32px;display:block" />
        <span v-else>{{ fmt(kpis.projecao_valor) }}</span>
      </div>
      <div class="card-sub" v-if="!loading">{{ fmtL(kpis.projecao_litros) }} L projetados</div>
    </div>

    <!-- Progresso -->
    <div class="card">
      <div class="card-label">Progresso do mês</div>
      <div class="card-value mono" v-if="!loading">{{ pct }}%</div>
      <div class="card-value skel" v-else style="width:70px;height:32px;display:block" />
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: loading ? '0%' : pct + '%' }" />
      </div>
      <div class="card-sub" v-if="!loading">dia {{ kpis.dia_calendario }} de {{ kpis.total_dias_mes }} · {{ kpis.dias_com_dados }} com dados</div>
    </div>

    <!-- Tendência -->
    <div class="card status-card" :class="statusColor">
      <div class="card-label">Tendência vs mês anterior</div>
      <div class="status-row" v-if="!loading">
        <span class="status-icon">{{ icon }}</span>
        <span class="status-text" :class="statusColor">{{ kpis.status }}</span>
      </div>
      <div class="skel" v-else style="width:100px;height:32px;margin:8px 0" />
      <div class="card-sub" v-if="!loading">
        {{ kpis.variacao_valor > 0 ? '+' : '' }}{{ fmt(kpis.variacao_valor) }}
        ({{ kpis.variacao_pct > 0 ? '+' : '' }}{{ kpis.variacao_pct?.toFixed(1) }}%)
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  kpis:    { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const fmt  = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtL = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'

const pct = computed(() => {
  const { dia_calendario: d, total_dias_mes: t } = props.kpis
  return d && t ? Math.min(100, Math.round(d / t * 100)) : 0
})

const icon        = computed(() => props.kpis.status === 'ALTA' ? '↑' : props.kpis.status === 'BAIXA' ? '↓' : '→')
const statusColor = computed(() => props.kpis.status === 'ALTA' ? 'red' : props.kpis.status === 'BAIXA' ? 'green' : 'neutral')
</script>

<style scoped>
.proj-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.accent-card { border-color: rgba(249,115,22,0.25); background: rgba(249,115,22,0.04); }
.card-label { font-size: 12px; font-weight: 500; color: var(--text-2); }
.card-value { font-size: 28px; font-weight: 700; color: var(--text); letter-spacing: -0.02em; line-height: 1; margin: 4px 0; }
.card-value.accent { color: var(--accent); }
.card-value.mono { font-family: 'JetBrains Mono', monospace; }
.card-sub { font-size: 12px; color: var(--text-3); }

.progress-track {
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
  margin: 4px 0;
}
.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 1s ease;
}

.status-row { display: flex; align-items: center; gap: 10px; margin: 4px 0; }
.status-icon { font-size: 20px; color: var(--text-2); }
.status-text { font-size: 22px; font-weight: 700; letter-spacing: -0.01em; }
.status-text.green { color: var(--green); }
.status-text.red   { color: var(--red); }
.status-text.neutral { color: var(--text-2); }

.skel { background: var(--border); border-radius: 6px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }

@media (max-width: 1200px) { .proj-grid { grid-template-columns: repeat(3,1fr); } }
@media (max-width: 900px)  { .proj-grid { grid-template-columns: repeat(2,1fr); } }
</style>
