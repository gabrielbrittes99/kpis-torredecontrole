<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Benchmark vs mercado ANP</div>
        <div class="card-hint">preço médio pago pela frota vs média de mercado por UF · fonte: ANP</div>
      </div>
      <div class="resumo-pills" v-if="resumo.combinacoes_analisadas">
        <div class="pill green" v-if="resumo.ufs_abaixo_mercado">
          <span>↓ {{ resumo.ufs_abaixo_mercado }} UF abaixo</span>
        </div>
        <div class="pill red" v-if="resumo.ufs_acima_mercado">
          <span>↑ {{ resumo.ufs_acima_mercado }} UF acima</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="skel" style="height:320px" />

    <template v-else-if="data.length">
      <!-- Destaque de economia/sobrecusto -->
      <div class="highlight-row">
        <div class="hl-card" :class="resumo.economia_potencial > 0 ? 'red' : 'green'">
          <div class="hl-label">Sobrecusto estimado</div>
          <div class="hl-value">{{ fmtR(resumo.economia_potencial_total) }}</div>
          <div class="hl-sub">{{ resumo.economia_pct?.toFixed(1) }}% do gasto total da frota</div>
        </div>
      </div>

      <!-- Tabela por UF + combustível -->
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>UF</th>
              <th>Combustível</th>
              <th class="right">Frota R$/L</th>
              <th class="right">ANP R$/L</th>
              <th class="right">Desvio</th>
              <th class="right">Sobrecusto</th>
              <th class="right">Litros</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in data" :key="`${row.uf}-${row.combustivel}`"
              :class="row.status">
              <td class="mono uf">{{ row.uf }}</td>
              <td class="comb">{{ row.combustivel }}</td>
              <td class="right mono">{{ row.preco_frota?.toFixed(3) }}</td>
              <td class="right mono dim">{{ row.preco_anp_mercado?.toFixed(3) ?? '—' }}</td>
              <td class="right">
                <span v-if="row.desvio_abs != null" class="desvio mono"
                  :class="row.desvio_abs > 0 ? 'red' : 'green'">
                  {{ row.desvio_abs > 0 ? '+' : '' }}{{ row.desvio_abs.toFixed(3) }}
                  <span class="desvio-pct">({{ row.desvio_pct > 0 ? '+' : '' }}{{ row.desvio_pct?.toFixed(1) }}%)</span>
                </span>
                <span v-else class="dim">—</span>
              </td>
              <td class="right mono" :class="row.economia_potencial > 0 ? 'red' : row.economia_potencial < 0 ? 'green' : ''">
                {{ row.economia_potencial != null ? fmtR(row.economia_potencial) : '—' }}
              </td>
              <td class="right mono dim">{{ fmtN(row.total_litros) }}</td>
              <td>
                <div class="status-dot" :class="row.status" :title="statusLabel(row.status)" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-else class="empty">
      <div>Sem dados de benchmark</div>
      <div class="empty-sub">ANP pode estar carregando os dados do mês atual</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data:    { type: Array,  default: () => [] },
  resumo:  { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
})

const statusLabel = s => ({
  acima_mercado:  'Acima do mercado',
  abaixo_mercado: 'Abaixo do mercado',
  na_media:       'Na média',
}[s] || s)

const fmtR = v => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : '—'
const fmtN = v => v != null ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint  { font-size: 12px; color: var(--text-3); margin-top: 2px; }

.resumo-pills { display: flex; gap: 8px; flex-shrink: 0; }
.pill { display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid; }
.pill.green { background: rgba(34,197,94,.08);  border-color: rgba(34,197,94,.25);  color: var(--green); }
.pill.red   { background: rgba(239,68,68,.08);  border-color: rgba(239,68,68,.25);  color: var(--red); }

.highlight-row { margin-bottom: 20px; }
.hl-card {
  display: inline-flex; flex-direction: column; gap: 2px;
  padding: 14px 20px; border-radius: 10px; border: 1px solid;
}
.hl-card.red   { background: rgba(239,68,68,.06);  border-color: rgba(239,68,68,.2); }
.hl-card.green { background: rgba(34,197,94,.06);  border-color: rgba(34,197,94,.2); }
.hl-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.hl-value { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
.hl-card.red   .hl-value { color: var(--red); }
.hl-card.green .hl-value { color: var(--green); }
.hl-sub   { font-size: 12px; color: var(--text-3); }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 500; color: var(--text-3);
  text-align: left; padding: 0 10px 10px;
  border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
}
th.right, td.right { text-align: right; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td {
  font-size: 12px; color: var(--text-2);
  padding: 8px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
}
tbody tr:last-child td { border-bottom: none; }
tbody tr.acima_mercado  { background: rgba(239,68,68,.03); }
tbody tr.abaixo_mercado { background: rgba(34,197,94,.03); }

.uf   { font-weight: 700; color: var(--text); letter-spacing: .04em; }
.comb { color: var(--text-2); max-width: 140px; overflow: hidden; text-overflow: ellipsis; }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: var(--text-3); }
.red  { color: var(--red); }
.green { color: var(--green); }

.desvio { font-size: 12px; font-weight: 600; display: flex; align-items: baseline; gap: 4px; justify-content: flex-end; }
.desvio-pct { font-size: 10px; font-weight: 400; opacity: .8; }

.status-dot {
  width: 6px; height: 6px; border-radius: 50%; margin-left: auto;
}
.status-dot.acima_mercado  { background: var(--red); }
.status-dot.abaixo_mercado { background: var(--green); }
.status-dot.na_media       { background: var(--text-3); }

.empty { padding: 48px 0; text-align: center; color: var(--text-3); font-size: 13px; }
.empty-sub { font-size: 11px; margin-top: 6px; opacity: .7; }

.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
