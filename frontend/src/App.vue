<template>
  <div class="shell">
    <!-- Sidebar -->
    <nav class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">G</div>
        <span class="logo-text font-syne">Gritsch</span>
      </div>

      <div class="nav-section-label font-syne">Torre de Controle</div>

      <button
        v-for="item in navItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeSection === item.id }"
        @click="activeSection = item.id"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label font-syne">{{ item.label }}</span>
      </button>

      <div class="sidebar-footer">
        <span class="sidebar-version mono">v2.0 · TruckPag</span>
      </div>
    </nav>

    <main class="main-content">
      <VigilanciaConstante  v-if="activeSection === 'vigilancia'" />
      <DashboardCombustivel v-else-if="activeSection === 'combustivel'" />
      <DashboardPrecos      v-else-if="activeSection === 'precos'" />
      <DashboardFrota       v-else-if="activeSection === 'frota'" />
      <DashboardOperacional  v-else-if="activeSection === 'operacional'" />
      <DashboardDiretoria    v-else-if="activeSection === 'diretoria'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import VigilanciaConstante  from './views/VigilanciaConstante.vue'
import DashboardCombustivel  from './views/DashboardCombustivel.vue'
import DashboardOperacional  from './views/DashboardOperacional.vue'
import DashboardPrecos      from './views/DashboardPrecos.vue'
import DashboardFrota       from './views/DashboardFrota.vue'
import DashboardDiretoria   from './views/DashboardDiretoria.vue'

const activeSection = ref('vigilancia')

const navItems = [
  { id: 'vigilancia',  icon: '🛡️', label: 'Vigilância Constante' },
  { id: 'combustivel', icon: '⛽', label: 'Visão Gerencial' },
  { id: 'precos',      icon: '📊', label: 'Inteligência de Preços' },
  { id: 'frota',       icon: '🚛', label: 'Eficiência de Frota' },
  { id: 'operacional',  icon: '🎯', label: 'Visão Operacional' },
  { id: 'diretoria',    icon: '📈', label: 'Visão da Diretoria' },
]
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

/* Sidebar Slate Dark */
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--deep);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 32px 0;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px 32px;
  margin-bottom: 24px;
}

.logo-mark {
  width: 36px;
  height: 36px;
  background: var(--orange);
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
}

.logo-text {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--text);
}

.nav-section-label {
  padding: 0 24px;
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
  margin-bottom: 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 24px;
  width: calc(100% - 32px);
  margin: 0 16px;
  border-radius: 8px;
  background: none;
  border: none;
  color: var(--text2);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  font-weight: 500;
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
}

.nav-label {
  font-size: 14px;
}

.sidebar-footer {
  margin-top: auto;
  padding: 16px 24px 0;
  border-top: 1px solid var(--border);
}

.sidebar-version {
  font-size: 11px;
  color: var(--text3);
  font-family: 'Inter', sans-serif;
}

/* Main content */
.main-content {
  margin-left: 260px;
  flex: 1;
  min-width: 0;
  background: var(--void);
  height: 100vh;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .sidebar { width: 64px; }
  .logo-text, .nav-label, .nav-section-label, .sidebar-footer { display: none; }
  .sidebar-logo { padding: 0 16px 32px; justify-content: center; }
  .logo-mark { margin: 0; }
  .nav-item { padding: 14px; justify-content: center; }
  .nav-icon { width: auto; font-size: 20px; }
  .main-content { margin-left: 64px; }
}
</style>
