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
.card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; height: 100%; box-sizing: border-box; }
.card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.card-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.card-hint { font-size: 12px; color: #94a3b8; margin-top: 2px; }

.table-wrap { overflow-x: auto; margin: 0 -24px; padding: 0 24px; }
table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  text-align: left; padding: 10px 10px;
  border-bottom: 1px solid #f1f5f9; white-space: nowrap;
}
th.right, td.right { text-align: right; }
th.center, td.center { text-align: center; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: #fcfcfc; }
tbody td { font-size: 13px; color: #334155; padding: 11px 10px; border-bottom: 1px solid #f8fafc; white-space: nowrap; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }

.filial-nome { font-size: 13px; font-weight: 600; color: #0f172a; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim  { color: #94a3b8; }
.green { color: #059669; font-family: 'JetBrains Mono', monospace; font-weight: 600; }

.badge-etanol  { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; background: #ecfdf5; color: #059669; border: 1px solid rgba(5,150,105,0.2); }
.badge-gasolina{ display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; background: #eff6ff; color: #3b82f6; border: 1px solid rgba(59,130,246,0.2); }
.badge-sem     { font-size: 12px; color: #94a3b8; }

.metodo-tag { display: inline-flex; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 600; }
.metodo-exato { background: #ecfdf5; color: #059669; }
.metodo-aprox { background: #fffbeb; color: #f59e0b; }

.badge-etanol.mini, .badge-gasolina.mini { font-size: 10px; padding: 1px 7px; }
.metodo-tag.mini { font-size: 10px; }

.legenda { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 16px; padding-top: 16px; border-top: 1px dashed #e2e8f0; font-size: 11px; color: #94a3b8; align-items: center; }
.legenda-item { display: flex; align-items: center; gap: 6px; }

.empty { height: 160px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 13px; font-style: italic; }
.skel { background: #f1f5f9; border-radius: 12px; animation: pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.8} }
</style>
