<template>
  <div class="page">
    <!-- TOPBAR -->
    <header class="topbar">
      <div class="topbar-main">
        <div class="topbar-left">
          <span class="logo">
            GRITSCH <span class="divider">//</span>
            <div class="title-group">
              <span class="subtitle">Gestão de Pneus</span>
              <span class="page-subtitle">Controle e análise de pneus da frota</span>
            </div>
          </span>
        </div>

        <div class="topbar-center">
          <div class="filters">
                        <div class="filter-group">
              <label>Ano</label>
              <select v-model="filtroAno" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="a in filtros.anos" :key="a" :value="a">{{ a }}</option>
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
              <label>Marca</label>
              <select v-model="filtroMarca" @change="loadAll">
                <option value="">Todas</option>
                <option v-for="m in filtros.marcas" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Fornecedor</label>
              <select v-model="filtroFornecedor" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="f in filtros.fornecedores" :key="f" :value="f">{{ f }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Aro</label>
              <select v-model="filtroAro" @change="loadAll">
                <option value="">Todos</option>
                <option v-for="a in filtros.aros" :key="a" :value="a">{{ a }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>Medida</label>
              <select v-model="filtroMedida" @change="loadAll">
                <option value="">Todas</option>
                <option v-for="m in filtros.medidas" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="page-body">

      <!-- SEÇÃO 1: KPIs -->
      <section class="v-block">
        <div class="section-heading">Indicadores Principais</div>
        <div class="kpi-grid four-col" v-if="!lKpis">
          <div class="kpi-card">
            <div class="kpi-label">Total de Pneus</div>
            <div class="kpi-value text-blue">{{ kpis.total_pneus || 0 }}</div>
            <div class="kpi-sub">Unidades compradas</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Frota (Placas)</div>
            <div class="kpi-value">{{ kpis.placas || 0 }}</div>
            <div class="kpi-sub">Veículos distintos</div>
          </div>
          <div class="kpi-card primary">
            <div class="kpi-label">Investimento Total</div>
            <div class="kpi-value">{{ fmtR(kpis.total_valor) }}</div>
            <div class="kpi-sub">Valor bruto faturado</div>
          </div>
          <div class="kpi-card primary">
            <div class="kpi-label">Preço Médio / Pneu</div>
            <div class="kpi-value">{{ fmtR(kpis.valor_medio) }}</div>
            <div class="kpi-sub">Média paga por unidade</div>
          </div>
          
          <div class="kpi-card" v-if="kpis.km_disponivel">
            <div class="kpi-label">KM Médio Rodado</div>
            <div class="kpi-value">{{ fmtN(kpis.km_media) }}</div>
            <div class="kpi-sub">Média por pneu</div>
          </div>
          <div class="kpi-card" v-if="kpis.km_disponivel">
            <div class="kpi-label">KM - Melhor Pneu</div>
            <div class="kpi-value text-green">{{ fmtN(kpis.km_max) }}</div>
            <div class="kpi-sub">Maior durabilidade</div>
          </div>
          <div class="kpi-card" v-if="kpis.km_disponivel">
            <div class="kpi-label">KM - Pior Pneu</div>
            <div class="kpi-value text-red">{{ fmtN(kpis.km_min) }}</div>
            <div class="kpi-sub">Menor durabilidade</div>
          </div>
          <div class="kpi-card" v-if="!kpis.km_disponivel">
            <div class="kpi-label">KM Médio</div>
            <div class="kpi-value">—</div>
            <div class="kpi-sub">Aguardando dados SQL</div>
          </div>
        </div>
        <div v-else class="kpi-grid four-col">
          <div v-for="i in 8" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- SEÇÃO 1.2: INVESTIMENTO POR ANO -->
      <section class="v-block">
        <div class="section-heading">Investimento por Ano (Visão Macro)</div>
        <div v-if="lTimeline" class="skel" style="height:200px" />
        <div v-else-if="!timeline.series?.length" class="empty">Sem dados</div>
        <apexchart v-else type="bar" height="200" :options="barAnoOptions" :series="barAnoSeries" />
      </section>

      <!-- SEÇÃO 1.5: TRIMESTRES -->
      <section class="v-block">
        <div class="section-heading">Gasto por Trimestre (vs Ano Anterior)</div>
        <div class="kpi-grid four-col" v-if="!lTrimestres">
          <div v-for="q in trimestres" :key="q.trimestre" 
               class="kpi-card" 
               :class="getStatusClass(q)"
               :title="getTrimestreTooltip(q)">
            <div class="kpi-label">{{ q.trimestre }}</div>
            <div class="kpi-value">{{ fmtR(q.valor) }}</div>
            <div class="kpi-sub">
              <div class="variacao-row">
                <span class="variacao-label">vs ano anterior</span>
                <span class="variacao-value" :class="q.variacao_pct > 0 ? 'text-red' : 'text-green'">
                  {{ q.variacao_pct > 0 ? '↑' : '↓' }} {{ Math.abs(q.variacao_pct) }}%
                </span>
              </div>
              <div class="status-row">
                <span class="status-badge" :class="getStatusBadgeClass(q)">
                  {{ getStatusLabel(q) }}
                </span>
                <div class="status-detail">{{ getStatusDetail(q) }}</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="kpi-grid four-col">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>
      </section>

      <!-- SEÇÃO 2: GRÁFICOS PRINCIPAIS -->
      <div class="two-col">
        <!-- Tipo: Novo vs Recap -->
        <section class="v-block">
          <div class="section-heading">Tipo de Pneu</div>
          <div v-if="lTipo" class="skel" style="height:280px" />
          <div v-else-if="!porTipo.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutTipoOptions" :series="donutTipoSeries" />
        </section>

        <!-- Distribuição por Marca -->
        <section class="v-block">
          <div class="section-heading">
            Investimento por Marca
            <span v-if="porMarca.length > marcasLimit" class="heading-badge">
              Top {{ marcasLimit }} + {{ porMarca.length - marcasLimit }} outras
            </span>
          </div>
          <div v-if="lMarca" class="skel" style="height:280px" />
          <div v-else-if="!porMarca.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="280" :options="barMarcaOptions" :series="barMarcaSeries" />
        </section>
      </div>

      <!-- SEÇÃO 3: FORNECEDOR E EIXO -->
      <div class="two-col">
        <!-- Distribuição por Fornecedor -->
        <section class="v-block">
          <div class="section-heading">Investimento por Fornecedor</div>
          <div v-if="lFornecedor" class="skel" style="height:280px" />
          <div v-else-if="!porFornecedor.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutFornecedorOptions" :series="donutFornecedorSeries" />
        </section>

        <!-- Distribuição por Eixo -->
        <section class="v-block">
          <div class="section-heading">Distribuição por Eixo</div>
          <div v-if="lEixo" class="skel" style="height:280px" />
          <div v-else-if="!porEixo.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutEixoOptions" :series="donutEixoSeries" />
        </section>
      </div>

      <!-- SEÇÃO 4: DISTRIBUIÇÃO POR MEDIDA E ESTADO -->
      <div class="two-col">
        <!-- Por Medida -->
        <section class="v-block">
          <div class="section-heading">Distribuição por Aro</div>
          <div v-if="lMedida" class="skel" style="height:280px" />
          <div v-else-if="!porMedida.length" class="empty">Sem dados</div>
          <apexchart v-else type="bar" height="280" :options="barMedidaOptions" :series="barMedidaSeries" />
        </section>

        <!-- Por Estado -->
        <section class="v-block">
          <div class="section-heading">Distribuição por Estado (UF)</div>
          <div v-if="lEstado" class="skel" style="height:280px" />
          <div v-else-if="!porEstado.length" class="empty">Sem dados</div>
          <apexchart v-else type="donut" height="280" :options="donutEstadoOptions" :series="donutEstadoSeries" />
        </section>
      </div>

      <!-- SEÇÃO 5: GASTOS POR MÊS -->
      <section class="v-block">
        <div class="section-heading">Gastos por Mês</div>
        <div v-if="lTimeline" class="skel" style="height:300px" />
        <div v-else-if="!timeline.series?.length" class="empty">Sem dados</div>
        <apexchart v-else type="area" height="340" :options="areaTimelineOptions" :series="areaTimelineSeries" />
      </section>

      <!-- SEÇÃO 6: PERFORMANCE POR FILIAL -->
      <section class="v-block">
        <div class="section-heading">
          Performance por Filial
          <button v-if="filtroFilial" class="clear-filter-btn" @click="limparFiltroFilial">
            ✕ {{ filtroFilial.replace('Gritsch ', '') }}
          </button>
        </div>
        <div v-if="lFilial" class="skel" style="height:400px" />
        <div v-else-if="!filialDashboard.length" class="empty">Sem dados</div>
        <div v-else class="filial-dashboard">
          <div class="filial-grid">
            <div v-for="f in filialDashboard" :key="f.filial" 
                 class="filial-card"
                 :class="[getFilialStatusClass(f), filtroFilial === f.filial ? 'filial-selected' : '']"
                 @click="selecionarFilial(f.filial)">
              <div class="filial-header">
                <span class="filial-nome">{{ f.filial.replace('Gritsch ', '') }}</span>
                <span class="filial-status" :class="getFilialStatusBadge(f)">
                  {{ getFilialStatusLabel(f) }}
                </span>
              </div>
              <div class="filial-kpis">
                <div class="filial-kpi">
                  <span class="kpi-label">Veículos</span>
                  <span class="kpi-value">{{ f.placas }}</span>
                </div>
                <div class="filial-kpi">
                  <span class="kpi-label">Investimento</span>
                  <span class="kpi-value">{{ fmtR(f.valor) }}</span>
                </div>
                <div class="filial-kpi">
                  <span class="kpi-label">Custo/Veículo</span>
                  <span class="kpi-value">{{ fmtR(f.custo_por_veiculo) }}</span>
                </div>
              </div>
              <div class="filial-metrics">
                <div class="metric-row">
                  <span class="metric-label">Emergência</span>
                  <div class="metric-bar-wrap">
                    <div class="metric-bar" :class="getEmergenciaClass(f.emergencia_pct)" 
                         :style="{ width: Math.min(f.emergencia_pct, 100) + '%' }"></div>
                  </div>
                  <span class="metric-value" :class="getEmergenciaClass(f.emergencia_pct)">
                    {{ f.emergencia_pct }}%
                  </span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Pneus/Veículo</span>
                  <div class="metric-bar-wrap">
                    <div class="metric-bar" :class="getPneusVeiculoClass(f.pneus_por_veiculo)"
                         :style="{ width: Math.min(f.pneus_por_veiculo / 15 * 100, 100) + '%' }"></div>
                  </div>
                  <span class="metric-value">{{ f.pneus_por_veiculo }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SEÇÃO 7: TOP VEÍCULOS -->
      <section class="v-block">
        <div class="section-heading">
          <span v-if="filtroFilial">
            📍 {{ filtroFilial.replace('Gritsch ', '') }} - 
          </span>
          Veículos com Maior Investimento
          <div class="legend-row">
            <span><span class="legend-dot bg-green"></span> Normal</span>
            <span><span class="legend-dot bg-yellow"></span> > 15% da Média</span>
            <span><span class="legend-dot bg-red"></span> > 30% da Média</span>
          </div>
        </div>
        <div v-if="lPlaca" class="skel" style="height:300px" />
        <div v-else-if="!porPlaca.length" class="empty">Sem dados</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th class="status-cell">Status</th>
                <th class="col-placa">Placa</th>
                <th>Veículo</th>
                <th class="col-qty">Qtd Pneus</th>
                <th class="col-val">Valor Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in veiculosComAlerta" :key="i" :class="getVeiculoRowClass(row)">
                <td class="status-cell">
                  <span class="status-dot" :class="getVeiculoDotClass(row)" :title="row.alerta"></span>
                </td>
                <td class="mono fw-bold">{{ row.placa }}</td>
                <td>{{ row.veiculo }}</td>
                <td class="col-qty mono">{{ row.quantidade }}</td>
                <td class="col-val mono">{{ fmtR(row.valor) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- SEÇÃO 8: RADAR DE ANOMALIAS (CUSTO E TEMPO) -->
      <section class="v-block">
        <div class="section-heading">
          <span>⚠️ Radar de Anomalias (Consumo Excessivo e Trocas Prematuras)</span>
          <button class="reload-btn" @click="loadAnomalias" :disabled="lAnomalias">
            {{ lAnomalias ? '⏳ Carregando...' : '🔄 Atualizar' }}
          </button>
        </div>

        <div v-if="lAnomalias" class="skel" style="height:300px" />

        <div v-else-if="anomalias && (anomalias.destruidores?.length || anomalias.prematuras?.length)">
          <!-- KPIs Resumo -->
          <div class="km-resumo-grid" v-if="anomalias.resumo" style="grid-template-columns: repeat(3, 1fr);">
            <div class="km-resumo-card">
              <span class="km-resumo-label">Destruidores Acima da Média</span>
              <span class="km-resumo-value text-red">{{ anomalias.resumo.total_acima_media }}</span>
              <span class="km-resumo-sub">placas críticas</span>
            </div>
            <div class="km-resumo-card">
              <span class="km-resumo-label">Mortes Prematuras</span>
              <span class="km-resumo-value text-yellow">{{ anomalias.resumo.total_trocas_prematuras }}</span>
              <span class="km-resumo-sub">trocas < 180 dias</span>
            </div>
            <div class="km-resumo-card">
              <span class="km-resumo-label">Potencial Desperdício / Sinistro</span>
              <span class="km-resumo-value">{{ fmtR(anomalias.resumo.valor_potencial_desperdicio) }}</span>
              <span class="km-resumo-sub">capital imobilizado/perdido</span>
            </div>
          </div>

          <!-- Tabelas Paralelas -->
          <div class="anomalias-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 16px;">
            <!-- Ranking Destruidores -->
            <div>
              <div class="section-heading" style="margin-bottom: 8px; font-size: 0.9rem; font-weight: 600;">🚚 Maiores Consumidores (Destruidores)</div>
              <div class="table-wrap" style="max-height:400px; overflow-y: auto;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Placa</th>
                      <th>Veículo</th>
                      <th class="right">Total Pneus / Ano</th>
                      <th>Gasto (R$)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(r, i) in anomalias.destruidores" :key="i" :class="r.alerta_consumo !== 'NORMAL' ? (r.alerta_consumo.includes('CRÍTICO') ? 'row-critical' : 'row-warning') : ''">
                      <td class="mono fw-bold">{{ r.placa }}</td>
                      <td>{{ r.veiculo }}</td>
                      <td class="right mono fw-bold text-red">{{ r.total_pneus }}</td>
                      <td class="mono">{{ fmtR(r.valor_total) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Trocas Prematuras -->
            <div>
              <div class="section-heading" style="margin-bottom: 8px; font-size: 0.9rem; font-weight: 600;">⏱️ Trocas Prematuras / Mortalidade</div>
              <div class="table-wrap" style="max-height:400px; overflow-y: auto;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Placa</th>
                      <th>Data Anterior</th>
                      <th>Data Troca</th>
                      <th class="right">Dias</th>
                      <th>Motivo Suspeito</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(r, i) in anomalias.prematuras" :key="i" :class="r.intervalo_dias < 120 ? 'row-critical' : 'row-warning'">
                      <td class="mono fw-bold">{{ r.placa }}</td>
                      <td class="mono">{{ r.data_anterior.slice(8,10) + '/' + r.data_anterior.slice(5,7) }}</td>
                      <td class="mono">{{ r.data_troca.slice(8,10) + '/' + r.data_troca.slice(5,7) }}</td>
                      <td class="right mono fw-bold text-red">{{ r.intervalo_dias }} d</td>
                      <td>{{ r.motivo_suspeito }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty">Sem dados de anomalias detectados. Clique em "Atualizar".</div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  fetchPneusFiltros, fetchPneusKpis, fetchPneusTabela,
  fetchPneusPorFilial, fetchPneusPorMarca, fetchPneusPorFornecedor,
  fetchPneusPorEixo, fetchPneusPorMedida, fetchPneusPorEstado,
  fetchPneusPorTipo, fetchPneusTimeline, fetchPneusPorPlaca, fetchPneusTrimestres,
  fetchAnomaliasPneu
} from '../api/pneus.js'

// Estado dos filtros
const filtros = ref({ anos: [], filiais: [], marcas: [], fornecedores: [], eixos: [], medidas: [], aros: [] })
const filtroAno = ref('')
const filtroFilial = ref('')
const filtroMarca = ref('')
const filtroFornecedor = ref('')
const filtroAro = ref('')
const filtroMedida = ref('')
const filialSelecionada = ref('')

// Dados
const kpis = ref({})
const porTipo = ref([])
const porFilial = ref([])
const porMarca = ref([])
const porFornecedor = ref([])
const porEixo = ref([])
const porMedida = ref([])
const porEstado = ref([])
const timeline = ref({})
const porPlaca = ref([])
const trimestres = ref([])
const anomalias = ref({ destruidores: [], prematuras: [], resumo: {} })


// Loading states
const lKpis = ref(true)
const lTipo = ref(true)
const lFilial = ref(true)
const lMarca = ref(true)
const lFornecedor = ref(true)
const lEixo = ref(true)
const lMedida = ref(true)
const lEstado = ref(true)
const lTimeline = ref(true)
const lPlaca = ref(true)
const lTrimestres = ref(true)
const lAnomalias = ref(false)


// Formatters
function fmtR(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
function fmtN(v) {
  if (v == null) return '—'
  return Number(v).toLocaleString('pt-BR')
}

// Labels das colunas
const LABELS = {
  n_fogo: 'Nº Fogo', dot: 'DOT', data_envio: 'Data Envio', filial: 'Filial',
  placa: 'Placa', veiculo: 'Veículo', marca: 'Marca', modelo: 'Modelo',
  medida: 'Medida', eixo: 'Eixo', estado_pneu: 'Tipo', fornecedor: 'Fornecedor',
  nf: 'NF', valor_un: 'R$/Un', total: 'Total',
}
function colLabel(col) { return LABELS[col] || col }
function isNumeric(col) { return ['valor_un', 'total'].includes(col) }
function fmtCell(val, col) {
  if (val == null || val === '') return '—'
  if (['valor_un', 'total'].includes(col)) return fmtR(val)
  if (col === 'data_envio' && val) {
    const d = new Date(val)
    if (!isNaN(d)) return d.toLocaleDateString('pt-BR')
  }
  return val
}

// Funções de status dos trimestres
function getStatusClass(q) {
  if (q.variacao_real_pct < 0) return 'status-good'
  if (q.variacao_industria_pct <= 0) return 'status-ok'
  return 'status-alert'
}

function getStatusBadgeClass(q) {
  if (q.variacao_real_pct < 0) return 'badge-green'
  if (q.variacao_industria_pct <= 0) return 'badge-yellow'
  return 'badge-red'
}

function getStatusLabel(q) {
  if (q.variacao_real_pct < 0) return 'Eficiente'
  if (q.variacao_industria_pct <= 0) return 'Em linha'
  return 'Atenção'
}

function getStatusDetail(q) {
  if (q.variacao_real_pct < 0) return 'Preço subiu menos que inflação'
  if (q.variacao_industria_pct <= 0) return 'Acompanhou mercado'
  
  // Motivos para atenção - priorizar o mais relevante
  if (q.variacao_industria_pct > 15) return 'Mercado de borracha em alta'
  if (q.variacao_real_pct > 20) return 'Acima significativo da inflação'
  if (q.variacao_placas_pct > 10) return 'Frota cresceu ' + q.variacao_placas_pct + '%'
  if (Math.abs(q.variacao_industria_pct) > Math.abs(q.variacao_real_pct)) return 'Acompanhou alta da indústria'
  return 'Revisar negociação'
}

function getTrimestreTooltip(q) {
  return `${q.trimestre} ${Math.abs(q.valor || 0).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}\n` +
    `───────────────\n` +
    `Variação nominal: ${q.variacao_pct > 0 ? '+' : ''}${q.variacao_pct}%\n` +
    `Variação real (IPCA): ${q.variacao_real_pct > 0 ? '+' : ''}${q.variacao_real_pct}%\n` +
    `vs Indústria (IPP): ${q.variacao_industria_pct > 0 ? '+' : ''}${q.variacao_industria_pct}%\n` +
    `───────────────\n` +
    `Frota: ${q.placas} veículos (${q.variacao_placas_pct > 0 ? '+' : ''}${q.variacao_placas_pct}%)`
}

// Dashboard de Filiais
const filialDashboard = computed(() => {
  const data = porFilial.value || []
  if (!data.length) return []
  
  // Calcular custo por veículo para cada filial
  return data.map(f => ({
    ...f,
    custo_por_veiculo: f.placas > 0 ? f.valor / f.placas : 0
  })).sort((a, b) => b.valor - a.valor)
})

// Funções de status para filial
function getFilialStatusClass(f) {
  const emerg = f.emergencia_pct || 0
  const mediaPneus = kpis.value.pneus_por_veiculo || 5
  if (emerg > 50 || f.pneus_por_veiculo > mediaPneus * 1.5) return 'filial-critical'
  if (emerg > 30 || f.pneus_por_veiculo > mediaPneus * 1.2) return 'filial-warning'
  return 'filial-ok'
}

function getFilialStatusBadge(f) {
  const emerg = f.emergencia_pct || 0
  const mediaPneus = kpis.value.pneus_por_veiculo || 5
  if (emerg > 50 || f.pneus_por_veiculo > mediaPneus * 1.5) return 'badge-red'
  if (emerg > 30 || f.pneus_por_veiculo > mediaPneus * 1.2) return 'badge-yellow'
  return 'badge-green'
}

function getFilialStatusLabel(f) {
  const emerg = f.emergencia_pct || 0
  const mediaPneus = kpis.value.pneus_por_veiculo || 5
  if (emerg > 50 || f.pneus_por_veiculo > mediaPneus * 1.5) return 'Crítico'
  if (emerg > 30 || f.pneus_por_veiculo > mediaPneus * 1.2) return 'Atenção'
  return 'OK'
}

function getEmergenciaClass(pct) {
  if (pct > 50) return 'metric-critical'
  if (pct > 30) return 'metric-warning'
  return 'metric-ok'
}

function getPneusVeiculoClass(val) {
  const media = kpis.value.pneus_por_veiculo || 5
  if (val > media * 1.5) return 'metric-critical'
  if (val > media * 1.2) return 'metric-warning'
  return 'metric-ok'
}

// Veículos com Alertas
const veiculosComAlerta = computed(() => {
  let data = porPlaca.value || []
  
  if (!data.length) return []
  
  const mediaFrota = kpis.value.ticket_medio_veiculo || 0
  
  return data.slice(0, 20).map(v => {
    // Calculamos o desvio em relação à média de investimento por veículo da frota
    const desvio = mediaFrota > 0 ? (v.valor / mediaFrota) : 1
    
    let alerta = "Gasto dentro da média"
    let nivel = 'normal'
    
    if (desvio > 1.30) {
      alerta = `Gasto ${(desvio * 100 - 100).toFixed(0)}% ACIMA da média da frota`
      nivel = 'critical'
    } else if (desvio > 1.15) {
      alerta = `Gasto ${(desvio * 100 - 100).toFixed(0)}% ACIMA da média da frota`
      nivel = 'warning'
    }
    
    return {
      ...v,
      alerta,
      nivel
    }
  })
})

function getVeiculoRowClass(row) {
  if (row.nivel === 'critical') return 'row-critical'
  if (row.nivel === 'warning') return 'row-warning'
  return ''
}

function getVeiculoDotClass(row) {
  if (row.nivel === 'critical') return 'dot-red'
  if (row.nivel === 'warning') return 'dot-yellow'
  return 'dot-green'
}

// Funções de controle
function selecionarFilial(filial) {
  if (filtroFilial.value === filial) {
    filtroFilial.value = ''
  } else {
    filtroFilial.value = filial
  }
  loadAll()
}

function limparFiltroFilial() {
  filtroFilial.value = ''
  loadAll()
}

// Params para API
const params = () => ({
  ano: filtroAno.value,
  filial: filtroFilial.value,
  marca: filtroMarca.value,
  fornecedor: filtroFornecedor.value,
  aro: filtroAro.value,
  medida: filtroMedida.value,
})

// Carregamento de dados
async function loadAll() {
  const p = params()
  lKpis.value = true; lTipo.value = true; lFilial.value = true
  lMarca.value = true; lFornecedor.value = true; lEixo.value = true
  lMedida.value = true; lEstado.value = true; lTimeline.value = true
  lPlaca.value = true
  lTrimestres.value = true

  try {
    const [k, t, fm, ma, fo, ex, me, es, tl, pl, tr] = await Promise.all([
      fetchPneusKpis(p),
      fetchPneusPorTipo(p),
      fetchPneusPorFilial(p),
      fetchPneusPorMarca(p),
      fetchPneusPorFornecedor(p),
      fetchPneusPorEixo(p),
      fetchPneusPorMedida(p),
      fetchPneusPorEstado(p),
      fetchPneusTimeline({ filial: p.filial, marca: p.marca, fornecedor: p.fornecedor }),
      fetchPneusPorPlaca({ ...p, limit: 20 }),
      fetchPneusTrimestres(p),
    ])
    kpis.value = k
    porTipo.value = t
    porFilial.value = fm
    porMarca.value = ma
    porFornecedor.value = fo
    porEixo.value = ex
    porMedida.value = me
    porEstado.value = es
    timeline.value = tl
    porPlaca.value = pl
    trimestres.value = tr
  } catch (e) {
    console.error('Pneus: erro ao carregar', e)
  }
  lKpis.value = false; lTipo.value = false; lFilial.value = false
  lMarca.value = false; lFornecedor.value = false; lEixo.value = false
  lMedida.value = false; lEstado.value = false; lTimeline.value = false
  lPlaca.value = false
  lTrimestres.value = false

  // Carregar anomalias automaticamente junto com os demais dados
  loadAnomalias()
}

async function loadAnomalias() {
  lAnomalias.value = true
  try {
    const p = params()
    const data = await fetchAnomaliasPneu({
      filial: p.filial,
      ano: p.ano,
    })
    anomalias.value = data || { destruidores: [], prematuras: [], resumo: {} }
  } catch (e) {
    console.error('Pneus: erro ao carregar anomalias', e)
    anomalias.value = { destruidores: [], prematuras: [], resumo: {} }
  }
  lAnomalias.value = false
}

onMounted(async () => {
  try {
    const f = await fetchPneusFiltros()
    filtros.value = f
  } catch (e) {
    console.error('Pneus: erro ao carregar filtros', e)
  }
  loadAll()
})

// Cores
const COLORS = ['#C41230', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16', '#6366F1']

// Gráficos

// Barra: Gasto por Ano (Comparativo Macro)
const barAnoOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { 
    categories: (timeline.value.anos || []).map(a => String(a)),
    labels: { style: { fontWeight: 600 } }
  },
  yaxis: { labels: { formatter: v => fmtR(v) } },
  colors: ['#3B82F6'],
  plotOptions: { bar: { borderRadius: 6, columnWidth: '35%', dataLabels: { position: 'top' } } },
  dataLabels: { 
    enabled: true, 
    formatter: v => fmtR(v),
    offsetY: -20,
    style: { fontSize: '10px', colors: ['#334155'] }
  },
  grid: { strokeDashArray: 4 }
}))

const barAnoSeries = computed(() => {
  const series = timeline.value.series || []
  const data = series.map(s => {
    return s.dados.reduce((sum, d) => sum + (d.valor || 0), 0)
  })
  return [{ name: 'Gasto Total', data }]
})

// Donut: Tipo (Novo vs Recap)
const donutTipoOptions = computed(() => ({
  labels: porTipo.value.map(t => t.estado_pneu),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: ['#10B981', '#F59E0B'],
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutTipoSeries = computed(() => porTipo.value.map(t => t.quantidade))

// Barra: Marca - Top 10 + Outros
const marcasLimit = 10
const marcasTop = computed(() => {
  const data = porMarca.value
  if (!data || !Array.isArray(data) || !data.length) return []
  
  // Filtra marcas válidas
  const validMarcas = data.filter(m => {
    const nome = m.marca
    return nome && String(nome).trim() !== '' && String(nome) !== 'nan' && String(nome) !== 'None'
  })
  
  if (!validMarcas.length) return []
  
  // Ordena por valor decrescente
  const sorted = [...validMarcas].sort((a, b) => (b.valor || 0) - (a.valor || 0))
  
  if (sorted.length <= marcasLimit) return sorted
  
  const top = sorted.slice(0, marcasLimit)
  const resto = sorted.slice(marcasLimit)
  const totalResto = resto.reduce((sum, m) => sum + (m.valor || 0), 0)
  const qtdResto = resto.reduce((sum, m) => sum + (m.quantidade || 0), 0)
  
  return [...top, { 
    marca: `${resto.length} outras`, 
    valor: totalResto, 
    quantidade: qtdResto,
    valor_medio: qtdResto > 0 ? totalResto / qtdResto : 0,
    isOutros: true 
  }]
})

const barMarcaOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { 
    categories: marcasTop.value.map(m => m.marca), 
    labels: { 
      style: { fontSize: '11px' },
      formatter: v => fmtR(v) // Os valores em dinheiro agora ficam na base (X)
    } 
  },
  yaxis: { 
    labels: { 
      show: true // Os nomes das marcas agora aparecem sem formatação de moeda (Y)
    } 
  },
  colors: marcasTop.value.map(m => m.isOutros ? '#94a3b8' : '#C41230'),
  plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
  dataLabels: { enabled: false },
  tooltip: {
    y: {
      formatter: (v, { dataPointIndex }) => {
        const item = marcasTop.value[dataPointIndex]
        return `${fmtR(v)} (${item?.quantidade || 0} pneus · Média: ${fmtR(item?.valor_medio)}/un)`
      }
    }
  }
}))
const barMarcaSeries = computed(() => [{ name: 'Valor', data: marcasTop.value.map(m => m.valor) }])

// Donut: Fornecedor
const donutFornecedorOptions = computed(() => ({
  labels: porFornecedor.value.map(f => f.fornecedor),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: COLORS,
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutFornecedorSeries = computed(() => porFornecedor.value.map(f => f.quantidade))

// Donut: Eixo
const donutEixoOptions = computed(() => ({
  labels: porEixo.value.map(e => e.eixo),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: ['#C41230', '#3B82F6', '#10B981', '#F59E0B'],
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutEixoSeries = computed(() => porEixo.value.map(e => e.quantidade))

// Barra: Filial
const barFilialOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { categories: porFilial.value.map(f => f.filial), labels: { style: { fontSize: '10px' }, rotate: -45 } },
  yaxis: [
    { title: { text: 'Valor (R$)' }, labels: { formatter: v => fmtR(v) } },
    { opposite: true, title: { text: 'Qtd' }, labels: { formatter: v => Math.round(v) } },
  ],
  colors: ['#C41230', '#3B82F6'],
  plotOptions: { bar: { borderRadius: 4 } },
  dataLabels: { enabled: false },
}))
const barFilialSeries = computed(() => [
  { name: 'Valor', type: 'column', data: porFilial.value.map(f => f.valor) },
  { name: 'Quantidade', type: 'column', data: porFilial.value.map(f => f.quantidade) },
])

// Barra: Medida
const barMedidaOptions = computed(() => ({
  chart: { toolbar: { show: false } },
  xaxis: { categories: porMedida.value.map(m => m.medida), labels: { style: { fontSize: '11px' }, formatter: v => Math.round(v) } },
  yaxis: { labels: { show: true } },
  colors: ['#3B82F6'],
  plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
  dataLabels: { enabled: false },
}))
const barMedidaSeries = computed(() => [{ name: 'Quantidade', data: porMedida.value.map(m => m.quantidade) }])


// Donut: Estado (UF)
const donutEstadoOptions = computed(() => ({
  labels: porEstado.value.map(e => e.estado),
  legend: { position: 'bottom', fontSize: '12px' },
  colors: COLORS,
  dataLabels: { enabled: true, formatter: v => v.toFixed(1) + '%' },
}))
const donutEstadoSeries = computed(() => porEstado.value.map(e => e.valor))

// Área: Gastos por Mês (com comparação por ano)
const TIMELINE_COLORS = ['#C41230', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
const areaTimelineOptions = computed(() => {
  const tl = timeline.value
  const meses = tl.meses || []
  const series = tl.series || []
  const lastIdx = series.length - 1
  // Último ano = linha grossa sólida + fill; anos anteriores = tracejado sem fill
  const dashArray = series.map((_, i) => i === lastIdx ? 0 : 5)
  const widths = series.map((_, i) => i === lastIdx ? 3 : 2)
  const fillOpacity = series.map((_, i) => i === lastIdx ? 0.3 : 0)
  // Cores: último ano (mais recente) = vermelho, anteriores = cores progressivas
  const colors = TIMELINE_COLORS.slice(0, series.length).reverse()
  return {
    chart: { toolbar: { show: false } },
    xaxis: { categories: meses, labels: { style: { fontSize: '11px' } } },
    yaxis: { labels: { formatter: v => fmtR(v) } },
    colors,
    stroke: { curve: 'smooth', width: widths, dashArray },
    fill: { type: 'solid', opacity: fillOpacity },
    dataLabels: { enabled: false },
    legend: { position: 'top', fontSize: '13px', fontWeight: 500 },
    tooltip: { y: { formatter: v => fmtR(v) } },
  }
})
const areaTimelineSeries = computed(() => {
  const tl = timeline.value
  if (!tl.series) return []
  return tl.series.map(s => ({
    name: `${s.ano}`,
    data: s.dados.map(d => d.valor),
  }))
})

</script>

<style scoped>
.page { min-height: 100vh; background: var(--void); }

.topbar {
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  padding: 12px 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}
.topbar-main { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.topbar-left { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.logo {
  font-size: 13px; font-weight: 700; color: #1e293b;
  display: flex; align-items: center; gap: 8px;
}
.divider { color: #cbd5e1; font-weight: 400; }
.title-group { display: flex; flex-direction: column; gap: 1px; }
.subtitle { font-size: 14px; font-weight: 600; color: #1e293b; }
.page-subtitle { font-size: 11px; color: #94a3b8; font-weight: 400; }

.topbar-center { flex: 1; }
.filters { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 2px; }
.filter-group label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.filter-group select {
  padding: 5px 10px; border: 1px solid #e2e8f0; border-radius: 6px;
  font-size: 12px; color: #1e293b; background: #fff; min-width: 120px;
  cursor: pointer;
}
.filter-group select:focus { outline: none; border-color: #C41230; }

.page-body { padding: 24px; }

.v-block {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 20px; margin-bottom: 20px;
}
.section-heading {
  font-size: 13px; font-weight: 700; color: #1e293b;
  margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.04em;
  display: flex; align-items: center; gap: 8px;
}
.heading-badge {
  font-size: 10px; font-weight: 500; color: #64748b;
  background: #f1f5f9; padding: 2px 8px; border-radius: 4px;
  text-transform: none; letter-spacing: normal;
}

/* KPI Grid */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.kpi-grid.four-col { grid-template-columns: repeat(4, 1fr); }
.kpi-card {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 16px; text-align: center;
  display: flex; flex-direction: column; justify-content: center;
}
.kpi-card.primary { background: #fef2f2; border-color: #fecaca; }
.kpi-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #1e293b; }
.kpi-value.silver { font-size: 20px; color: #334155; }
.kpi-card.primary .kpi-value { color: #C41230; }
.kpi-sub { font-size: 11px; color: #94a3b8; margin-top: 4px; }

/* Trimestres - Status Styles */
.status-good { border-left: 4px solid #10b981; background: #f0fdf4; }
.status-ok { border-left: 4px solid #f59e0b; background: #fffbeb; }
.status-alert { border-left: 4px solid #ef4444; background: #fef2f2; }

.variacao-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.variacao-label { font-size: 10px; color: #64748b; }
.variacao-value { font-size: 13px; font-weight: 600; }

.status-row { text-align: center; margin-top: 4px; }
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.badge-green { background: #d1fae5; color: #065f46; }
.badge-yellow { background: #fef3c7; color: #92400e; }
.badge-red { background: #fee2e2; color: #991b1b; }

.status-detail { 
  font-size: 9px; 
  color: #64748b; 
  margin-top: 4px; 
  font-style: italic;
}

.row-sb { display: flex; align-items: center; justify-content: space-between; }
.text-red { color: #ef4444; font-weight: 600; }
.text-green { color: #10b981; font-weight: 600; }
.text-neutral { color: #94a3b8; }
.text-muted { color: #94a3b8; }
.fs-10 { font-size: 10px; }
.mb-1 { margin-bottom: 4px; }
.pt-1 { padding-top: 6px; }
.border-t { border-top: 1px solid #e2e8f0; }
/* Table Layout Fixes */
.data-table th.col-qty, .data-table td.col-qty { text-align: right; width: 100px; padding-right: 20px; }
.data-table th.col-val, .data-table td.col-val { text-align: right; width: 150px; padding-right: 20px; }
.data-table th.col-avg, .data-table td.col-avg { text-align: right; width: 130px; padding-right: 20px; }
.data-table th.col-placa, .data-table td.col-placa { width: 100px; }

.badge-alert {
  position: absolute; right: 2px; top: 50%; transform: translateY(-50%);
  cursor: help; font-size: 11px;
}

.fw-600 { font-weight: 600; }
.flex { display: flex; align-items: center; }
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }

.info-icon {
  font-style: normal;
  color: #3b82f6;
  cursor: help;
  font-size: 11px;
  line-height: 1;
}
.info-icon:hover { color: #1d4ed8; }
.kpi-skel { height: 90px; border-radius: 8px; background: #f1f5f9; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

/* Table */
.table-wrap { overflow-x: auto; }
.data-table {
  width: 100%; border-collapse: collapse; font-size: 12px;
}
.data-table th {
  text-align: left; padding: 8px 10px; border-bottom: 2px solid #e2e8f0;
  font-size: 10px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
}
.data-table td {
  padding: 8px 10px; border-bottom: 1px solid #f1f5f9; color: #1e293b;
}
.data-table tbody tr:hover { background: #fafbfc; }
.data-table tbody tr.row-warning { }
.data-table tbody tr.row-critical { }
.right { text-align: right; }
.mono { font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }

.empty {
  text-align: center; padding: 40px; color: #94a3b8; font-size: 13px;
}
.skel {
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Dashboard de Filiais */
.filial-dashboard {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filial-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.filial-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
  border-left: 4px solid #10b981;
}

.filial-card.filial-warning { border-left-color: #f59e0b; }
.filial-card.filial-critical { border-left-color: #ef4444; }
.filial-card.filial-selected { 
  border: 2px solid #3b82f6; 
  cursor: pointer;
}
.filial-card:hover { cursor: pointer; }

.clear-filter-btn {
  margin-left: auto;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 10px;
  cursor: pointer;
  font-weight: 500;
}
.clear-filter-btn:hover { background: #2563eb; }

.filial-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.filial-nome {
  font-weight: 600;
  font-size: 13px;
  color: #1e293b;
}

.filial-status {
  font-size: 9px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: uppercase;
}

.badge-green { background: #d1fae5; color: #065f46; }
.badge-yellow { background: #fef3c7; color: #92400e; }
.badge-red { background: #fee2e2; color: #991b1b; }

.filial-kpis {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.filial-kpi {
  text-align: center;
}

.filial-kpi .kpi-label {
  display: block;
  font-size: 9px;
  color: #64748b;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.filial-kpi .kpi-value {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.filial-metrics {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-label {
  font-size: 10px;
  color: #64748b;
  width: 70px;
  flex-shrink: 0;
}

.metric-bar-wrap {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.metric-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.metric-bar.metric-ok { background: #10b981; }
.metric-bar.metric-warning { background: #f59e0b; }
.metric-bar.metric-critical { background: #ef4444; }

.metric-value {
  font-size: 11px;
  font-weight: 600;
  color: #1e293b;
  width: 35px;
  text-align: right;
}

.metric-value.metric-ok { color: #10b981; }
.metric-value.metric-warning { color: #f59e0b; }
.metric-value.metric-critical { color: #ef4444; }

/* Tabela de Veículos */
.status-cell {
  width: 30px;
  text-align: center;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-green { background: #10b981; }
.dot-yellow { background: #f59e0b; }
.dot-red { background: #ef4444; }

.alerta-icon {
  margin-left: 4px;
  cursor: help;
}

.legend-row {
  display: flex;
  gap: 12px;
  font-size: 10px;
  color: #64748b;
  margin-left: auto;
  font-weight: 400;
  text-transform: none;
  letter-spacing: normal;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.legend-dot.bg-green { background: #10b981; }
.legend-dot.bg-yellow { background: #f59e0b; }
.legend-dot.bg-red { background: #ef4444; }

/* Relatório KM/Pneu */
.km-resumo-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}
.km-resumo-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.km-resumo-label {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.km-resumo-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.km-table tbody tr.row-km-ref { background: #fffbeb; }
.km-table tbody tr.row-km-miss { background: #fef2f2; }
.km-table td { font-size: 11px; }
.km-table th { font-size: 10px; }

.reload-btn {
  margin-left: auto;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}
.reload-btn:hover:not(:disabled) { background: #e2e8f0; }
.reload-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.text-blue { color: #3b82f6; }

@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
  .km-resumo-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .km-resumo-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
