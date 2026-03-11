<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Eficiência km/L por veículo</div>
      <div class="card-hint">calculado via hodômetro</div>
    </div>
    <div v-if="loading" class="skel" style="height:280px" />
    <div v-else-if="!data.length" class="empty">
      <div>Hodômetro não registrado</div>
      <div class="empty-sub">Dados disponíveis quando o hodômetro for preenchido nos abastecimentos</div>
    </div>
    <table v-else>
      <thead>
        <tr>
          <th style="width:28px">#</th>
          <th>Placa</th>
          <th class="right">km/L</th>
          <th class="right">Total km</th>
          <th class="right">R$/km</th>
          <th style="width:80px"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(p, i) in data" :key="p.placa">
          <td class="rank mono">{{ i + 1 }}</td>
          <td>
            <div class="placa mono">{{ p.placa }}</div>
            <div class="model">{{ p.motorista_principal || p.modelo }}</div>
          </td>
          <td class="right">
            <span class="kml mono" :class="kmlClass(p.km_litro)">{{ p.km_litro?.toFixed(1) || '—' }}</span>
          </td>
          <td class="right mono dim">{{ fmtN(p.total_km) }}</td>
          <td class="right mono dim">{{ p.custo_por_km ? `R$ ${p.custo_por_km.toFixed(2)}` : '—' }}</td>
          <td>
            <div class="bar-track">
              <div class="bar-fill" :class="kmlClass(p.km_litro)" :style="{ width: barW(p.km_litro) + '%' }" />
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const maxKml = computed(() => props.data.length ? Math.max(...props.data.map(d => d.km_litro || 0)) : 1)
const minKml = computed(() => props.data.length ? Math.min(...props.data.map(d => d.km_litro || 0)) : 0)

function barW(kml) {
  if (!kml || maxKml.value === minKml.value) return 50
  return Math.max(5, (kml - minKml.value) / (maxKml.value - minKml.value) * 100)
}

function kmlClass(kml) {
  if (!kml) return 'neutral'
  const median = (maxKml.value + minKml.value) / 2
  if (kml >= median * 1.1) return 'green'
  if (kml <= median * 0.9) return 'red'
  return 'neutral'
}

const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; overflow-x: auto; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); }

.empty { height: 280px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: var(--text-3); font-size: 13px; text-align: center; }
.empty-sub { font-size: 11px; max-width: 220px; line-height: 1.5; }

table { width: 100%; border-collapse: collapse; }
thead th { font-size: 11px; font-weight: 500; color: var(--text-3); text-align: left; padding: 0 10px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td { font-size: 12px; color: var(--text-2); padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }

.rank  { color: var(--text-3); font-size: 11px; }
.placa { font-weight: 600; letter-spacing: .04em; color: var(--text); }
.model { font-size: 11px; color: var(--text-3); }
.kml   { font-size: 15px; font-weight: 700; }
.kml.green   { color: var(--green); }
.kml.red     { color: var(--red); }
.kml.neutral { color: var(--text); }
.dim   { color: var(--text-3); }
.mono  { font-family: 'JetBrains Mono', monospace; }

.bar-track { height: 3px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 2px; opacity: .8; transition: width .6s ease; }
.bar-fill.green   { background: var(--green); }
.bar-fill.red     { background: var(--red); }
.bar-fill.neutral { background: var(--accent); }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
