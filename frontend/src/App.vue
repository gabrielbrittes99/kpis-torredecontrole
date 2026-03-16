<template>
  <div class="shell" :class="{ 'sidebar-collapsed': collapsed }">
    <!-- Sidebar -->
    <nav class="sidebar" :class="{ collapsed }">
      <div class="sidebar-top">
        <div class="sidebar-logo">
          <div class="logo-mark">G</div>
          <span v-show="!collapsed" class="logo-text font-syne">Gritsch</span>
        </div>
        <button class="toggle-btn" @click="collapsed = !collapsed" :title="collapsed ? 'Expandir menu' : 'Recolher menu'">
          <span class="toggle-icon">{{ collapsed ? '☰' : '✕' }}</span>
        </button>
      </div>

      <div v-show="!collapsed" class="nav-section-label font-syne">Torre de Controle</div>

      <!-- Vigilância -->
      <button
        class="nav-item"
        :class="{ active: activeSection === 'vigilancia' }"
        @click="activeSection = 'vigilancia'"
        :title="collapsed ? 'Vigilância Constante' : ''"
      >
        <span class="nav-icon">🛡️</span>
        <span v-show="!collapsed" class="nav-label font-syne">Vigilância Constante</span>
      </button>

      <!-- Grupo Combustível -->
      <div class="nav-group">
        <button
          class="nav-item nav-group-header"
          :class="{ 'group-open': combustivelOpen, active: isCombustivelActive }"
          @click="collapsed ? (collapsed = false, combustivelOpen = true) : (combustivelOpen = !combustivelOpen)"
          :title="collapsed ? 'Combustível' : ''"
        >
          <span class="nav-icon">⛽</span>
          <span v-show="!collapsed" class="nav-label font-syne">Combustível</span>
          <span v-show="!collapsed" class="nav-arrow">{{ combustivelOpen ? '▾' : '▸' }}</span>
        </button>

        <div v-show="combustivelOpen && !collapsed" class="nav-sub">
          <button
            v-for="sub in combustivelSubs"
            :key="sub.id"
            class="nav-item nav-sub-item"
            :class="{ active: activeSection === sub.id }"
            @click="activeSection = sub.id"
          >
            <span class="nav-icon-sub">{{ sub.icon }}</span>
            <span class="nav-label font-syne">{{ sub.label }}</span>
          </button>
        </div>
      </div>

      <!-- Outros -->
      <button
        v-for="item in outrosNavItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeSection === item.id }"
        @click="activeSection = item.id"
        :title="collapsed ? item.label : ''"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-show="!collapsed" class="nav-label font-syne">{{ item.label }}</span>
      </button>

      <div class="sidebar-footer">
        <span v-show="!collapsed" class="sidebar-version mono">v2.0 · TruckPag</span>
      </div>
    </nav>

    <main class="main-content">
      <VigilanciaConstante   v-if="activeSection === 'vigilancia'" />
      <VisaoGeral            v-else-if="activeSection === 'visao-geral'" />
      <DashboardOperacional  v-else-if="activeSection === 'operacional'" />
      <DashboardDiretoria    v-else-if="activeSection === 'diretoria'" />
      <!-- legados mantidos -->
      <DashboardCombustivel  v-else-if="activeSection === 'combustivel'" />
      <DashboardPrecos       v-else-if="activeSection === 'precos'" />
      <DashboardFrota        v-else-if="activeSection === 'frota'" />
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VigilanciaConstante  from './views/VigilanciaConstante.vue'
import VisaoGeral           from './views/VisaoGeral.vue'
import DashboardCombustivel  from './views/DashboardCombustivel.vue'
import DashboardOperacional  from './views/DashboardOperacional.vue'
import DashboardPrecos      from './views/DashboardPrecos.vue'
import DashboardFrota       from './views/DashboardFrota.vue'
import DashboardDiretoria   from './views/DashboardDiretoria.vue'

const activeSection  = ref('vigilancia')
const combustivelOpen = ref(false)
const collapsed = ref(false)

const combustivelSubs = [
  { id: 'visao-geral',  icon: '📊', label: 'Visão Geral' },
  { id: 'operacional',  icon: '🎯', label: 'Visão Operacional' },
  { id: 'diretoria',    icon: '📈', label: 'Visão da Diretoria' },
]

const outrosNavItems = [
  { id: 'precos',  icon: '💹', label: 'Inteligência de Preços' },
  { id: 'frota',   icon: '🚛', label: 'Eficiência de Frota' },
]

const isCombustivelActive = computed(() =>
  combustivelSubs.some(s => s.id === activeSection.value)
)
</script>

<style>
/* Reset global */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--void); color: var(--text); font-family: 'Inter', sans-serif; }

.shell {
  display: flex;
  min-height: 100vh;
  background: var(--void);
}

/* ─── Sidebar ─────────────────────────────────────────────────────────────── */
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--deep);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 100;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar.collapsed {
  width: 68px;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 24px;
  margin-bottom: 16px;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}

.logo-mark {
  width: 36px;
  height: 36px;
  background: var(--orange);
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800;
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  flex-shrink: 0;
}

.logo-text {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--text);
  white-space: nowrap;
}

.toggle-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--s3);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  flex-shrink: 0;
}
.toggle-btn:hover {
  background: var(--s2);
}
.toggle-icon {
  font-size: 14px;
  color: var(--text2);
}

.nav-section-label {
  padding: 0 20px;
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
  margin-bottom: 12px;
  white-space: nowrap;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 20px;
  width: calc(100% - 16px);
  margin: 2px 8px;
  border-radius: 10px;
  background: none;
  border: none;
  color: var(--text2);
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
}
.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 12px 0;
  width: calc(100% - 12px);
  margin: 2px 6px;
}

.nav-item:hover {
  background: var(--s1);
  color: var(--text);
}

.nav-item.active {
  background: var(--orange-bg);
  color: var(--orange);
  font-weight: 600;
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  flex-shrink: 0;
  text-align: center;
}

.nav-label {
  font-size: 14px;
  flex: 1;
  white-space: nowrap;
}

.nav-arrow {
  font-size: 10px;
  color: var(--text3);
}

/* Sub-nav */
.nav-group { width: 100%; }

.nav-group-header.group-open {
  color: var(--text);
}

.nav-sub {
  padding-left: 8px;
}

.nav-sub-item {
  padding: 9px 20px;
  font-size: 13px;
}

.nav-icon-sub {
  font-size: 14px;
  width: 20px;
  flex-shrink: 0;
  text-align: center;
}

.sidebar-footer {
  margin-top: auto;
  padding: 16px 20px 0;
  border-top: 1px solid var(--border);
}

.sidebar-version {
  font-size: 11px;
  color: var(--text3);
  font-family: 'Inter', sans-serif;
}

/* ─── Main content ────────────────────────────────────────────────────────── */
.main-content {
  margin-left: 260px;
  flex: 1;
  min-width: 0;
  background: var(--void);
  height: 100vh;
  overflow-y: auto;
  transition: margin-left 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar-collapsed .main-content {
  margin-left: 68px;
}

@media (max-width: 768px) {
  .sidebar { width: 68px; }
  .sidebar.collapsed { width: 68px; }
  .logo-text, .nav-label, .nav-section-label, .sidebar-footer, .nav-arrow { display: none; }
  .sidebar-logo { justify-content: center; }
  .logo-mark { margin: 0; }
  .nav-item { padding: 14px; justify-content: center; }
  .nav-icon { width: auto; font-size: 20px; }
  .nav-sub { padding-left: 0; }
  .main-content { margin-left: 68px; }
  .sidebar-collapsed .main-content { margin-left: 68px; }
}
</style>
