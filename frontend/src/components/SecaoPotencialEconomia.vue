<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Potencial de economia</div>
      <div class="card-hint">se todos usassem o posto mais barato da UF</div>
    </div>
    <div v-if="loading" class="skel" style="height:260px" />
    <template v-else-if="data.economia_potencial != null">
      <!-- Destaque principal -->
      <div class="highlight">
        <div class="hl-label">Economia potencial total</div>
        <div class="hl-value">{{ fmtR(data.economia_potencial) }}</div>
        <div class="hl-sub">{{ data.economia_pct?.toFixed(1) }}% do gasto histórico de {{ fmtR(data.total_gasto) }}</div>
      </div>

      <!-- Por UF -->
      <div class="uf-list" v-if="data.por_uf?.length">
        <div class="uf-header">
          <span>Estado</span>
          <span class="right">Economia</span>
          <span class="right">%</span>
        </div>
        <div v-for="u in data.por_uf.slice(0, 8)" :key="u.uf" class="uf-row">
          <span class="uf-nome mono">{{ u.uf }}</span>
          <span class="uf-val right">{{ fmtR(u.economia) }}</span>
          <span class="uf-pct right mono" :class="u.economia_pct > 5 ? 'orange' : ''">{{ u.economia_pct.toFixed(1) }}%</span>
        </div>
      </div>
    </template>
    <div v-else class="empty">Sem dados suficientes</div>
  </div>
</template>

<script setup>
const props = defineProps({
  data:    { type: Object,  default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

.highlight {
  background: rgba(34,197,94,.06);
  border: 1px solid rgba(34,197,94,.2);
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 16px;
}
.hl-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.hl-value { font-size: 32px; font-weight: 800; color: var(--green); letter-spacing: -0.03em; line-height: 1.1; margin: 6px 0 4px; }
.hl-sub { font-size: 12px; color: var(--text-3); }

.uf-header {
  display: grid; grid-template-columns: 1fr auto auto;
  gap: 12px; font-size: 10px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .04em;
  padding-bottom: 6px; border-bottom: 1px solid var(--border-subtle); margin-bottom: 4px;
}
.uf-row {
  display: grid; grid-template-columns: 1fr auto auto;
  gap: 12px; align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 12px;
}
.uf-row:last-child { border-bottom: none; }
.uf-nome { color: var(--text-2); }
.uf-val  { color: var(--text); font-weight: 600; }
.uf-pct  { color: var(--text-3); }
.uf-pct.orange { color: var(--accent); font-weight: 600; }
.right { text-align: right; }
.mono { font-family: 'JetBrains Mono', monospace; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
