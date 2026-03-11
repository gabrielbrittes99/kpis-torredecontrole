<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Alertas de uso</div>
      <div class="card-hint">anomalias detectadas automaticamente</div>
    </div>
    <div v-if="loading" class="skel" style="height:200px" />
    <div v-else-if="!data.length" class="empty">Nenhuma anomalia detectada</div>
    <template v-else>
      <!-- Contadores por tipo -->
      <div class="tipo-counts">
        <div v-for="(meta, tipo) in TIPOS" :key="tipo"
          v-if="countByTipo[tipo]"
          class="tipo-badge" :class="tipo">
          <span class="tipo-badge-icon">{{ meta.icon }}</span>
          <span class="tipo-badge-label">{{ meta.label }}</span>
          <span class="tipo-badge-count">{{ countByTipo[tipo] }}</span>
        </div>
      </div>
      <div class="list">
        <div v-for="(a, i) in data.slice(0, 50)" :key="i" class="alerta-row">
          <div class="alerta-type" :class="a.tipo">
            <span class="alerta-icon">{{ tipoIcon(a.tipo) }}</span>
          </div>
          <div class="alerta-body">
            <div class="alerta-top">
              <span class="alerta-badge" :class="a.tipo">{{ tipoLabel(a.tipo) }}</span>
              <span class="alerta-desc">{{ a.descricao }}</span>
            </div>
            <div class="alerta-meta">
              <span class="mono">{{ a.placa }}</span>
              <span class="sep">·</span>
              <span>{{ a.motorista || 'sem motorista' }}</span>
              <span class="sep">·</span>
              <span>{{ a.cidade || a.posto || '—' }}</span>
              <span class="sep">·</span>
              <span class="mono">{{ fmtData(a.data) }}</span>
            </div>
          </div>
          <div class="alerta-valor">
            <div class="mono">{{ fmtR(a.valor) }}</div>
            <div class="dim">{{ a.litragem?.toFixed(0) }} L</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const countByTipo = computed(() => {
  const counts = {}
  for (const a of props.data) counts[a.tipo] = (counts[a.tipo] || 0) + 1
  return counts
})

const TIPOS = {
  acima_capacidade_tanque: { icon: '🚨', label: 'Tanque excedido' },
  volume_excessivo:        { icon: '⚠',  label: 'Volume excessivo' },
  preco_alto:              { icon: '💸', label: 'Preço alto' },
  abastecimento_duplo:     { icon: '🔁', label: 'Duplo abastecimento' },
}

const tipoIcon  = t => TIPOS[t]?.icon  || '!'
const tipoLabel = t => TIPOS[t]?.label || t

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtData = s => {
  if (!s) return ''
  const [y, m, d] = s.split('-')
  return `${d}/${m}/${y}`
}
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }
.empty { padding: 40px 0; text-align: center; color: var(--text-3); font-size: 13px; }

.list { display: flex; flex-direction: column; gap: 2px; }

.alerta-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 8px;
  transition: background 0.1s;
}
.alerta-row:hover { background: var(--surface-hover); }

.alerta-type {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 16px;
}
.alerta-type.acima_capacidade_tanque { background: rgba(239,68,68,.15); }
.alerta-type.volume_excessivo        { background: rgba(234,179,8,.1); }
.alerta-type.preco_alto              { background: rgba(239,68,68,.1); }
.alerta-type.abastecimento_duplo     { background: rgba(59,130,246,.1); }

.tipo-counts { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.tipo-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
  border: 1px solid;
}
.tipo-badge-icon  { font-size: 13px; }
.tipo-badge-label { color: var(--text-2); }
.tipo-badge-count { font-family: 'JetBrains Mono', monospace; color: var(--text); }
.tipo-badge.acima_capacidade_tanque { background: rgba(239,68,68,.08);  border-color: rgba(239,68,68,.25); }
.tipo-badge.volume_excessivo        { background: rgba(234,179,8,.08);  border-color: rgba(234,179,8,.25); }
.tipo-badge.preco_alto              { background: rgba(239,68,68,.08);  border-color: rgba(239,68,68,.2); }
.tipo-badge.abastecimento_duplo     { background: rgba(59,130,246,.08); border-color: rgba(59,130,246,.2); }

.alerta-top { display: flex; align-items: baseline; gap: 8px; margin-bottom: 2px; }
.alerta-badge {
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: .04em; flex-shrink: 0;
}
.alerta-badge.acima_capacidade_tanque { background: rgba(239,68,68,.15);  color: #ef4444; }
.alerta-badge.volume_excessivo        { background: rgba(234,179,8,.15);  color: #eab308; }
.alerta-badge.preco_alto              { background: rgba(239,68,68,.12);  color: #f87171; }
.alerta-badge.abastecimento_duplo     { background: rgba(59,130,246,.12); color: #60a5fa; }

.alerta-body { flex: 1; min-width: 0; }
.alerta-desc { font-size: 13px; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alerta-meta { font-size: 11px; color: var(--text-3); margin-top: 2px; display: flex; gap: 6px; flex-wrap: wrap; }
.sep { opacity: .4; }

.alerta-valor { text-align: right; flex-shrink: 0; }
.alerta-valor .mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text); font-weight: 600; }
.alerta-valor .dim { font-size: 11px; color: var(--text-3); }

.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: var(--text-3); }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
