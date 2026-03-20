<template>
  <header class="topbar">
    <div class="topbar-main">
      <div class="topbar-left">
        <span class="logo">
          GRITSCH <span class="divider">//</span>
          <div class="title-group">
            <span class="subtitle">{{ title }}</span>
            <span v-if="subtitle" class="page-subtitle">{{ subtitle }}</span>
          </div>
        </span>
      </div>
      
      <div class="topbar-center">
        <!-- Seletor de Período Inteligente -->
        <div v-if="showPeriod" class="smart-period">
          <select v-model="filtrosState.selecao.modoTempo" class="mode-select">
            <option value="mes">Mensal</option>
            <option value="bimestre">Bimestral</option>
            <option value="semestre">Semestral</option>
            <option value="ano">Anual</option>
            <option value="personalizado">Personalizado</option>
          </select>

          <div class="period-controls">
            <!-- Mensal -->
            <template v-if="filtrosState.selecao.modoTempo === 'mes'">
              <select v-model="filtrosState.selecao.mes" class="period-pill">
                <option v-for="(m, i) in filtrosState.opcoes.meses" :key="i" :value="i + 1">{{ m }}</option>
              </select>
            </template>

            <!-- Bimestral -->
            <template v-if="filtrosState.selecao.modoTempo === 'bimestre'">
              <select v-model="filtrosState.selecao.bimestre" class="period-pill">
                <option v-for="(b, i) in filtrosState.opcoes.bimestres" :key="i" :value="i + 1">{{ b }}</option>
              </select>
            </template>

            <!-- Semestral -->
            <template v-if="filtrosState.selecao.modoTempo === 'semestre'">
              <select v-model="filtrosState.selecao.semestre" class="period-pill">
                <option v-for="(s, i) in filtrosState.opcoes.semestres" :key="i" :value="i + 1">{{ s }}</option>
              </select>
            </template>

            <!-- Anual / Default Year -->
            <template v-if="filtrosState.selecao.modoTempo !== 'personalizado'">
              <select v-model="filtrosState.selecao.ano" class="period-pill">
                <option v-for="y in filtrosState.opcoes.anos" :key="y" :value="y">{{ y }}</option>
              </select>
            </template>

            <!-- Personalizado -->
            <template v-if="filtrosState.selecao.modoTempo === 'personalizado'">
              <input type="date" v-model="filtrosState.selecao.data_inicio" class="date-input">
              <span class="to">até</span>
              <input type="date" v-model="filtrosState.selecao.data_fim" class="date-input">
            </template>
          </div>
        </div>
      </div>
      
      <div class="topbar-right">
        <button v-if="showFilters" 
                class="btn-advanced" 
                :class="{ active: showAdvanced }" 
                @click="showAdvanced = !showAdvanced">
          <span class="icon">⚙</span> Filtros Avançados
          <span v-if="filtrosAtivosCount > 0" class="badge">{{ filtrosAtivosCount }}</span>
        </button>
        <div v-if="ultimaAtualiz" class="update-badge">{{ ultimaAtualiz }}</div>
        <slot name="right"></slot>
      </div>
    </div>

    <!-- Gaveta de Filtros Avançados -->
    <transition name="slide">
      <div v-if="showAdvanced && showFilters" class="filter-drawer">
        <div class="drawer-content">
          <div class="filter-item">
            <label>Região</label>
            <select v-model="filtrosState.selecao.regiao">
              <option :value="null">Todas</option>
              <option v-for="r in filtrosState.opcoes.regioes" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          
          <div class="filter-item">
            <label>UF</label>
            <select v-model="filtrosState.selecao.estado">
              <option :value="null">Todas</option>
              <option v-for="e in filtrosState.opcoes.estados" :key="e" :value="e">{{ e }}</option>
            </select>
          </div>
          
          <div class="filter-item">
            <label>Filial</label>
            <select v-model="filtrosState.selecao.filial">
              <option :value="null">Todas</option>
              <option v-for="f in filtrosState.opcoes.filiais" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          
          <div class="filter-item">
            <label>Grupo</label>
            <select v-model="filtrosState.selecao.grupo">
              <option :value="null">Todos</option>
              <option v-for="g in filtrosState.opcoes.grupos_veiculo" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>

          <div class="filter-item">
            <label>Combustível</label>
            <select v-model="filtrosState.selecao.combustivel" class="comb-select">
              <option :value="null">Todos</option>
              <option v-for="c in filtrosState.opcoes.combustiveis" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <button @click="limparFiltros" class="btn-clear" v-if="temFiltrosAtivos">
            Limpar Filtros
          </button>
        </div>
      </div>
    </transition>
  </header>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useFiltrosStore } from '../stores/filtros'

defineProps({
  title: { type: String, default: 'Torre de Controle' },
  subtitle: { type: String, default: '' },
  showFilters: { type: Boolean, default: true },
  showPeriod: { type: Boolean, default: true },
  ultimaAtualizacao: { type: String, default: '' }
})

const filtrosState = useFiltrosStore()
const showAdvanced = ref(false)

const filtrosAtivosCount = computed(() => {
  const s = filtrosState.selecao
  let count = 0
  if (s.regiao) count++
  if (s.estado) count++
  if (s.filial) count++
  if (s.grupo) count++
  if (s.combustivel) count++
  return count
})

const temFiltrosAtivos = computed(() => filtrosAtivosCount.value > 0)

const limparFiltros = () => filtrosState.limparFiltrosGlobais()

onMounted(() => filtrosState.loadOpcoesFiltros())
</script>

<style scoped>
.topbar {
  background: white; border-bottom: 1px solid #e2e8f0;
  position: sticky; top: 0; z-index: 1000;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

.topbar-main {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; height: 64px; gap: 24px;
}

.topbar-left { flex-shrink: 0; width: 300px; }
.logo { font-size: 16px; font-weight: 800; letter-spacing: 0.05em; color: #0f172a; display: flex; align-items: center; white-space: nowrap; }
.logo .divider { color: #C41230; margin: 0 12px; font-weight: 400; opacity: 0.5; }
.title-group { display: flex; flex-direction: column; line-height: 1.2; }
.logo .subtitle { color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
.page-subtitle { color: #94a3b8; font-size: 10px; font-weight: 500; text-transform: none; letter-spacing: 0; }

.topbar-center { flex: 1; display: flex; justify-content: center; }

/* Smart Period Selector */
.smart-period {
  display: flex; items: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 4px; gap: 4px;
}
.mode-select {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 12px; font-weight: 700; color: #0f172a; padding: 6px 12px; outline: none; cursor: pointer;
}
.period-controls { display: flex; align-items: center; gap: 4px; }
.period-pill {
  background: transparent; border: none; font-size: 12px; font-weight: 600; color: #475569; padding: 6px 8px; cursor: pointer; outline: none; transition: 0.2s; border-radius: 6px;
}
.period-pill:hover { background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

.date-input { border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; padding: 4px 8px; color: #475569; }
.to { font-size: 11px; color: #94a3b8; font-weight: 600; }

.topbar-right { flex-shrink: 0; display: flex; gap: 16px; align-items: center; width: 300px; justify-content: flex-end; }

.btn-advanced {
  display: flex; align-items: center; gap: 8px; background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 16px; 
  font-size: 12px; font-weight: 700; color: #475569; cursor: pointer; transition: all 0.2s; position: relative;
}
.btn-advanced:hover { border-color: #C41230; color: #C41230; }
.btn-advanced.active { background: #fff7ed; border-color: #C41230; color: #C41230; }
.btn-advanced .badge {
  position: absolute; top: -8px; right: -8px; background: #C41230; color: white; font-size: 10px; width: 18px; height: 18px; 
  display: flex; items: center; justify-content: center; border-radius: 50%; box-shadow: 0 2px 4px rgba(249,115,22,0.3);
}

.update-badge { font-size: 11px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-weight: 500; }

/* Filter Drawer */
.filter-drawer {
  background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 16px 40px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}
.drawer-content { display: flex; gap: 24px; align-items: flex-end; flex-wrap: wrap; }
.filter-item { display: flex; flex-direction: column; gap: 6px; }
.filter-item label { font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 2px; }
.filter-item select {
  min-width: 140px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 12px; font-weight: 600; color: #1e293b; outline: none; transition: 0.2s;
}
.filter-item select:focus { border-color: #C41230; box-shadow: 0 0 0 3px rgba(249,115,22,0.1); }
.filter-item .comb-select { color: #C41230; }

.btn-clear {
  background: #fee2e2; border: none; color: #ef4444; padding: 10px 16px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; transition: 0.2s;
}
.btn-clear:hover { background: #fecaca; }

/* Transitions */
.slide-enter-active, .slide-leave-active { transition: all 0.3s ease-out; max-height: 200px; opacity: 1; }
.slide-enter-from, .slide-leave-to { max-height: 0; opacity: 0; padding-top: 0; padding-bottom: 0; overflow: hidden; }
</style>
