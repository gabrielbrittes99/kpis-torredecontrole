<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Etanol × Gasolina — decisão por filial</div>
        <div class="card-hint">menor custo/km = combustível recomendado · verde = etanol vale · azul = gasolina</div>
      </div>
    </div>
    <div v-if="loading" class="skel" style="height:220px" />
    <div v-else-if="!data.length" class="empty">Sem dados de gasolina ou etanol nas filiais</div>
    <div v-else>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Filial</th>
              <th class="right">Custo/km Gasolina</th>
              <th class="right">Custo/km Etanol</th>
              <th class="right">Preço/L Gasolina</th>
              <th class="right">Preço/L Etanol</th>
              <th class="center">Melhor opção</th>
              <th class="right">Economia/km</th>
              <th class="center">Método</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in data" :key="r.filial">
              <td class="filial-nome">{{ r.filial }}</td>
              <td class="right mono dim">{{ fmt4(r.custo_km_gasolina) }}</td>
              <td class="right mono dim">{{ fmt4(r.custo_km_etanol) }}</td>
              <td class="right mono dim">{{ fmt4(r.preco_litro_gasolina) }}</td>
              <td class="right mono dim">{{ fmt4(r.preco_litro_etanol) }}</td>
              <td class="center">
                <span v-if="r.melhor_opcao === 'ETANOL'" class="badge-etanol">✓ Etanol</span>
                <span v-else-if="r.melhor_opcao === 'GASOLINA'" class="badge-gasolina">✓ Gasolina</span>
                <span v-else class="badge-sem">—</span>
              </td>
              <td class="right mono">
                <span v-if="r.economia_km != null" class="green">
                  R$ {{ r.economia_km.toFixed(4) }}/km
                </span>
                <span v-else class="dim">—</span>
              </td>
              <td class="center">
                <span class="metodo-tag" :class="r.metodo === 'custo_km' ? 'metodo-exato' : 'metodo-aprox'">
                  {{ r.metodo === 'custo_km' ? 'km real' : r.metodo === 'preco_litro_70pct' ? '70% regra' : 'insuf.' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="legenda">
        <span class="legenda-item"><span class="badge-etanol mini">Etanol</span> menor custo/km — recomendado usar etanol</span>
        <span class="legenda-item"><span class="badge-gasolina mini">Gasolina</span> menor custo/km — recomendado usar gasolina</span>
        <span class="legenda-item"><span class="metodo-tag metodo-aprox mini">70% regra</span> sem hodômetro — usa regra: etanol &lt; 70% preço gasolina → etanol vale</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data:    { type: Array,   default: () => [] },
  loading: { type: Boolean, default: false },
})

const fmt4 = v => v != null ? `R$ ${Number(v).toFixed(4)}` : '—'
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); }
.card-hint { font-size: 12px; color: var(--text-3); margin-top: 2px; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 500; color: var(--text-3);
  text-align: left; padding: 0 10px 10px;
  border-bottom: 1px solid var(--border-subtle); white-space: nowrap;
}
th.right, td.right { text-align: right; }
th.center, td.center { text-align: center; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--surface-hover); }
tbody td { font-size: 12px; color: var(--text-2); padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }

.filial-nome { font-size: 13px; font-weight: 500; color: var(--text); }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: var(--text-3); }
.green { color: var(--green); font-family: 'JetBrains Mono', monospace; }

.badge-etanol  { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: rgba(34,197,94,.12); color: #22c55e; border: 1px solid rgba(34,197,94,.25); }
.badge-gasolina{ display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; background: rgba(59,130,246,.12); color: #60a5fa; border: 1px solid rgba(59,130,246,.25); }
.badge-sem     { font-size: 12px; color: var(--text-3); }

.metodo-tag { display: inline-flex; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 500; }
.metodo-exato { background: rgba(34,197,94,.1); color: #22c55e; }
.metodo-aprox { background: rgba(245,158,11,.1); color: #f59e0b; }

.badge-etanol.mini, .badge-gasolina.mini { font-size: 10px; padding: 1px 7px; }
.metodo-tag.mini { font-size: 10px; }

.legenda { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 16px; font-size: 11px; color: var(--text-3); align-items: center; }
.legenda-item { display: flex; align-items: center; gap: 6px; }

.empty { height: 160px; display: flex; align-items: center; justify-content: center; color: var(--text-3); font-size: 13px; }
.skel { background: var(--border); border-radius: 8px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.7} }
</style>
