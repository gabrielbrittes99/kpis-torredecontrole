<template>
  <div class="vigilancia-root animate-in">

    <!-- ZONA 1: Header Fixed -->
    <header class="v-header">
      <div class="header-left">
        <span class="logo">GRITSCH <span class="divider">//</span> <span class="subtitle">Torre de Decisão</span></span>
      </div>

      <div class="header-center">
        <div class="status-indicator" :class="getStatusGlobalClass">
          {{ getStatusGlobalText }}
        </div>
      </div>

      <div class="header-right">
        <div class="live-indicator">
          <div class="pulse-dot"></div>
          <span class="mono">ao vivo · TruckPag</span>
        </div>
        <div class="clock mono">{{ currentTime }}</div>
      </div>
    </header>

    <!-- ALERTAS CENTRALIZADOS -->
    <div class="alerts-container">
      <AlertasList :alertas="alertas" style="margin-bottom: 24px;" />

      <!-- Alerta de Recomendação Flex -->
      <div v-if="estado.flex" class="flex-recommendation-alert" :class="estado.flex.recomendacao.includes('ETANOL') ? 'etanol' : 'gasolina'">
        <div class="flex-alert-icon">{{ estado.flex.recomendacao.includes('ETANOL') ? '🍃' : '⛽' }}</div>
        <div class="flex-alert-content">
          <div class="flex-alert-title">RECOMENDAÇÃO FLEX: {{ estado.flex.recomendacao }}</div>
          <div class="flex-alert-desc">
            Análise regional indica economia potencial de <strong>{{ estado.flex.economia_potencial }}</strong> no custo por KM utilizando {{ estado.flex.recomendacao.split(' ').pop() }}.
          </div>
        </div>
      </div>
    </div>

    <!-- ZONA 2: Situation Bar -->
    <section class="v-situation-bar">
      <div class="status-card" v-for="card in situationCards" :key="card.label" :class="card.status">
        <div class="card-bar"></div>
        <div class="card-top-label mono">{{ card.label }}</div>
        <div class="card-main">
          <div class="card-value">{{ card.value }}</div>
          <div class="card-badge-verdict" :class="card.status">{{ card.verdict }}</div>
        </div>
        <div class="card-footer mono">
          <span class="subtext">{{ card.sub }}</span>
          <span class="detail">{{ card.detail }}</span>
        </div>
      </div>
    </section>

    <!-- ZONA 3: Main Layout -->
    <main class="v-main-layout">

      <!-- Coluna Esquerda -->
      <div class="col-left">

        <!-- Bloco Ações Agora -->
        <div class="v-block actions-block">
          <div class="section-title">O QUE FAZER AGORA <span class="action-count-badge">{{ pendentesCount }}</span></div>
          <div class="actions-grid">
            <div v-for="(acao, idx) in acoes" :key="idx" class="action-item" :class="acao.tipo" @click="abrirAcao(acao)">
              <div class="item-number-circle">{{ idx + 1 }}</div>
              <div class="item-body">
                <div class="item-title">{{ acao.titulo }}</div>
                <div class="item-desc mono">{{ acao.desc }}</div>
                <div class="item-footer">
                  <span class="impact-badge">{{ acao.impacto }}</span>
                  <span class="btn-ver">Ver →</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-grid">
          <!-- Onde Abastecer -->
          <div class="v-block">
            <div class="section-title">ONDE ABASTECER AGORA</div>
            <div class="posto-list">
              <div v-for="p in postos" :key="p.nome" class="posto-row">
                <div class="p-rank">{{ p.rank }}</div>
                <div class="p-info">
                  <div class="p-name">{{ p.nome }}</div>
                  <div class="p-city mono">{{ p.cidade }}</div>
                </div>
                <div class="p-price-area">
                  <div class="p-price">R$ {{ p.preco.toFixed(2) }}</div>
                  <div class="p-diff mono" :class="p.trend">{{ p.diff }}</div>
                </div>
                <div class="p-badge" :class="p.badgeClass">{{ p.badge }}</div>
              </div>
            </div>
          </div>

          <!-- Status Frota -->
          <div class="v-block">
            <div class="section-title">STATUS DA FROTA</div>
            <div class="frota-list">
              <div v-for="v in veiculos" :key="v.placa" class="frota-row">
                <div class="v-placa-badge" :class="v.status">{{ v.placa }}</div>
                <div class="v-info">
                  <div class="v-prob mono">{{ v.problema }}</div>
                  <div class="v-det mono">{{ v.detalhe }}</div>
                </div>
                <div class="v-kml" :class="v.kmlStatus">{{ v.kml }} k/L</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Coluna Direita (320px) -->
      <aside class="col-right">

        <!-- Análise Flex -->
        <div class="v-block side-block">
          <div class="label-tiny mono">EFICIÊNCIA FLEX — MÉDIA REGIÃO</div>
          <div class="flex-comparison">
            <div class="flex-item">
              <span class="f-label">GASOLINA</span>
              <span class="f-val">R$ {{ estado.flex?.gasolina_preco?.toFixed(2) }}</span>
              <span class="f-sub mono">Custo/KM: R$ 0,54</span>
            </div>
            <div class="flex-divider">vs</div>
            <div class="flex-item">
              <span class="f-label">ETANOL</span>
              <span class="f-val">R$ {{ estado.flex?.etanol_preco?.toFixed(2) }}</span>
              <span class="f-sub mono">Custo/KM: R$ 0,48</span>
            </div>
          </div>
          <div class="flex-ratio-bar">
            <div class="ratio-fill" :style="{ width: estado.flex?.ratio + '%' }"></div>
            <span class="ratio-text">{{ estado.flex?.ratio }}%</span>
          </div>
          <p class="label-sub" style="margin-top: 12px; font-size: 11px;">
            Ponto de equilíbrio ideal: <strong>70%</strong>. <br/>
            Atual: {{ estado.flex?.ratio }}%. {{ estado.flex?.recomendacao }}
          </p>
        </div>

        <!-- Projeção -->
        <div class="v-block side-block proj-block highlighted">
          <div class="label-tiny mono">PROJEÇÃO DE FECHAMENTO — {{ currentMonthName }} de {{ new Date().getFullYear() }}</div>
          <div class="proj-value" :class="{ critical: projecao > meta }">R$ {{ fmtN(projecao) }}</div>

          <div class="meta-comparison">
             <div class="meta-info">
               <span class="meta-label">META ORÇAMENTÁRIA (HISTÓRICO)</span>
               <span class="meta-val">R$ {{ fmtN(meta) }}</span>
             </div>
             <div class="meta-badge" :class="projecao > meta ? 'bad' : 'good'">
               {{ projecao > meta ? '▲ ACIMA' : '▼ OK' }}
             </div>
          </div>

          <div class="progress-section">
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: Math.min(100, (projecao/meta)*100) + '%' }" :class="{ critical: projecao > meta }"></div>
              <div class="meta-threshold" style="left: 100%"></div>
            </div>
            <div class="progress-footer mono">
              <span>R$ 0</span>
              <span>100% DA META</span>
            </div>
          </div>

          <div class="daily-metrics">
            <div class="metric-item">
              <div class="m-label mono">GASTO/DIA REAL (HOJE)</div>
              <div class="m-value" :class="{ red: gastoDia > metaDiaria }">R$ {{ fmtN(gastoDia) }}</div>
            </div>
            <div class="metric-divider"></div>
            <div class="metric-item">
              <div class="m-label mono">LIMITE DIÁRIO (HIST.)</div>
              <div class="m-value">R$ {{ fmtN(metaDiaria) }}</div>
            </div>
          </div>
        </div>

        <!-- IA de Mercado -->
        <div class="v-block side-block ia-block">
          <div class="ia-header">
            <div class="label-tiny mono">INTELIGÊNCIA DE MERCADO <span class="ia-live-badge">IA AO VIVO</span></div>
            <button class="btn-update mono" @click="fetchIntel" :disabled="iaLoading">
              <span class="icon" :class="{ rotate: iaLoading }">⟳</span>
              {{ iaLoading ? 'Consultando...' : 'Atualizar' }}
            </button>
          </div>
          <div v-if="iaLoading" class="ia-loading mono">
            Consultando inteligência...
          </div>
          <div v-else-if="intel" class="ia-content">
            <div class="ia-resumo mono">
               <span class="trend-icon">{{ intel.tendencia === 'alta' ? '▲' : '→' }}</span>
               {{ intel.resumo }}
            </div>
            <div v-for="(n, i) in intel.noticias" :key="i" class="ia-card" :class="n.impacto">
              <div class="ia-n-header">
                <span class="fonte mono">{{ n.fonte }}</span>
                <span class="impacto mono">{{ n.impacto }}</span>
              </div>
              <div class="ia-n-title">{{ n.titulo }}</div>
              <div class="ia-n-market mono" v-if="n.brent_usd">
                Brent: {{ n.brent_usd }} · Câmbio: {{ n.cambio }}
              </div>
            </div>
          </div>
        </div>

        <!-- Score de Saúde -->
        <div class="v-block side-block">
          <div class="label-tiny mono">SCORE DE SAÚDE</div>
          <div class="score-display">
            <div class="score-main">{{ avgScore }}%</div>
            <div class="score-metrics">
              <div v-for="(val, key) in scores" :key="key" class="score-row">
                <span class="mono">{{ keyMap[key] }}</span>
                <div class="score-bar-bg">
                  <div class="score-bar" :style="{ width: val + '%', background: getHealthColor(val) }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>

    </main>

    <!-- Modal Ação (V2.0) -->
    <Teleport to="body">
      <div v-if="modalAcao" class="modal-overlay" @click.self="modalAcao = null">
        <div class="modal-card animate-modal">
          <button class="modal-close" @click="modalAcao = null">×</button>
          <div class="modal-title" :class="modalAcao.tipo">{{ modalAcao.titulo }}</div>
          <div class="modal-sub">{{ modalAcao.desc }}</div>

          <div class="modal-steps">
            <div v-for="(p, i) in steps" :key="i" class="modal-step">
              <div class="step-num">{{ i + 1 }}</div>
              <div class="step-content">
                <div class="step-txt">{{ p.txt }}</div>
                <div class="step-sub">{{ p.sub }}</div>
              </div>
            </div>
          </div>

          <button class="modal-btn" :class="modalAcao.tipo">Executar Ação</button>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVigilanciaData } from '../composables/useVigilanciaData'
import { useMercadoIA } from '../composables/useMercadoIA'
import AlertasList from '../components/AlertasList.vue'
import { fetchAlertas } from '../api/alertas.js'

const { estado, carregando, ultimaAtualizacao, fetchTudo } = useVigilanciaData()
const { intel, loading: iaLoading, fetchIntel } = useMercadoIA()

const currentTime = ref(new Date().toLocaleTimeString('pt-BR'))
const alertas = ref([])
let timerId = null

onMounted(async () => {
  fetchTudo()
  fetchAlertas().then(d => alertas.value = d)
  timerId = setInterval(() => {
    currentTime.value = new Date().toLocaleTimeString('pt-BR')
  }, 1000)
  // Refresh data every 10 min as per TTL
  setInterval(fetchTudo, 600000)
})

onUnmounted(() => clearInterval(timerId))

// Mapeamentos e Computeds
const _hoje = new Date()
const periodo = computed(() => _hoje.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }))
const periodoLabel = _hoje.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
const currentMonthName = _hoje.toLocaleDateString('pt-BR', { month: 'long' })

const getStatusGlobalText = computed(() => {
  if (pendentesCount.value > 0) return '⚠ ATENÇÃO NECESSÁRIA'
  return '✓ OPERAÇÃO SAUDÁVEL'
})

const getStatusGlobalClass = computed(() => {
  if (pendentesCount.value > 0) return 'critical'
  return 'healthy'
})

const situationCards = computed(() => {
  const orc = estado.value.situacao?.orcamento || {}
  const veic = estado.value.situacao?.veiculos || {}
  const anp = estado.value.situacao?.preco_anp || {}
  const sav = estado.value.situacao?.saving || {}
  const pctHist = orc.pct_media_hist || 0
  const nVeic = veic.com_problema || 0
  const varAnp = anp.variacao_pct || 0
  return [
    {
      label: 'ORÇAMENTO DO MÊS',
      value: pctHist.toFixed(1) + '%',
      verdict: pctHist > 102 ? '▲ Agir Agora' : '✓ No Esperado',
      status: pctHist > 102 ? 'critical' : 'healthy',
      sub: `Proj. R$ ${fmtK(orc.projecao || 0)}`,
      detail: `Ref. hist. R$ ${fmtK(orc.referencia_hist || 0)}`
    },
    {
      label: 'VEÍCULOS COM PROBLEMA',
      value: nVeic,
      verdict: nVeic > 0 ? '⚠ Verificar' : '✓ No Esperado',
      status: nVeic > 0 ? 'warning' : 'healthy',
      sub: `de ${veic.ativos || 0} ativos`,
      detail: nVeic > 0 ? `Ex: ${(veic.lista_problema || [])[0]?.placa || '—'}` : 'Frota OK'
    },
    {
      label: 'PREÇO MÉDIO vs ANP',
      value: (varAnp > 0 ? '+' : '') + varAnp.toFixed(1) + '%',
      verdict: varAnp <= 0 ? '✓ Economizando' : '▲ Perdendo',
      status: varAnp <= 0 ? 'healthy' : 'critical',
      sub: anp.pago_medio ? `Pago R$ ${anp.pago_medio.toFixed(3)}` : 'Sem dados ANP',
      detail: anp.anp_medio ? `ANP R$ ${anp.anp_medio.toFixed(3)}` : ''
    },
    {
      label: 'SAVING ACUMULADO',
      value: 'R$ ' + fmtK(sav.valor || 0),
      verdict: '↑ Economia Real',
      status: 'info',
      sub: periodoLabel,
      detail: 'vs preço ANP mercado'
    }
  ]
})

const projecao   = computed(() => estado.value.situacao?.orcamento?.projecao     || 0)
const meta       = computed(() => estado.value.situacao?.orcamento?.referencia_hist || 0)
const gastoDia   = computed(() => estado.value.situacao?.orcamento?.media_diaria   || 0)
const metaDiaria = computed(() => {
  // Meta diária = referência histórica ÷ dias no mês
  const ref = estado.value.situacao?.orcamento?.referencia_hist || 0
  const diasMes = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()
  return ref > 0 ? ref / diasMes : 0
})
const diasRestantes = computed(() => estado.value.situacao?.orcamento?.dias_restantes || 0)

// Score sintético calculado a partir dos dados reais
const scores = computed(() => {
  const orc = estado.value.situacao?.orcamento || {}
  const anp = estado.value.situacao?.preco_anp || {}
  const veic = estado.value.situacao?.veiculos || {}
  const pct = orc.pct_media_hist || 100
  return {
    orcamento: Math.max(0, Math.min(100, Math.round(200 - pct))),
    precos:    anp.variacao_pct != null ? Math.max(0, Math.min(100, Math.round(100 - anp.variacao_pct * 5))) : 50,
    frota:     veic.ativos > 0 ? Math.round((1 - (veic.com_problema || 0) / veic.ativos) * 100) : 100,
    rota:      100,
  }
})
const avgScore = computed(() => {
  const vals = Object.values(scores.value)
  return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0
})

const keyMap = { precos: 'PREÇOS', frota: 'FROTA', orcamento: 'META', rota: 'ROTA' }

// Ações baseadas nas anomalias reais do backend
const acoes = computed(() => {
  const anom = estado.value.anomalias || []
  return anom.map(a => ({
    tipo: a.tipo === 'critica' || a.tipo === 'preco' ? 'critica' : 'atencao',
    titulo: (a.tipo === 'critica' || a.tipo === 'gasto') ? a.titulo : `Inspecionar ${a.titulo}`,
    desc: a.detalhe,
    impacto: a.valor
  }))
})
const pendentesCount = computed(() => (estado.value.anomalias || []).length)

const postos = [
  { rank: '①', nome: 'Ale Combustíveis', cidade: 'CURITIBA - BR-116', preco: 5.72, diff: '-5,9% ANP', trend: 'good', badge: 'MELHOR', badgeClass: 'good' },
  { rank: '②', nome: 'Raízen Ponta Grossa', cidade: 'CENTRO', preco: 5.78, diff: '-2,9% ANP', trend: 'good', badge: '', badgeClass: '' },
  { rank: '✕', nome: 'Ipiranga Cascavel', cidade: 'CASCAVEL - BR-376', preco: 6.34, diff: '+8,2% ANP', trend: 'bad', badge: 'EVITAR', badgeClass: 'bad' }
]

const veiculos = computed(() =>
  (estado.value.situacao?.veiculos?.lista_problema || []).map(v => ({
    placa: v.placa,
    problema: 'Consumo Crítico',
    detalhe: `KM/L atual: ${v.kml_atual} (média: ${v.kml_medio})`,
    status: 'critical',
    kml: v.kml_atual,
    kmlStatus: 'bad'
  }))
)

const modalAcao = ref(null)
const steps = [
  { txt: 'Contatar motorista via rádio', sub: 'Confirmar se houve abastecimento em rota não autorizada.' },
  { txt: 'Bloquear posto no cadastro', sub: 'Impedir novas transações neste CNPJ por 30 dias.' }
]

const abrirAcao = (acao) => { modalAcao.value = acao }

const fmtN = v => Number(v || 0).toLocaleString('pt-BR')
const fmtK = v => {
  const n = Number(v || 0)
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  return (n / 1000).toFixed(1) + 'k'
}

const getHealthColor = v => {
  if (v > 70) return 'var(--green)'
  if (v > 40) return 'var(--yellow)'
  return 'var(--red)'
}
</script>

<style scoped>
.vigilancia-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--void);
  padding: 0 40px 48px;
  overflow-y: auto;
}

/* Header */
.v-header {
  height: 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border2);
  margin-bottom: 24px;
}

.logo { font-size: 20px; font-weight: 800; color: var(--text); }
.logo .divider { color: var(--orange); margin: 0 4px; }
.logo .subtitle { color: var(--text3); font-weight: 600; font-size: 13px; text-transform: uppercase; }

.status-indicator {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 700;
  border-radius: 6px;
  background: white;
  border: 1px solid var(--border2);
}
.status-indicator.critical { color: var(--red); background: var(--red2); border-color: var(--red3); }
.status-indicator.healthy { color: var(--green); background: var(--green2); }

/* Alerts */
.alerts-container { margin-bottom: 32px; }

.flex-recommendation-alert {
  display: flex;
  gap: 16px;
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  border-left: 6px solid var(--orange);
  box-shadow: 0 4px 6px rgba(0,0,0,0.02);
  margin-top: 12px;
}
.flex-recommendation-alert.etanol { border-left-color: var(--green); }
.flex-recommendation-alert.gasolina { border-left-color: var(--blue); }
.flex-alert-icon { font-size: 24px; }
.flex-alert-title { font-weight: 800; font-size: 14px; margin-bottom: 2px; }
.flex-alert-desc { font-size: 13px; color: var(--text2); }

/* Situation Bar */
.v-situation-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.status-card {
  background: white;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid var(--border2);
  transition: transform 0.2s;
}
.status-card:hover { transform: translateY(-4px); }

.card-top-label { font-size: 10px; font-weight: 700; color: var(--text3); text-transform: uppercase; margin-bottom: 12px; }
.card-main { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
.card-value { font-size: 34px; font-weight: 800; line-height: 1; color: var(--text); }
.status-card.critical .card-value { color: var(--red); }
.status-card.warning .card-value { color: var(--yellow); }
.status-card.healthy .card-value { color: var(--green); }

.card-badge-verdict { font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 100px; }
.card-badge-verdict.critical { background: var(--red2); color: var(--red); }
.card-badge-verdict.healthy { background: var(--green2); color: #065F46; }

.card-footer { display: flex; flex-direction: column; gap: 4px; border-top: 1px solid var(--void); padding-top: 12px; }
.card-footer span { font-size: 11px; color: var(--text3); }

/* Layout Main */
.v-main-layout { display: grid; grid-template-columns: 1fr 360px; gap: 32px; }
@media (max-width: 1200px) { .v-main-layout { grid-template-columns: 1fr; } }

.v-block { background: white; border-radius: 16px; padding: 32px; border: 1px solid var(--border2); }
.section-title { font-size: 12px; font-weight: 800; color: var(--text3); margin-bottom: 24px; text-transform: uppercase; }

/* Flex Side Block */
.flex-comparison { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.flex-item { display: flex; flex-direction: column; }
.f-label { font-size: 10px; font-weight: 800; color: var(--text3); }
.f-val { font-size: 18px; font-weight: 800; color: var(--text); }
.f-sub { font-size: 10px; color: var(--text3); margin-top: 2px; }
.flex-divider { color: var(--text3); font-weight: 800; font-size: 12px; opacity: 0.3; }
.flex-ratio-bar { height: 12px; background: var(--void); border-radius: 10px; overflow: hidden; position: relative; }
.ratio-fill { height: 100%; background: var(--orange); }
.ratio-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 9px; font-weight: 800; }

.proj-block.highlighted {
  border: 1px solid var(--border);
  background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.proj-block.highlighted::before {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 100px; height: 100px;
  background: radial-gradient(circle at top right, var(--orange-bg), transparent);
  pointer-events: none;
}

.proj-value { font-size: 36px; font-weight: 800; line-height: 1; margin: 12px 0 24px 0; color: var(--text); letter-spacing: -0.02em; }
.proj-value.critical { color: var(--red); }

.meta-comparison { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; padding: 12px; background: white; border-radius: 12px; border: 1px solid var(--void); }
.meta-info { display: flex; flex-direction: column; }
.meta-label { font-size: 9px; font-weight: 800; color: var(--text3); }
.meta-val { font-size: 14px; font-weight: 700; color: var(--text2); }
.meta-badge { font-size: 10px; font-weight: 800; padding: 4px 8px; border-radius: 6px; }
.meta-badge.bad { background: var(--red2); color: var(--red); }
.meta-badge.good { background: var(--green2); color: var(--green); }

.progress-section { margin-bottom: 32px; }
.progress-bar-bg { height: 8px; background: var(--void); border-radius: 4px; position: relative; margin-bottom: 8px; }
.progress-bar-fill { height: 100%; border-radius: 4px; background: var(--green); transition: width 0.6s ease; }
.progress-bar-fill.critical { background: var(--red); }
.meta-threshold { position: absolute; top: -4px; width: 2px; height: 16px; background: var(--text); opacity: 0.2; }
.progress-footer { display: flex; justify-content: space-between; font-size: 10px; color: var(--text3); font-weight: 700; }

.daily-metrics { display: flex; align-items: center; gap: 20px; }
.metric-item { flex: 1; }
.m-label { font-size: 9px; font-weight: 800; color: var(--text3); margin-bottom: 4px; }
.m-value { font-size: 18px; font-weight: 800; color: var(--text); }
.m-value.red { color: var(--red); }
.m-value.yellow { color: var(--yellow); }
.metric-divider { width: 1px; height: 30px; background: var(--void); }

.action-item {
  display: flex; gap: 16px; background: var(--s3); padding: 20px; border-radius: 12px; margin-bottom: 12px; cursor: pointer; border: 1px solid var(--border2);
}
.action-item:hover { border-color: var(--orange); }
.item-number-circle { width: 28px; height: 28px; background: var(--orange); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; flex-shrink: 0; }
.action-item.critica .item-number-circle { background: var(--red); }
.item-title { font-weight: 700; font-size: 14px; margin-bottom: 4px; }
.item-desc { font-size: 12px; color: var(--text2); }

.posto-row { display: grid; grid-template-columns: 24px 1fr 100px 60px; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--void); }
.p-name { font-weight: 700; font-size: 13px; }
.p-price { font-weight: 800; text-align: right; }
.p-diff { font-size: 11px; text-align: right; font-weight: 700; }
.p-diff.good { color: var(--green); }
.p-diff.bad { color: var(--red); }

.score-main { font-size: 48px; font-weight: 800; color: var(--green); }
.score-metrics { margin-top: 12px; }
.score-row { display: grid; grid-template-columns: 80px 1fr; align-items: center; gap: 12px; margin-bottom: 8px; }
.score-bar-bg { height: 6px; background: var(--void); border-radius: 4px; overflow: hidden; }
.score-bar { height: 100%; }

.ia-loading {
  padding: 40px;
  text-align: center;
  font-size: 13px;
  color: var(--text3);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  width: 100%;
  max-width: 460px;
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  position: relative;
}

.modal-close {
  position: absolute;
  top: 20px;
  right: 20px;
  border: none;
  background: var(--void);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--text3);
}

.modal-title { font-size: 20px; font-weight: 800; margin-bottom: 8px; color: var(--text); }
.modal-title.critica { color: var(--red); }
.modal-title.atencao { color: var(--yellow); }

.modal-sub { font-size: 14px; color: var(--text2); margin-bottom: 32px; line-height: 1.5; }

.modal-steps { display: flex; flex-direction: column; gap: 20px; margin-bottom: 32px; }
.modal-step { display: flex; gap: 16px; align-items: flex-start; }
.step-num {
  width: 28px;
  height: 28px;
  background: var(--orange-bg);
  color: var(--orange);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 12px;
  flex-shrink: 0;
}

.step-txt { font-weight: 700; font-size: 14px; color: var(--text); margin-bottom: 2px; }
.step-sub { font-size: 13px; color: var(--text3); line-height: 1.4; }

.modal-btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 12px;
  background: var(--orange);
  color: white;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: opacity 0.2s;
}
.modal-btn:hover { opacity: 0.9; }
.modal-btn.critica { background: var(--red); }
.modal-btn.atencao { background: var(--yellow); }

.animate-modal { animation: modalScale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
@keyframes modalScale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }

.animate-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
