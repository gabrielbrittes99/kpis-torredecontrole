<template>
  <div class="gp-page">
    <header class="gp-header">
      <h1>Central de Alertas e Tomada de Decisão</h1>
      <p style="color:var(--text3); margin-top:4px;">Indicadores de performance e avisos de Manutenção de Pneus para a Frota.</p>
    </header>

    <!-- INDICADORES RESUMO -->
    <div class="kpi-grid">
      <div class="kpi-card kpi-red">
        <span class="kpi-val">{{ alertasRodizio.length }}</span>
        <span class="kpi-lbl">Veículos Precisando de Rodízio</span>
      </div>
      <div class="kpi-card kpi-yellow">
        <span class="kpi-val">{{ dash?.em_uso || 0 }}</span>
        <span class="kpi-lbl">Pneus Ativos na Frota</span>
      </div>
    </div>

    <!-- PAINEL DE ALERTA: RODÍZIO -->
    <section class="gp-section">
      <div class="alert-panel-header">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--red)"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <h3>Rodízio Recomendado (Giro Contínuo > 7.000 KM)</h3>
      </div>
      
      <div v-if="alertasRodizio.length > 0" class="alerts-grid">
        <div v-for="a in alertasRodizio" :key="a.numero_fogo" class="alert-card">
          <div class="ac-head"><strong>Placa: {{ a.placa }}</strong> <span class="badge badge-outline">{{ posLabel(a.posicao) }}</span></div>
          <div class="ac-body">
            <span class="ac-fogo">Nº Fogo: <strong>{{ a.numero_fogo }}</strong></span>
            <div style="font-size: 11px; margin-top:4px;">Excesso detectado:</div>
            <div class="ac-progress">
              <div class="ac-bar" :style="{ width: Math.min(100, (a.km_rodado / a.limite) * 100) + '%' }"></div>
            </div>
            <div class="ac-km">{{ a.km_rodado.toLocaleString('pt-BR') }} KM (Limite Ideal: {{ a.limite.toLocaleString('pt-BR') }} KM)</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>Toda a frota está em conformidade com o cronograma de rodízios no momento.</p>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchGPDashboard } from '../api/gestaoPneus.js'

const dash = ref(null)
const alertasRodizio = ref([])

const posLabel = (p) => {
  const map = { E1_ESQ: 'E1 Esq', E1_DIR: 'E1 Dir', E2_ESQ_EXT: 'E2 Esq Ext', E2_ESQ_INT: 'E2 Esq Int', E2_DIR_INT: 'E2 Dir Int', E2_DIR_EXT: 'E2 Dir Ext', E3_ESQ_EXT: 'E3 Esq Ext', E3_ESQ_INT: 'E3 Esq Int', E3_DIR_INT: 'E3 Dir Int', E3_DIR_EXT: 'E3 Dir Ext', ESTEPE_1: 'Estepe 1', ESTEPE_2: 'Estepe 2' }
  return map[p] || p
}

async function loadData() {
  try {
    dash.value = await fetchGPDashboard()
    alertasRodizio.value = dash.value.alertas_rodizio || []
  } catch(e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>

<style scoped>
.gp-page { padding: 28px 32px; width: 100%; max-width: none; }
.gp-header h1 { font-size: 22px; font-weight: 800; margin-bottom: 8px; color: var(--text); }
.gp-section { background: #fff; border: 1px solid var(--border); border-radius: 20px; padding: 32px; box-shadow: var(--shadow-sm); margin-bottom: 32px; }

/* KPI Cards */
.kpi-grid { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 32px; }
.kpi-card { background: #fff; border: 1px solid var(--border); border-radius: 16px; padding: 20px 24px; min-width: 250px; flex: 1; display: flex; flex-direction: column; gap: 6px; box-shadow: var(--shadow-sm); transition: transform 0.2s; }
.kpi-val { font-size: 32px; font-weight: 800; color: var(--text); line-height: 1.1; letter-spacing: -0.02em; }
.kpi-lbl { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text3); }
.kpi-red .kpi-val { color: var(--red); }
.kpi-yellow .kpi-val { color: var(--yellow); }

/* Alertas Rodízio */
.alert-panel-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
.alert-panel-header h3 { font-size: 18px; font-weight: 800; color: var(--text); margin: 0; }
.alerts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }

.alert-card { background: linear-gradient(135deg, var(--red) 0%, #b91c1c 100%); border-radius: 16px; padding: 20px; color: #fff; box-shadow: 0 8px 24px rgba(220, 38, 38, 0.2); display: flex; flex-direction: column; gap: 12px; transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.1); }
.alert-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(220, 38, 38, 0.3); }

.ac-head { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(255,255,255,0.3); padding-bottom: 12px; font-size: 15px; }
.badge-outline { background: rgba(255,255,255,0.15) !important; color: #fff !important; border: 1px solid rgba(255,255,255,0.4); }

.ac-body { display: flex; flex-direction: column; gap: 8px; }
.ac-fogo { font-size: 13px; opacity: 0.9; }
.ac-progress { height: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; overflow: hidden; margin-top: 4px; }
.ac-bar { height: 100%; background: #fbbf24; border-radius: 4px; }
.ac-km { font-size: 12px; font-weight: 700; text-align: right; margin-top: 8px; color: #fca5a5; }

.empty-state { text-align: center; color: var(--text3); padding: 40px; font-size: 15px; font-weight: 500; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; }
</style>
