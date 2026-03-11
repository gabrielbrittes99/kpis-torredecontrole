<template>
  <div class="shell">
    <!-- Sidebar -->
    <nav class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">G</div>
        <span class="logo-text">Gritsch</span>
      </div>

      <div class="nav-section-label">Torre de Controle</div>

      <button
        v-for="item in navItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeSection === item.id }"
        @click="activeSection = item.id"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </button>

      <div class="sidebar-footer">
        <span class="sidebar-version">v2.0 · TruckPag</span>
      </div>
    </nav>

    <!-- Main content -->
    <main class="main-content">
      <DashboardCombustivel v-if="activeSection === 'combustivel'" />
      <DashboardPrecos      v-else-if="activeSection === 'precos'" />
      <DashboardFrota       v-else-if="activeSection === 'frota'" />
      <DashboardOperacional  v-else-if="activeSection === 'operacional'" />
      <DashboardDiretoria    v-else-if="activeSection === 'diretoria'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DashboardCombustivel  from './views/DashboardCombustivel.vue'
import DashboardOperacional  from './views/DashboardOperacional.vue'
import DashboardPrecos      from './views/DashboardPrecos.vue'
import DashboardFrota       from './views/DashboardFrota.vue'
import DashboardDiretoria   from './views/DashboardDiretoria.vue'

const activeSection = ref('combustivel')

const navItems = [
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
body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; }

.shell {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 20;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.logo-mark {
  width: 28px;
  height: 28px;
  background: var(--accent);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  color: white;
  flex-shrink: 0;
}

.logo-text {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 12px 20px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 20px;
  background: transparent;
  border: none;
  color: var(--text-2);
  font-size: 13px;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  text-align: left;
  width: 100%;
  border-radius: 0;
  transition: background 0.1s, color 0.1s;
  position: relative;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.nav-item.active {
  color: var(--text);
  background: var(--surface-hover);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}

.nav-icon { font-size: 14px; width: 18px; text-align: center; }
.nav-label { font-weight: 450; }

.sidebar-footer {
  margin-top: auto;
  padding: 16px 20px 0;
  border-top: 1px solid var(--border);
}

.sidebar-version {
  font-size: 11px;
  color: var(--text-3);
  font-family: 'JetBrains Mono', monospace;
}

/* Main content */
.main-content {
  margin-left: 220px;
  flex: 1;
  min-width: 0;
}

@media (max-width: 768px) {
  .sidebar { width: 56px; }
  .logo-text, .nav-label, .nav-section-label, .sidebar-footer { display: none; }
  .sidebar-logo { padding: 0 14px 16px; justify-content: center; }
  .logo-mark { margin: 0; }
  .nav-item { padding: 10px; justify-content: center; }
  .nav-icon { width: auto; }
  .main-content { margin-left: 56px; }
}
</style>
