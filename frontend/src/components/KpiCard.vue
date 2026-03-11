<template>
  <div class="card">
    <div class="card-label">{{ label }}</div>
    <div class="card-value">
      <span v-if="loading" class="skel skel-value" />
      <span v-else>{{ formatted }}</span>
    </div>
    <div v-if="!loading && delta !== null" class="card-badge" :class="badgeClass">
      <span class="badge-icon">{{ delta > 0 ? '↑' : delta < 0 ? '↓' : '→' }}</span>
      {{ Math.abs(delta).toFixed(1) }}%
    </div>
    <div v-if="!loading && sub" class="card-sub">{{ sub }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:       { type: String },
  value:       { type: [Number, String], default: null },
  format:      { type: String, default: 'integer' }, // currency | integer | decimal
  delta:       { type: Number, default: null },
  deltaInvert: { type: Boolean, default: false },
  loading:     { type: Boolean, default: false },
  sub:         { type: String, default: '' },
})

const formatted = computed(() => {
  if (props.value === null || props.value === undefined) return '—'
  const v = Number(props.value)
  if (props.format === 'currency')
    return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
  if (props.format === 'decimal')
    return 'R$ ' + v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return v.toLocaleString('pt-BR', { maximumFractionDigits: 0 })
})

const badgeClass = computed(() => {
  if (props.delta === null) return 'neutral'
  const positive = props.delta > 0
  if (props.deltaInvert) return positive ? 'bad' : 'good'
  return positive ? 'good' : 'bad'
})
</script>

<style scoped>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: background 0.15s;
}
.card:hover { background: var(--surface-hover); }

.card-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-2);
  letter-spacing: 0.01em;
}
.card-value {
  font-size: 30px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
  line-height: 1;
  margin: 4px 0;
}
.card-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  font-weight: 500;
  font-family: 'JetBrains Mono', monospace;
  padding: 2px 8px;
  border-radius: 20px;
  width: fit-content;
}
.card-badge.good    { background: var(--green-bg); color: var(--green); }
.card-badge.bad     { background: var(--red-bg);   color: var(--red); }
.card-badge.neutral { background: var(--border);   color: var(--text-2); }
.badge-icon { font-size: 10px; }

.card-sub {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}
.skel {
  display: block;
  background: var(--border);
  border-radius: 6px;
  animation: pulse 1.4s ease infinite;
}
.skel-value { height: 34px; width: 120px; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
