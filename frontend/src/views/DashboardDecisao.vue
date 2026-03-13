<template>
  <div class="page-container decisao-page">
    <div class="page-header">
      <div class="header-main">
        <h1 class="page-title">Painel de Decisão</h1>
        <p class="page-subtitle">Ações prioritárias para otimização da operação em tempo real.</p>
      </div>
      <div class="header-actions">
        <button @click="atualizar" class="btn-refresh" :disabled="carregando">
          <span class="refresh-icon" :class="{ spinning: carregando }">↻</span>
          {{ carregando ? 'Atualizando...' : 'Atualizar Dados' }}
        </button>
      </div>
    </div>

    <div v-if="carregando && !kpis" class="loading-state">
      <div class="spinner"></div>
      <p>Analisando indicadores...</p>
    </div>

    <div v-else class="decisao-grid">
      <!-- Coluna Esquerda: Diagnóstico e Ações -->
      <div class="col-main">
        <!-- 5 Seconds Dashboard (Traffic Lights) -->
        <div class="status-row">
          <div class="status-card" :class="kpis?.statusOrcamento">
            <div class="status-indicator"></div>
            <div class="status-info">
              <span class="status-label">Orçamento</span>
              <span class="status-value">{{ kpis?.statusOrcamento === 'critico' ? 'Risco Alto' : 'Sob Controle' }}</span>
            </div>
          </div>
          <div class="status-card" :class="kpis?.veiculosComAlerta > 0 ? 'atencao' : 'ok'">
            <div class="status-indicator"></div>
            <div class="status-info">
              <span class="status-label">Frota</span>
              <span class="status-value">{{ kpis?.veiculosComAlerta }} Veículos Alerta</span>
            </div>
          </div>
          <div class="status-card" :class="kpis?.statusPrecos">
            <div class="status-indicator"></div>
            <div class="status-info">
              <span class="status-label">Preço Médio</span>
              <span class="status-value">Performance {{ kpis?.statusPrecos === 'ok' ? 'Boa' : 'Baixa' }}</span>
            </div>
          </div>
          <div class="status-card ok">
            <div class="status-indicator"></div>
            <div class="status-info">
              <span class="status-label">Saving Real</span>
              <span class="status-value">{{ fmtR(kpis?.savingMes) }}</span>
            </div>
          </div>
        </div>

        <!-- Ações Priorizadas -->
        <h2 class="section-title">Ações Priorizadas</h2>
        <div class="actions-list">
          <div v-for="acao in acoes" :key="acao.id" class="action-item" @click="abrirModal(acao)">
            <div class="action-icon">{{ acao.icon }}</div>
            <div class="action-content">
              <div class="action-header">
                <span class="action-title">{{ acao.titulo }}</span>
                <span class="action-impact" :class="acao.tipo">{{ acao.impacto }}</span>
              </div>
              <p class="action-desc">{{ acao.descricao }}</p>
            </div>
            <div class="action-chevron">›</div>
          </div>
        </div>
      </div>

      <!-- Coluna Direita: Painel do Diretor -->
      <div class="col-side">
        <div class="director-card health-card">
          <div class="card-label">Saúde da Operação</div>
          <div class="health-meta">
            <div class="health-score" :style="{ color: getHealthColor(kpis?.saudeOperacao) }">
              {{ kpis?.saudeOperacao }}%
            </div>
            <div class="health-bg">
              <div class="health-fill" :style="{ width: kpis?.saudeOperacao + '%', background: getHealthColor(kpis?.saudeOperacao) }"></div>
            </div>
          </div>
          <p class="health-status">{{ getHealthText(kpis?.saudeOperacao) }}</p>
        </div>

        <div class="director-card projection-card">
          <div class="card-label">Projeção de Fechamento</div>
          <div class="proj-value">{{ fmtR(estado.kpis?.projecao_valor) }}</div>
          <div class="proj-meta">
            <span class="meta-label">Meta Diária Necessária</span>
            <span class="meta-value">{{ fmtR((estado.kpis?.total_valor || 0) / 30) }}</span>
          </div>
          <div class="proj-bar">
            <div class="proj-fill" :style="{ width: Math.min(kpis?.percentualOrcamento || 0, 100) + '%' }"></div>
          </div>
          <div class="proj-footer">
            {{ kpis?.percentualOrcamento || 0 }}% do teto mensal consumido/projetado
          </div>
        </div>

        <div class="director-card abnormal-card">
          <div class="card-label">Gastos Anormais Detectados</div>
          <div class="abnormal-list">
            <div v-for="a in alertasCriticos" :key="a.id" class="abnormal-item">
              <span class="abnormal-dot"></span>
              <span class="abnormal-text">{{ a.titulo }}</span>
            </div>
            <div v-if="alertasCriticos.length === 0" class="empty-state">
              Nenhuma anomalia crítica hoje.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Ação -->
    <div v-if="modalAtivo" class="modal-overlay" @click.self="modalAtivo = null">
      <div class="modal-card">
        <div class="modal-header">
          <h2>{{ modalAtivo.titulo }}</h2>
          <button @click="modalAtivo = null" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="impact-banner">Impacto Estimado: {{ modalAtivo.impacto }}</div>
          <h3>Passo a Passo para Decisão:</h3>
          <ul class="steps-list">
            <li v-for="(p, i) in modalAtivo.passos" :key="i">
              <span class="step-num">{{ i + 1 }}</span>
              <span class="step-text">{{ p }}</span>
            </li>
          </ul>
        </div>
        <div class="modal-footer">
          <button @click="modalAtivo = null" class="btn-confirm">Entendido, Registrar Ação</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useTorreApi } from '../composables/useTorreApi'

const { estado, carregando, carregarTorre, getKpisDecisao } = useTorreApi()

const kpis = computed(() => getKpisDecisao())
const modalAtivo = ref(null)

const fmtR = v => v ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }) : 'R$ 0'

onMounted(() => {
  carregarTorre()
})

const atualizar = () => carregarTorre()

const alertasCriticos = computed(() => {
  return estado.alertas?.filter(a => a.nivel === 'critico').slice(0, 3) || []
})

const acoes = computed(() => {
  const list = []
  
  if (kpis.value?.statusOrcamento === 'critico') {
    list.push({
      id: 1,
      icon: '📉',
      titulo: 'Reduzir Meta Diária de Abastecimento',
      tipo: 'negativo',
      impacto: 'Impacto: -R$ 12.400 este mês',
      descricao: 'O ritmo atual excederá o orçamento em 15%. Recomenda-se limitar abastecimentos não-essenciais.',
      passos: [
        'Acessar plataforma TruckPag > Limites por Veículo',
        'Reduzir limites diários em 10% para a frota administrativa',
        'Notificar gestores de frota sobre a nova cota',
        'Monitorar variação na projeção em 48h'
      ]
    })
  }

  const veiculos = estado.alertas?.filter(a => a.id === 'consumo_anormal')
  if (veiculos?.length > 0) {
    list.push({
      id: 2,
      icon: '🚛',
      titulo: `Inspecionar ${veiculos.length} Veículos com Alto Consumo`,
      tipo: 'negativo',
      impacto: `Impacto: R$ 4.200/semana extra`,
      descricao: 'Detectamos desvio de consumo em veículos específicos. Pode indicar falha mecânica ou uso indevido.',
      passos: [
        'Citar placas em relatório de manutenção preventiva',
        'Verificar pressão dos pneus e filtros de ar',
        'Cruzar dados de telemetria com horários de abastecimento',
        'Entrevistar motoristas responsáveis'
      ]
    })
  }

  if (kpis.value?.savingMes > 5000) {
    list.push({
      id: 3,
      icon: '💰',
      titulo: 'Bonificar Melhores Compradores',
      tipo: 'positivo',
      impacto: `Resultado: +${fmtR(kpis.value?.savingMes)} de economia`,
      descricao: 'A frota está performando abaixo da média ANP. Reforçar o engajamento de uso dos postos preferenciais.',
      passos: [
        'Identificar motoristas com menor preço médio pago',
        'Enviar mensagem de feedback positivo via plataforma',
        'Divulgar ranking de melhores postos da semana para a equipe',
        'Manter estratégia de rota atual'
      ]
    })
  }

  list.push({
    id: 4,
    icon: '⛽',
    titulo: 'Bloquear 3 Postos Acima do Mercado',
    tipo: 'negativo',
    impacto: 'Economia: R$ 3.100/mês',
    descricao: 'Identificamos postos com preços > 10% acima da ANP municipal na sua rota frequente.',
    passos: [
      'Identificar razão social dos postos no relatório de Benchmark',
      'Acessar TruckPag > Gestão de Rede > Bloqueio de Postos',
      'Inserir o CNPJ dos postos identificados na lista negra',
      'Indicar postos vizinhos com melhor preço na rota'
    ]
  })

  return list
})

function abrirModal(acao) {
  modalAtivo.value = acao
}

function getHealthColor(score) {
  if (score > 80) return '#10b981'
  if (score > 50) return '#f59e0b'
  return '#ef4444'
}

function getHealthText(score) {
  if (score > 80) return 'Operação saudável e eficiente'
  if (score > 50) return 'Atenção necessária em pontos específicos'
  return 'Ações imediatas requeridas'
}
</script>

<style scoped>
.decisao-page { padding-bottom: 40px; }
.decisao-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
}

/* Status Cards (5 Seconds Dashboard) */
.status-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.status-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.1s;
}
.status-indicator { width: 12px; height: 12px; border-radius: 50%; background: #666; }
.status-card.ok .status-indicator { background: #10b981; box-shadow: 0 0 10px rgba(16,185,129,0.3); }
.status-card.atencao .status-indicator { background: #f59e0b; box-shadow: 0 0 10px rgba(245,158,11,0.3); }
.status-card.critico .status-indicator { background: #ef4444; box-shadow: 0 0 10px rgba(239,68,68,0.3); }

.status-info { display: flex; flex-direction: column; }
.status-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.5px; }
.status-value { font-size: 14px; font-weight: 700; color: var(--text); }

/* Ações */
.section-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 20px; }
.actions-list { display: flex; flex-direction: column; gap: 12px; }
.action-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.action-item:hover { border-color: var(--accent); background: var(--surface-hover); transform: translateX(4px); }
.action-icon { font-size: 24px; }
.action-content { flex: 1; }
.action-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.action-title { font-size: 15px; font-weight: 700; color: var(--text); }
.action-impact { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.action-impact.positivo { background: rgba(16,185,129,0.1); color: #10b981; }
.action-impact.negativo { background: rgba(239,68,68,0.1); color: #ef4444; }
.action-desc { font-size: 13px; color: var(--text-2); margin: 0; }
.action-chevron { color: var(--text-3); font-size: 20px; }

/* Lateral */
.col-side { display: flex; flex-direction: column; gap: 20px; }
.director-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
.card-label { font-size: 12px; font-weight: 600; color: var(--text-3); margin-bottom: 16px; text-transform: uppercase; }

.health-meta { margin-bottom: 12px; }
.health-score { font-size: 44px; font-weight: 800; line-height: 1; margin-bottom: 12px; }
.health-bg { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.health-fill { height: 100%; transition: width 1s ease-out; }
.health-status { font-size: 13px; color: var(--text-2); margin: 0; }

.proj-value { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 16px; }
.proj-meta { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px; }
.meta-label { color: var(--text-3); }
.meta-value { color: var(--text-2); font-weight: 600; }
.proj-bar { height: 6px; background: var(--border); border-radius: 3px; margin-bottom: 8px; overflow: hidden; }
.proj-fill { height: 100%; background: var(--accent); }
.proj-footer { font-size: 11px; color: var(--text-3); }

.abnormal-list { display: flex; flex-direction: column; gap: 10px; }
.abnormal-item { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--text-2); }
.abnormal-dot { width: 6px; height: 6px; border-radius: 50%; background: #ef4444; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.modal-card {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 20px;
  width: 100%;
  max-width: 500px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.5);
}
.modal-header {
  padding: 24px;
  background: var(--surface);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
}
.modal-header h2 { font-size: 18px; margin: 0; }
.btn-close { background: none; border: none; font-size: 28px; color: var(--text-3); cursor: pointer; }

.modal-body { padding: 24px; }
.impact-banner {
  background: rgba(16,185,129,0.1);
  color: #10b981;
  padding: 12px;
  border-radius: 8px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 24px;
}
.steps-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 16px; }
.steps-list li { display: flex; gap: 16px; }
.step-num {
  width: 24px;
  height: 24px;
  background: var(--accent);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.step-text { color: var(--text-2); font-size: 14px; line-height: 1.5; }

.modal-footer { padding: 24px; display: flex; flex-direction: column; gap: 12px; }
.btn-confirm {
  background: var(--accent);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
}

@keyframes spin { from {transform:rotate(0)} to {transform:rotate(360deg)} }
.refresh-icon.spinning { animation: spin 1s linear infinite; display: inline-block; }
</style>
