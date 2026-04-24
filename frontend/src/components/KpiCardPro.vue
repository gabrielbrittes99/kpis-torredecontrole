<template>
  <div class="kpi-pro-card" :class="[theme]">

    <!-- Header: Título e Ícone -->
    <div class="kpi-header">
      <div class="kpi-title-stack">
        <span class="kpi-title">{{ title }}</span>
        <span v-if="period" class="kpi-period">{{ period }}</span>
      </div>
      <span v-if="icon" class="kpi-icon">{{ icon }}</span>
    </div>

    <!-- Body: Valor Principal e Badge de Tendência -->
    <div class="kpi-body">
      <div class="kpi-main-line">
        <span class="kpi-value mono">{{ formattedValue }}</span>
        <span v-if="unit" class="kpi-unit">{{ unit }}</span>
      </div>

      <div v-if="trendValue != null" class="kpi-trend" :class="trendClass">
        <span class="trend-icon">{{ trendIcon }}</span>
        <span class="trend-text">{{ Math.abs(trendValue).toFixed(trendDecimals) }}%</span>
      </div>
    </div>

    <!-- Linha de delta absoluto + ref -->
    <div v-if="deltaAbsolute || refLabel" class="kpi-delta-line">
      <span v-if="deltaAbsolute" class="kpi-delta mono" :class="deltaClass">{{ deltaAbsolute }}</span>
      <span v-if="refLabel" class="kpi-ref">vs {{ refLabel }}</span>
    </div>

    <!-- Footer: Descrição / Métricas secundárias -->
    <div class="kpi-footer">
      <span v-if="description" class="kpi-desc">{{ description }}</span>
      <div v-if="secondaryMetrics && secondaryMetrics.length" class="kpi-secondary">
        <div v-for="(m, i) in secondaryMetrics" :key="i" class="kpi-sec-row">
          <span class="kpi-sec-label" :style="m.color ? { color: m.color } : {}">{{ m.label }}</span>
          <span class="kpi-sec-value mono">{{ m.value }}</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: [Number, String], required: true },
  format: { type: String, default: 'number' }, // 'currency', 'number', 'raw'
  decimals: { type: Number, default: 0 },
  unit: { type: String, default: '' },
  
  trendValue: { type: Number, default: null }, // Variação percentual (ex: 2.5, -1.4)
  trendInvert: { type: Boolean, default: false }, // Se true, + é vermelho e - é verde (ex: custos)
  trendDecimals: { type: Number, default: 1 },
  
  description: { type: String, default: '' },
  period: { type: String, default: '' },
  icon: { type: String, default: '' },

  theme: { type: String, default: 'neutral' }, // 'neutral', 'primary', 'dark'

  // Δ absoluto pré-formatado (ex: "+R$ 142.380" ou "-1.2k L"); aparece abaixo do valor
  deltaAbsolute: { type: String, default: '' },
  // Rótulo do período de referência (ex: "Mar/26") — aparece ao lado do delta
  refLabel: { type: String, default: '' },
  // Lista de métricas secundárias no rodapé: [{label, value, color?}]
  secondaryMetrics: { type: Array, default: () => [] },
})

// === FORMATAÇÃO DE VALORES ===
const formattedValue = computed(() => {
  if (props.value == null || props.value === '') return '—'
  if (props.format === 'raw') return props.value
  
  const num = Number(props.value)
  if (isNaN(num)) return props.value

  if (props.format === 'currency') {
    return 'R$ ' + num.toLocaleString('pt-BR', { minimumFractionDigits: props.decimals, maximumFractionDigits: props.decimals })
  }
  
  return num.toLocaleString('pt-BR', { minimumFractionDigits: props.decimals, maximumFractionDigits: props.decimals })
})

// === TENDÊNCIA E CORES ===
const trendClass = computed(() => {
  if (props.trendValue == null || props.trendValue === 0) return 'neutral'
  return props.trendValue > 0 ? 'up' : 'down'
})

const trendIcon = computed(() => {
  if (props.trendValue == null || props.trendValue === 0) return '—'
  return props.trendValue > 0 ? '▲' : '▼'
})

// Cor do delta absoluto: segue o mesmo sinal do trendValue + trendInvert
const deltaClass = computed(() => {
  if (props.trendValue == null || props.trendValue === 0) return 'neutral'
  const positive = props.trendValue > 0
  const good = props.trendInvert ? !positive : positive
  return good ? 'delta-good' : 'delta-bad'
})
</script>

<style scoped>
.kpi-pro-card {
  position: relative;
  background:
    linear-gradient(#ffffff, #ffffff) padding-box,
    linear-gradient(135deg, rgba(0,0,0,0.09) 0%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.04) 60%, rgba(0,0,0,0.09) 100%) border-box;
  border: 1px solid transparent;
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  min-height: 120px;
  z-index: 1;
}

.kpi-pro-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
}

/* Themes */
.kpi-pro-card.primary {
  border-left: 4px solid #C41230;
}
.kpi-pro-card.dark {
  background:
    linear-gradient(#0f172a, #0f172a) padding-box,
    linear-gradient(135deg, rgba(255,255,255,0.13) 0%, rgba(255,255,255,0.05) 40%, rgba(255,255,255,0.05) 60%, rgba(255,255,255,0.13) 100%) border-box;
  border: 1px solid transparent;
  color: white;
}
.kpi-pro-card.dark .kpi-title, 
.kpi-pro-card.dark .kpi-desc,
.kpi-pro-card.dark .kpi-unit {
  color: #94a3b8;
}
.kpi-pro-card.dark .kpi-value {
  color: #f8fafc;
}

/* Header */
.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  position: relative;
  z-index: 10;
}

.kpi-title-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-title {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  line-height: 1.2;
}

.kpi-period {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
  opacity: 0.8;
  margin-top: 1px;
}

.kpi-icon {
  font-size: 16px;
  opacity: 0.7;
}

/* Body */
.kpi-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  position: relative;
  z-index: 10;
  flex-wrap: wrap;
  gap: 8px;
}

.kpi-main-line {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1;
}

.kpi-value.mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.kpi-unit {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
}

/* Trend Badge */
.kpi-trend {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.kpi-trend.up {
  background: #eff6ff;
  color: #2563eb;
}
.kpi-trend.down {
  background: #fef2f2;
  color: #dc2626;
}
.kpi-trend.neutral {
  background: #f1f5f9;
  color: #64748b;
}

.kpi-pro-card.dark .kpi-trend.up { background: rgba(37, 99, 235, 0.2); }
.kpi-pro-card.dark .kpi-trend.down { background: rgba(220, 38, 38, 0.2); }
.kpi-pro-card.dark .kpi-trend.neutral { background: rgba(100, 116, 139, 0.2); }

/* Footer */
.kpi-footer {
  position: relative;
  z-index: 10;
}

.kpi-desc {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

/* Delta absolute line */
.kpi-delta-line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: -2px;
  margin-bottom: 8px;
  position: relative;
  z-index: 10;
}
.kpi-delta {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.kpi-delta.delta-good { color: #059669; }
.kpi-delta.delta-bad  { color: #dc2626; }
.kpi-delta.neutral    { color: #64748b; }
.kpi-ref {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

/* Secondary metrics (mini breakdown) */
.kpi-secondary {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.kpi-sec-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
}
.kpi-sec-label {
  color: #64748b;
  font-weight: 600;
}
.kpi-sec-value {
  color: #1e293b;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.kpi-pro-card.dark .kpi-secondary { border-top-color: rgba(255,255,255,0.1); }
.kpi-pro-card.dark .kpi-sec-label { color: #94a3b8; }
.kpi-pro-card.dark .kpi-sec-value { color: #f1f5f9; }
</style>
