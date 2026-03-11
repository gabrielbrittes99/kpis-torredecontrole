<template>
  <div class="card">
    <div v-if="loading" class="skel" style="height:200px" />
    <template v-else>
      <div class="header-row">
        <div>
          <div class="card-title">Combustíveis comuns vs premium/aditivados</div>
          <div class="card-hint">Gasto extra em relação ao combustível equivalente mais barato</div>
        </div>
        <div v-if="data.gasto_premium_total > 0" class="premium-total">
          <div class="pt-label">Gasto premium total</div>
          <div class="pt-value">{{ fmtR(data.gasto_premium_total) }}</div>
        </div>
      </div>

      <div class="grupos" v-if="data.grupos?.length">
        <div v-for="g in data.grupos" :key="g.nome" class="grupo-row">
          <div class="grupo-info">
            <span class="grupo-badge" :class="g.categoria">{{ g.categoria === 'premium' ? 'Premium' : 'Comum' }}</span>
            <span class="grupo-nome">{{ g.nome }}</span>
          </div>
          <div class="grupo-stats">
            <span class="mono dim">R$ {{ g.preco_medio.toFixed(3) }}/L</span>
            <span class="mono">{{ fmtR(g.total_valor) }}</span>
            <span class="mono dim">{{ fmtN(g.total_litros) }} L</span>
            <span class="mono dim">{{ g.qtd }} abast.</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" :class="g.categoria" :style="{ width: barW(g.total_valor) + '%' }" />
          </div>
        </div>
      </div>
      <div v-else class="empty">Sem dados de combustível premium encontrados</div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const maxVal = computed(() => {
  const grupos = props.data?.grupos || []
  return grupos.length ? Math.max(...grupos.map(g => g.total_valor)) : 1
})

const barW = v => Math.max(3, (v / maxVal.value) * 100)

const fmtR = v => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const fmtN = v => Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }

.header-row { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.card-hint { font-size: 12px; color: var(--text-3); }

.premium-total { text-align: right; flex-shrink: 0; }
.pt-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .03em; }
.pt-value { font-size: 22px; font-weight: 700; color: var(--red); font-family: 'JetBrains Mono', monospace; }

.grupos { display: flex; flex-direction: column; gap: 12px; }

.grupo-row { display: flex; flex-direction: column; gap: 6px; }

.grupo-info { display: flex; align-items: center; gap: 8px; }
.grupo-badge {
  font-size: 10px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
  padding: 2px 8px; border-radius: 20px;
}
.grupo-badge.premium { background: rgba(249,115,22,.15); color: var(--accent); }
.grupo-badge.comum   { background: rgba(59,130,246,.1);  color: #3b82f6; }

.grupo-nome { font-size: 13px; font-weight: 500; color: var(--text); }

.grupo-stats {
  display: flex; gap: 20px; align-items: center;
  font-size: 12px;
}

.bar-track { height: 3px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; opacity: .8; transition: width .6s ease; }
.bar-fill.premium { background: var(--accent); }
.bar-fill.comum   { background: #3b82f6; }

.empty { padding: 32px 0; text-align: center; color: var(--text-3); font-size: 13px; }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: var(--text-3); }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
