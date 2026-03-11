<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Mix de combustíveis</div>
      <div class="card-hint">por volume (litros)</div>
    </div>

    <div v-if="loading" class="skel" style="height:220px" />

    <div v-else-if="!data.length" class="empty">Sem dados</div>

    <div v-else class="lista">
      <div v-for="(item, i) in rows" :key="item.nome_combustivel" class="item">
        <div class="item-top">
          <div class="item-nome">{{ item.nome_combustivel }}</div>
          <div class="item-nums">
            <span class="mono bold">{{ fmtN(item.total_litros) }} L</span>
            <span class="sep">·</span>
            <span class="mono dim">{{ fmtR(item.total_valor) }}</span>
            <span class="sep">·</span>
            <span class="preco mono" :class="i === 0 ? 'accent' : ''">R$ {{ item.preco_litro?.toFixed(3) }}/L</span>
          </div>
        </div>
        <div class="bar-track">
          <div
            class="bar-fill"
            :style="{
              width: item.pct_litros + '%',
              background: CORES[i % CORES.length],
              opacity: i === 0 ? 1 : 0.55 + (i * 0.01),
            }"
          />
        </div>
        <div class="item-pct mono dim">{{ item.pct_litros }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

// Ordena por litros e agrupa "outros" se tiver mais de 5
const CORES = ['#f97316','#3b82f6','#22c55e','#a855f7','#eab308']

const rows = computed(() => {
  const sorted = [...props.data].sort((a, b) => b.total_litros - a.total_litros)
  const total = props.data.reduce((s, x) => s + x.total_litros, 0)
  const withPct = r => ({ ...r, pct_litros: +(r.total_litros / total * 100).toFixed(1) })
  if (sorted.length <= 5) return sorted.map(withPct)
  const top = sorted.slice(0, 4).map(withPct)
  const outros = sorted.slice(4)
  const outrosLitros = outros.reduce((s, x) => s + x.total_litros, 0)
  const outrosValor  = outros.reduce((s, x) => s + x.total_valor, 0)
  top.push({
    nome_combustivel: `Outros (${outros.length} tipos)`,
    total_litros: outrosLitros,
    total_valor:  outrosValor,
    preco_litro:  outrosValor / outrosLitros,
    pct_litros:   +(outrosLitros / total * 100).toFixed(1),
  })
  return top
})

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint  { font-size: 12px; color: var(--text-3); }

.lista { display: flex; flex-direction: column; gap: 14px; }

.item { display: flex; flex-direction: column; gap: 5px; }

.item-top { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.item-nome { font-size: 12px; font-weight: 500; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0; max-width: 140px; }
.item-nums { display: flex; align-items: baseline; gap: 4px; flex-shrink: 0; flex-wrap: wrap; justify-content: flex-end; }

.bar-track { height: 4px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 2px; transition: width .6s ease; }

.item-pct { font-size: 10px; text-align: right; }

.mono   { font-family: 'JetBrains Mono', monospace; }
.bold   { font-size: 13px; font-weight: 600; color: var(--text); }
.dim    { color: var(--text-3); font-size: 11px; }
.preco  { font-size: 11px; color: var(--text-2); }
.accent { color: var(--accent); }
.sep    { color: var(--border); font-size: 10px; }

.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel  { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
