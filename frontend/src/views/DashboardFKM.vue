<template>
  <div class="page">
    <GlobalTopbar
      title="FKM · Fechamento Mensal"
      subtitle="Custo total da frota — combustível + manutenção + km rodado"
      :showPeriod="false" :showFilters="false"
    >
      <template #center>
        <div class="topbar-filters">
          <div class="filter-group">
            <label>Mês</label>
            <select v-model="filtroMes" @change="loadAll">
              <option v-for="m in filtros.meses" :key="m" :value="m">{{ fmtMes(m) }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Filial</label>
            <select v-model="filtroFilial" @change="loadAll">
              <option value="">Todas</option>
              <option v-for="f in filtros.filiais" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Grupo</label>
            <select v-model="filtroGrupo" @change="loadAll">
              <option value="">Todos</option>
              <option v-for="g in filtros.grupos" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Contrato</label>
            <select v-model="filtroContrato" @change="loadAll">
              <option value="">Todos</option>
              <option v-for="c in filtros.contratos" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>
      </template>
      <template #right>
        <button class="btn-topbar" @click="refreshCache" :disabled="refreshing">
          {{ refreshing ? 'Atualizando...' : 'Recarregar Planilha' }}
        </button>
      </template>
    </GlobalTopbar>

    <div class="page-body">

      <!-- ━━━━━ SEÇÃO 1: KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Custo Total da Frota"
            :value="kpis.total_geral || 0"
            format="currency"
            theme="primary"
            :description="`${fmtN(kpis.qtd_veiculos)} veículos · ${fmtN(kpis.qtd_filiais)} filiais`"
          />
          <KpiCardPro
            title="Custo / KM Total"
            :value="kpis.custo_km_total || 0"
            format="currency"
            :decimals="4"
            :description="`Comb: R$ ${fmt4(kpis.custo_km_combustivel)} / km · Man: R$ ${fmt4(kpis.custo_km_manutencao)} / km`"
          />
          <KpiCardPro
            title="Total KM Rodado"
            :value="kpis.total_km || 0"
            format="number"
            unit="km"
            :description="`Média: ${fmtN(Math.round((kpis.total_km || 0) / Math.max(kpis.qtd_veiculos || 1, 1)))} km/veículo`"
          />
          <KpiCardPro
            title="Eficiência Média"
            :value="kpis.media_kml || 0"
            format="number"
            :decimals="2"
            unit="km/L"
            :description="`${fmtN(kpis.total_litros)} litros · ${fmtR(kpis.total_combustivel)} em combustível`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>

        <!-- Sub-KPIs: categorias -->
        <div class="cat-kpis" v-if="!lKpis && kpis.total_geral">
          <div class="cat-kpi">
            <span class="cat-label">Combustível</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_combustivel) }}</span>
            <span class="cat-pct">{{ kpis.pct_combustivel }}%</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Manutenção Geral</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_geral_manutencao) }}</span>
            <span class="cat-pct">{{ kpis.pct_manutencao }}%</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Pneus</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_pneus) }}</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Lataria e Pintura</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_lataria) }}</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Arla</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_arla) }}</span>
          </div>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO: RECONCILIAÇÃO TRUCKPAG × DIRETO ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading" style="margin-bottom:0">
            Combustível · TruckPag vs Faturado Direto · {{ fmtMes(filtroMes) }}
          </div>
          <span v-if="reconciliacao.totais?.qtd_alertas > 0" class="section-badge badge-warn">
            {{ reconciliacao.totais.qtd_alertas }} alertas de qualidade
          </span>
        </div>

        <div v-if="lReconciliacao" class="skel" style="height:160px" />
        <template v-else-if="reconciliacao.totais">

          <!-- Summary chips -->
          <div class="recon-chips">
            <div class="recon-chip">
              <span class="recon-chip-label">Total FKM (real)</span>
              <span class="recon-chip-val">{{ fmtR(reconciliacao.totais.valor_fkm) }}</span>
            </div>
            <div class="recon-chip recon-chip-tp">
              <span class="recon-chip-label">Via TruckPag</span>
              <span class="recon-chip-val">{{ fmtR(reconciliacao.totais.valor_truckpag) }}</span>
              <span class="recon-chip-pct">{{ reconciliacao.totais.pct_truckpag }}%</span>
            </div>
            <div class="recon-chip recon-chip-direto">
              <span class="recon-chip-label">Faturado Direto</span>
              <span class="recon-chip-val">{{ fmtR(reconciliacao.totais.valor_direto) }}</span>
              <span class="recon-chip-pct">{{ (100 - reconciliacao.totais.pct_truckpag).toFixed(1) }}%</span>
            </div>
            <div class="recon-chip">
              <span class="recon-chip-label">Veículos c/ Direto</span>
              <span class="recon-chip-val">{{ reconciliacao.totais.qtd_com_direto }}</span>
              <span class="recon-chip-pct">de {{ reconciliacao.totais.qtd_veiculos }} no mês</span>
            </div>
          </div>

          <!-- Tabela por filial -->
          <div class="table-wrap" v-if="reconciliacao.resumo_filiais?.length">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Filial</th>
                  <th class="right">Total FKM</th>
                  <th class="right">TruckPag</th>
                  <th class="right">Direto</th>
                  <th class="right">% TruckPag</th>
                  <th class="right">Veículos</th>
                  <th class="right">c/ Direto</th>
                  <th class="right">Alertas</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in reconciliacao.resumo_filiais" :key="row.filial">
                  <td class="filial-cell">{{ row.filial }}</td>
                  <td class="right mono">{{ fmtR(row.total_valor_fkm) }}</td>
                  <td class="right mono">{{ fmtR(row.total_valor_truckpag) }}</td>
                  <td class="right mono" :class="row.total_valor_direto > 100 ? 'text-yellow' : ''">{{ fmtR(row.total_valor_direto) }}</td>
                  <td class="right mono">
                    <div class="pct-bar-wrap">
                      <div class="pct-bar-track">
                        <div class="pct-bar-fill" :style="{ width: Math.min(row.pct_truckpag, 100) + '%' }" />
                      </div>
                      <span :class="row.pct_truckpag >= 95 ? 'text-green' : row.pct_truckpag >= 60 ? '' : 'text-yellow'">
                        {{ row.pct_truckpag }}%
                      </span>
                    </div>
                  </td>
                  <td class="right mono">{{ row.qtd_veiculos }}</td>
                  <td class="right mono" :class="row.qtd_com_direto > 0 ? 'text-yellow' : 'text-green'">{{ row.qtd_com_direto }}</td>
                  <td class="right mono" :class="row.qtd_alertas > 0 ? 'text-red' : ''">{{ row.qtd_alertas || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Veículos com alerta de qualidade -->
          <div v-if="veiculosComAlerta.length">
            <button class="btn-toggle" @click="showAlertas = !showAlertas">
              {{ showAlertas ? '▲ Ocultar' : '▼ Ver' }} veículos com alerta ({{ veiculosComAlerta.length }})
            </button>
            <div v-if="showAlertas" class="table-wrap" style="margin-top:12px">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Placa</th>
                    <th>Filial</th>
                    <th>Combustível</th>
                    <th class="right">Total FKM</th>
                    <th class="right">TruckPag</th>
                    <th class="right">Direto</th>
                    <th class="right">% TP</th>
                    <th class="right">Preço/L impl.</th>
                    <th>Alertas</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in veiculosComAlerta" :key="v.placa">
                    <td class="placa-cell mono">{{ v.placa }}</td>
                    <td class="filial-cell">{{ v.filial }}</td>
                    <td>{{ v.tp_combustivel || '—' }}</td>
                    <td class="right mono">{{ fmtR(v.valor_fkm) }}</td>
                    <td class="right mono">{{ fmtR(v.valor_truckpag) }}</td>
                    <td class="right mono" :class="v.valor_direto > 100 ? 'text-yellow' : ''">{{ fmtR(v.valor_direto) }}</td>
                    <td class="right mono">{{ v.pct_truckpag != null ? v.pct_truckpag + '%' : '—' }}</td>
                    <td class="right mono">{{ v.preco_litro_implicito != null ? fmtR(v.preco_litro_implicito) + '/L' : '—' }}</td>
                    <td>
                      <span v-for="flag in v.flags" :key="flag" class="flag-badge" :class="'flag-' + flag">{{ flagLabel(flag) }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </template>
        <div v-else class="empty">Sem dados de reconciliação para {{ fmtMes(filtroMes) }}</div>
      </section>

      <!-- ━━━━━ SEÇÃO 2: GRÁFICOS ━━━━━ -->
      <div class="two-col">

        <!-- Distribuição por categoria -->
        <section class="v-block">
          <div class="section-heading">Composição do Custo</div>
          <div v-if="lCategorias" class="skel" style="height:280px" />
          <div v-else-if="!categorias.length" class="empty">Sem dados</div>
          <apexchart
            v-else
            type="donut"
            height="280"
            :options="donutOptions"
            :series="donutSeries"
          />
        </section>

        <!-- Evolução mensal -->
        <section class="v-block">
          <div class="section-heading">Evolução Mensal</div>
          <div v-if="lEvolucao" class="skel" style="height:280px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados históricos</div>
          <apexchart
            v-else
            type="line"
            height="280"
            :options="lineOptions"
            :series="lineSeries"
          />
        </section>
      </div>

      <!-- ━━━━━ SEÇÃO EXTRA: RESUMO POR CONTRATO ━━━━━ -->
      <section class="v-block" v-if="porContrato.length > 0">
        <div class="section-heading">Resumo por Contrato · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lContratos" class="skel" style="height:200px" />
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Contrato</th>
                <th class="right">Custo Total</th>
                <th class="right">KM Rodado</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L Médio</th>
                <th class="right">Veículos Alocados</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porContrato" :key="row.contrato">
                <td class="filial-cell" style="font-weight:600; color:var(--brand);">{{ row.contrato }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_valor) }}</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono" :class="custoKmClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.media_kml ? row.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 3: RESUMO POR FILIAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Resumo por Filial · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lFilial" class="skel" style="height:260px" />
        <div v-else-if="!porFilial.length" class="empty">Sem dados por filial</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Filial</th>
                <th class="right">KM Rodado</th>
                <th class="right">Combustível</th>
                <th class="right">Man. Geral</th>
                <th class="right">Pneus</th>
                <th class="right">Lataria</th>
                <th class="right">Total</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L</th>
                <th class="right">Veículos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porFilial" :key="row.filial">
                <td class="filial-cell">{{ row.filial }}</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono">{{ fmtR(row.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(row.total_geral_manutencao) }}</td>
                <td class="right mono">{{ fmtR(row.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(row.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_geral) }}</td>
                <td class="right mono" :class="custoKmClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.media_kml ? row.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td>TOTAL</td>
                <td class="right mono">{{ fmtN(kpis.total_km) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_geral_manutencao) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(kpis.total_geral) }}</td>
                <td class="right mono">{{ fmt4(kpis.custo_km_total) }}</td>
                <td class="right mono">{{ kpis.media_kml ? kpis.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ kpis.qtd_veiculos }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 4: TOP VEÍCULOS (TCO) ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading">Top Veículos por Custo Total · {{ fmtMes(filtroMes) }}</div>
          <span class="section-badge">{{ veiculos.length }} veículos</span>
        </div>
        <div v-if="lVeiculos" class="skel" style="height:260px" />
        <div v-else-if="!veiculos.length" class="empty">Sem dados de veículos</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Placa</th>
                <th>Modelo</th>
                <th>Grupo</th>
                <th>Filial</th>
                <th class="right">KM</th>
                <th class="right">Combustível</th>
                <th class="right">Manutenção</th>
                <th class="right">Pneus</th>
                <th class="right">Total</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, idx) in veiculos" :key="v.placa">
                <td class="idx-cell mono">{{ idx + 1 }}</td>
                <td class="placa-cell mono">{{ v.placa }}</td>
                <td>{{ v.modelo || '—' }}</td>
                <td><span class="grupo-badge" :class="grupoBadgeClass(v.grupo)">{{ v.grupo || '—' }}</span></td>
                <td class="filial-cell">{{ v.filial || '—' }}</td>
                <td class="right mono">{{ fmtN(v.total_km) }}</td>
                <td class="right mono">{{ fmtR(v.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(v.total_manutencao) }}</td>
                <td class="right mono">{{ fmtR(v.total_pneus) }}</td>
                <td class="right mono fw-bold">{{ fmtR(v.total_geral) }}</td>
                <td class="right mono" :class="custoKmClass(v.custo_km)">{{ fmt4(v.custo_km) }}</td>
                <td class="right mono">{{ v.media_kml ? v.media_kml.toFixed(2) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import {
  fetchFkmFiltros,
  fetchFkmKpis,
  fetchFkmResumoPorFilial,
  fetchFkmCustoPorVeiculo,
  fetchFkmEvolucaoMensal,
  fetchFkmDistribuicaoCategorias,
  fetchFkmReconciliacao,
} from '../api/fkm.js'
import { fetchContratosKpis } from '../api/contratos.js'

// ── Estado ────────────────────────────────────────────────────────────────
const filtros   = ref({ meses: [], filiais: [], grupos: [], combustiveis: [], contratos: [] })
const filtroMes = ref('')
const filtroFilial = ref('')
const filtroGrupo  = ref('')
const filtroContrato = ref('')

const kpis      = ref({})
const categorias = ref([])
const evolucao  = ref([])
const porFilial = ref([])
const veiculos  = ref([])
const porContrato = ref([])

const lKpis           = ref(true)
const lCategorias     = ref(true)
const lEvolucao       = ref(true)
const lFilial         = ref(true)
const lVeiculos       = ref(true)
const lContratos      = ref(true)
const lReconciliacao  = ref(true)
const refreshing      = ref(false)

const reconciliacao   = ref({})
const showAlertas     = ref(false)

// ── Formatadores ──────────────────────────────────────────────────────────
const fmtR = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtN = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
const fmt4 = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })

const fmtMes = (ym) => {
  if (!ym) return '—'
  const [ano, mes] = ym.split('-')
  const nomes = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  return `${nomes[parseInt(mes)]}/${ano}`
}

const custoKmClass = (v) => {
  if (v == null) return ''
  if (v > 1.5) return 'text-red'
  if (v > 1.0) return 'text-yellow'
  return 'text-green'
}

const grupoBadgeClass = (g) => {
  if (!g) return ''
  const lower = g.toLowerCase()
  if (['bitruck', 'truck', 'toco', '3/4'].includes(lower)) return 'badge-truck'
  if (lower === 'pesado') return 'badge-heavy'
  if (lower === 'médio' || lower === 'medio') return 'badge-medium'
  return 'badge-light'
}

// ── Reconciliação ─────────────────────────────────────────────────────────
const veiculosComAlerta = computed(() =>
  (reconciliacao.value.veiculos ?? []).filter(v => v.tem_alerta)
)

const FLAG_LABELS = {
  gap_negativo:   'Gap negativo',
  preco_suspeito: 'Preço/L suspeito',
  kml_divergente: 'km/L divergente',
  sem_truckpag:   'Sem TruckPag',
}
function flagLabel(f) { return FLAG_LABELS[f] ?? f }

// ── Gráfico Donut ─────────────────────────────────────────────────────────
const donutSeries  = computed(() => categorias.value.map(c => c.valor))
const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter' },
  labels: categorias.value.map(c => c.categoria),
  colors: ['#C41230', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
  legend: { position: 'bottom', fontSize: '12px', labels: { colors: '#475569' } },
  dataLabels: { enabled: true, formatter: (val) => val.toFixed(1) + '%', style: { fontSize: '11px' } },
  plotOptions: { pie: { donut: { size: '60%', labels: { show: true, total: { show: true, label: 'Total', formatter: () => fmtR(kpis.value.total_geral) } } } } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

// ── Gráfico Linha ──────────────────────────────────────────────────────────
const lineSeries = computed(() => [
  { name: 'Total Geral', data: evolucao.value.map(e => e.total_geral) },
  { name: 'Combustível', data: evolucao.value.map(e => e.total_combustivel) },
  { name: 'Manutenção', data: evolucao.value.map(e => e.total_manutencao) },
])
const lineOptions = computed(() => ({
  chart: { type: 'line', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  colors: ['#C41230', '#3b82f6', '#10b981'],
  stroke: { curve: 'smooth', width: [2.5, 2, 2] },
  xaxis: { categories: evolucao.value.map(e => fmtMes(e.ano_mes)), labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
  yaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  legend: { position: 'top', fontSize: '12px', labels: { colors: '#475569' } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

// ── Carga de dados ────────────────────────────────────────────────────────
const params = () => {
  const p = {}
  if (filtroMes.value)    p.ano_mes = filtroMes.value
  if (filtroFilial.value) p.filial  = filtroFilial.value
  if (filtroGrupo.value)  p.grupo   = filtroGrupo.value
  if (filtroContrato.value) p.contrato = filtroContrato.value
  return p
}

const loadAll = async () => {
  const p = params()
  lKpis.value = lCategorias.value = lFilial.value = lVeiculos.value = lContratos.value = lReconciliacao.value = true
  showAlertas.value = false

  // Reconciliação: passa só ano_mes, filial e contrato (sem grupo — TruckPag não tem esse filtro)
  const pRecon = {}
  if (filtroMes.value)     pRecon.ano_mes  = filtroMes.value
  if (filtroFilial.value)  pRecon.filial   = filtroFilial.value
  if (filtroContrato.value) pRecon.contrato = filtroContrato.value

  Promise.all([
    fetchFkmKpis(p).then(d => { kpis.value = d; lKpis.value = false }).catch(() => lKpis.value = false),
    fetchFkmDistribuicaoCategorias(p).then(d => { categorias.value = d; lCategorias.value = false }).catch(() => lCategorias.value = false),
    fetchFkmResumoPorFilial(p).then(d => { porFilial.value = d; lFilial.value = false }).catch(() => lFilial.value = false),
    fetchFkmCustoPorVeiculo({ ...p, limit: 50 }).then(d => { veiculos.value = d; lVeiculos.value = false }).catch(() => lVeiculos.value = false),
    fetchContratosKpis({ ano_mes: p.ano_mes, contrato: p.contrato }).then(d => { porContrato.value = d; lContratos.value = false }).catch(() => lContratos.value = false),
    fetchFkmReconciliacao(pRecon).then(d => { reconciliacao.value = d; lReconciliacao.value = false }).catch(() => lReconciliacao.value = false),
  ])
}

const loadEvolucao = async () => {
  lEvolucao.value = true
  const p = {}
  if (filtroFilial.value) p.filial = filtroFilial.value
  if (filtroGrupo.value)  p.grupo  = filtroGrupo.value
  fetchFkmEvolucaoMensal(p)
    .then(d => { evolucao.value = d; lEvolucao.value = false })
    .catch(() => lEvolucao.value = false)
}

const refreshCache = async () => {
  refreshing.value = true
  try {
    await fetch(`${import.meta.env.VITE_API_URL}/api/fkm/cache/refresh`, { method: 'POST' })
    await init()
  } finally {
    refreshing.value = false
  }
}

const init = async () => {
  const f = await fetchFkmFiltros()
  filtros.value = f
  if (f.meses.length && !filtroMes.value) filtroMes.value = f.meses[0]
  await Promise.all([loadAll(), loadEvolucao()])
}

onMounted(init)
</script>

<style scoped>
.page { min-height: 100vh; background: #f8fafc; }


/* ── Page body ── */
.page-body {
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1600px;
}

/* ── KPI grid ── */
.kpi-pro-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

/* ── Sub KPIs de categoria ── */
.cat-kpis {
  display: flex; gap: 0; border-top: none; padding-top: 16px;
  flex-wrap: wrap; position: relative;
}
.cat-kpis::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(to right, transparent, rgba(0,0,0,0.10) 20%, rgba(0,0,0,0.10) 80%, transparent); }
.cat-kpi {
  flex: 1; min-width: 120px;
  display: flex; flex-direction: column; gap: 3px;
  padding: 0 20px 0 0;
  border-right: 1px solid rgba(0,0,0,0.04);
}
.cat-kpi:last-child { border-right: none; }
.cat-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.cat-value { font-size: 14px; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
.cat-pct { font-size: 11px; font-weight: 600; color: #C41230; }

/* ── Two col ── */
.two-col { display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }

/* ── Section heading ── */
.section-heading {
  font-size: 12px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 16px;
}
.section-heading-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-heading-row .section-heading { margin-bottom: 0; }
.section-badge {
  background: #f1f5f9; border-radius: 6px; padding: 2px 8px;
  font-size: 11px; font-weight: 700; color: #64748b;
}

/* ── Table ── */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th {
  background: #f8fafc; border-bottom: 1px solid rgba(0,0,0,0.07); padding: 8px 12px;
  font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;
  white-space: nowrap;
}
.data-table td { padding: 9px 12px; border-bottom: 1px solid rgba(0,0,0,0.04); color: #1e293b; white-space: nowrap; }
.data-table tbody tr:hover { background: #fafafa; }
.data-table tfoot tr { background: #f8fafc; }
.data-table tfoot td { padding: 10px 12px; font-weight: 700; font-size: 12px; border-top: 2px solid #e2e8f0; }
.right { text-align: right; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }

.idx-cell { color: #94a3b8; font-size: 11px; width: 32px; }
.placa-cell { font-weight: 700; color: #0f172a; letter-spacing: 0.05em; }
.filial-cell { color: #475569; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }

.text-red { color: #dc2626; font-weight: 700; }
.text-yellow { color: #d97706; font-weight: 600; }
.text-green { color: #059669; }

/* Grupo badges */
.grupo-badge { display: inline-block; padding: 2px 7px; border-radius: 5px; font-size: 10px; font-weight: 700; }
.badge-truck   { background: #fef3c7; color: #92400e; }
.badge-heavy   { background: #fee2e2; color: #991b1b; }
.badge-medium  { background: #dbeafe; color: #1e40af; }
.badge-light   { background: #d1fae5; color: #065f46; }

/* ── Reconciliação ── */
.recon-chips {
  display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px;
}
.recon-chip {
  flex: 1; min-width: 160px;
  background: #f8fafc;
  border: 1px solid rgba(0,0,0,0.07);
  border-radius: 12px; padding: 14px 18px;
  display: flex; flex-direction: column; gap: 4px;
}
.recon-chip-tp   { border-top: 3px solid #2563eb; }
.recon-chip-direto { border-top: 3px solid #f59e0b; }
.recon-chip-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.recon-chip-val   { font-size: 18px; font-weight: 800; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
.recon-chip-pct   { font-size: 12px; font-weight: 700; color: #64748b; }

.pct-bar-wrap { display: flex; align-items: center; gap: 8px; }
.pct-bar-track { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 60px; }
.pct-bar-fill  { height: 100%; background: #2563eb; border-radius: 3px; transition: width 0.4s ease; }

.btn-toggle {
  background: none; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 6px 14px; font-size: 12px; font-weight: 600; color: #64748b;
  cursor: pointer; margin-top: 12px; transition: all 0.15s;
}
.btn-toggle:hover { background: #f8fafc; border-color: #cbd5e1; }

.flag-badge {
  display: inline-block; padding: 2px 7px; border-radius: 5px;
  font-size: 10px; font-weight: 700; margin-right: 4px; white-space: nowrap;
}
.flag-gap_negativo   { background: #fef2f2; color: #dc2626; }
.flag-preco_suspeito { background: #fff7ed; color: #ea580c; }
.flag-kml_divergente { background: #fffbeb; color: #d97706; }
.flag-sem_truckpag   { background: #eff6ff; color: #2563eb; }

.badge-warn { background: #fff7ed; color: #ea580c; border: 1px solid rgba(234,88,12,0.2); }

/* ── Utilitários ── */
.empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 40px 0; }
.skel { background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }
.kpi-skel { height: 120px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 1200px) {
  .two-col { grid-template-columns: 1fr; }
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .page-body { padding: 16px; }
  .kpi-pro-grid { grid-template-columns: 1fr; }
}
</style>
