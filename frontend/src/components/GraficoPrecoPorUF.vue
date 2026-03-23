<template>
  <div class="pricing-container">
    <div v-if="loading" class="skel" style="height:260px; border-radius:12px;" />
    
    <div v-else-if="sortedData.length" class="chart-wrap">
      <apexchart 
        type="bar" 
        height="300" 
        :options="chartOptions" 
        :series="chartSeries" 
      />
    </div>
    
    <div v-else class="empty">Sem dados para exibição</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
  color:   { type: String,  default: '#3b82f6' },
})

// Pega os top 12 estados em volume (para não poluir se houver 27 estados) e ordena por preço.
// Mas se quiser mostrar todos, basta ordenar por preço. Vamos ordenar do mais caro para o mais barato.
const sortedData = computed(() => {
  return [...props.data]
    .sort((a, b) => b.preco_medio - a.preco_medio)
    .slice(0, 15) // Limita a 15 estados para não ficar gigante verticalmente
})

const chartSeries = computed(() => [{
  name: 'Preço Médio (R$)',
  data: sortedData.value.map(d => d.preco_medio)
}])

const chartOptions = computed(() => {
  const categories = sortedData.value.map(d => d.uf)
  const isDark = false
  
  return {
    chart: {
      type: 'bar',
      toolbar: { show: false },
      background: 'transparent',
      fontFamily: 'Inter, sans-serif'
    },
    plotOptions: {
      bar: {
        horizontal: true,
        borderRadius: 4,
        dataLabels: { position: 'top' },
        barHeight: '70%'
      }
    },
    colors: [props.color],
    dataLabels: {
      enabled: true,
      textAnchor: 'start',
      style: {
        fontSize: '11px',
        fontWeight: 'bold',
        colors: ['#0f172a']
      },
      formatter: v => 'R$ ' + v.toFixed(3),
      offsetX: 10
    },
    xaxis: {
      categories: categories,
      labels: {
        style: { colors: '#64748b', fontSize: '11px' },
        formatter: v => 'R$ ' + Number(v).toFixed(2)
      },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      labels: {
        style: {
          colors: '#475569',
          fontSize: '11px',
          fontWeight: 'bold'
        }
      }
    },
    grid: {
      borderColor: '#f1f5f9',
      strokeDashArray: 4,
      xaxis: { lines: { show: true } },
      yaxis: { lines: { show: false } }
    },
    tooltip: {
      theme: 'light',
      y: {
        formatter: (val, { dataPointIndex }) => {
          const item = sortedData.value[dataPointIndex]
          return `R$ ${val.toFixed(3)} | Vol: ${(item.total_litros/1000).toFixed(1)}k L`
        }
      }
    }
  }
})
</script>

<style scoped>
.pricing-container {
  min-height: 260px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}
.chart-wrap {
  width: 100%;
}
.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: var(--text3); font-size: 13px; }
.skel { background: var(--border); border-radius: 12px; min-height: 120px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
