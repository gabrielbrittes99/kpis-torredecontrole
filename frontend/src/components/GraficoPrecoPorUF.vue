<template>
  <div class="pricing-container">
    <div v-if="loading" class="grid-skeleton">
      <div v-for="i in 8" :key="i" class="skel card-skel" />
    </div>
    
    <div v-else-if="data.length" class="states-grid">
      <div 
        v-for="(d, i) in sortedData" 
        :key="d.uf" 
        class="state-card"
        :class="{ 
          'cheapest': i === 0, 
          'expensive': i === sortedData.length - 1 
        }"
      >
        <div class="card-badge">{{ d.uf }}</div>
        
        <div class="price-section">
          <span class="currency">R$</span>
          <span class="price-val">{{ d.preco_medio.toFixed(3) }}</span>
        </div>
        
        <div class="card-stats">
          <div class="stat">
            <span class="s-label">LITROS</span>
            <span class="s-val">{{ fmtL(d.total_litros) }}</span>
          </div>
          <div class="stat">
            <span class="s-label">ABAST.</span>
            <span class="s-val">{{ d.qtd_abastecimentos }}</span>
          </div>
        </div>

        <div v-if="i === 0" class="rank-tag good">MAIS BARATO</div>
        <div v-if="i === sortedData.length - 1" class="rank-tag bad">MAIS CARO</div>
      </div>
    </div>
    
    <div v-else class="empty">Sem dados para exibição</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const sortedData = computed(() => {
  return [...props.data].sort((a, b) => a.preco_medio - b.preco_medio)
})

const fmtL = v => {
  if (v >= 1000) return (v / 1000).toFixed(1) + 'k L'
  return Math.round(v) + ' L'
}
</script>

<style scoped>
.pricing-container { min-height: 260px; }

.states-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.state-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  position: relative;
  transition: all 0.2s ease;
  overflow: hidden;
}
.state-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04); border-color: var(--s4); }

.card-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  color: var(--text3);
  padding: 2px 8px;
  background: var(--void);
  border-radius: 6px;
  margin-bottom: 12px;
}

.price-section {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 16px;
}
.currency { font-size: 13px; font-weight: 600; color: var(--text3); }
.price-val { font-size: 1.5rem; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }

.card-stats {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--void);
  padding-top: 12px;
}
.stat { display: flex; flex-direction: column; gap: 2px; }
.s-label { font-size: 8px; font-weight: 800; color: var(--text3); text-transform: uppercase; }
.s-val { font-size: 11px; font-weight: 700; color: var(--text2); }

.rank-tag {
  position: absolute;
  top: 12px;
  right: -25px;
  transform: rotate(45deg);
  font-size: 8px;
  font-weight: 800;
  padding: 4px 30px;
  color: white;
}
.rank-tag.good { background: var(--green); }
.rank-tag.bad { background: var(--red); }

/* Feedback visual para os extremos */
.state-card.cheapest { border-color: var(--green); background: linear-gradient(to bottom right, #ffffff, var(--green2)); }
.state-card.expensive { border-color: var(--red); background: linear-gradient(to bottom right, #ffffff, var(--red2)); }

.empty { height: 260px; display: flex; align-items: center; justify-content: center; color: var(--text3); font-size: 13px; }

/* Skeleton */
.grid-skeleton { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.skel { background: var(--border); border-radius: 12px; min-height: 120px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
