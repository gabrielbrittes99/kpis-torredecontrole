<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">Frota por filial operacional</div>
      <div class="card-hint">veículos · idade média · valor FIPE total · fonte: BlueFleet</div>
    </div>
    <div v-if="loading" class="skel" style="height:220px" />
    <div v-else-if="!data.length" class="empty">Sem dados de filial</div>
    <div v-else class="filial-list">
      <div v-for="f in data" :key="f.FilialOperacional" class="filial-row">
        <div class="filial-info">
          <div class="filial-nome">{{ f.FilialOperacional || 'Sem filial' }}</div>
          <div class="filial-meta">
            <span class="badge">{{ f.qtd_veiculos }} veículos</span>
            <span class="sep">·</span>
            <span class="dim">Idade média: <b class="mono">{{ f.idade_media_meses ? Math.round(f.idade_media_meses) + ' meses' : '—' }}</b></span>
            <span class="sep">·</span>
            <span class="dim">FIPE: <b class="mono">{{ fmtR(f.valor_fipe_total) }}</b></span>
          </div>
        </div>
        <div class="filial-bar-wrap">
          <div class="filial-bar-track">
            <div class="filial-bar-fill" :style="{ width: barW(f.qtd_veiculos) + '%' }" />
          </div>
          <span class="filial-pct mono">{{ Math.round(f.qtd_veiculos / total * 100) }}%</span>
        </div>
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

const total   = computed(() => props.data.reduce((s, f) => s + (f.qtd_veiculos || 0), 0))
const maxQtd  = computed(() => Math.max(...props.data.map(f => f.qtd_veiculos || 0), 1))

const barW = qtd => Math.max(4, (qtd / maxQtd.value) * 100)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint  { font-size: 12px; color: var(--text-3); }
.empty { height: 180px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }

.filial-list { display: flex; flex-direction: column; gap: 12px; }

.filial-row {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 14px; border-radius: 8px; border: 1px solid var(--border-subtle);
  background: var(--bg); transition: border-color 0.15s;
}
.filial-row:hover { border-color: var(--border); }

.filial-info { flex: 1; min-width: 0; }
.filial-nome { font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.filial-meta { display: flex; align-items: center; gap: 6px; margin-top: 4px; font-size: 11px; flex-wrap: wrap; }

.badge {
  background: rgba(249,115,22,.1); color: var(--accent);
  border: 1px solid rgba(249,115,22,.2);
  padding: 1px 8px; border-radius: 20px;
  font-size: 11px; font-weight: 600;
}

.filial-bar-wrap { display: flex; align-items: center; gap: 10px; flex-shrink: 0; width: 160px; }
.filial-bar-track { flex: 1; height: 4px; background: var(--border-subtle); border-radius: 2px; overflow: hidden; }
.filial-bar-fill  { height: 100%; background: var(--accent); border-radius: 2px; opacity: .7; transition: width .6s ease; }
.filial-pct { font-size: 11px; color: var(--text-3); width: 32px; text-align: right; }

.sep { opacity: .35; }
.dim { color: var(--text-3); }
.mono { font-family: 'JetBrains Mono', monospace; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
