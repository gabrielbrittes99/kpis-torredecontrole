<template>
  <div class="kpi-pro-card" :class="[theme]">
    
    <!-- Header: Título e Ícone -->
    <div class="kpi-header">
      <span class="kpi-title">{{ title }}</span>
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

    <!-- Footer: Descrição / Label Secundário -->
    <div class="kpi-footer">
      <span class="kpi-desc">{{ description }}</span>
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
  icon: { type: String, default: '' },
  
  theme: { type: String, default: 'neutral' }, // 'neutral', 'primary', 'dark'
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
  const isPositive = props.trendValue > 0
  
  if (props.trendInvert) {
    // Invertido: Subir é ruim (Custo), Cair é bom (Economia)
    return isPositive ? 'bad' : 'good'
  } else {
    // Normal: Subir é bom (Receita/Saving), Cair é ruim
    return isPositive ? 'good' : 'bad'
  }
})

const trendIcon = computed(() => {
  if (props.trendValue == null || props.trendValue === 0) return '—'
  return props.trendValue > 0 ? '▲' : '▼'
})
</script>

<style scoped>
.kpi-pro-card {
  position: relative;
  background: #ffffff;
  border: 1px solid #e2e8f0;
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
  background: #0f172a;
  border-color: #1e293b;
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
  align-items: center;
  margin-bottom: 12px;
  position: relative;
  z-index: 10;
}

.kpi-title {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
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

.kpi-trend.good {
  background: #ecfdf5;
  color: #059669;
}
.kpi-trend.bad {
  background: #fef2f2;
  color: #dc2626;
}
.kpi-trend.neutral {
  background: #f1f5f9;
  color: #64748b;
}

.kpi-pro-card.dark .kpi-trend.good { background: rgba(5, 150, 105, 0.2); }
.kpi-pro-card.dark .kpi-trend.bad { background: rgba(220, 38, 38, 0.2); }
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
</style>
