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
          <span class="toggle-icon"></span>
        </button>
      </div>

      <div v-show="!collapsed" class="nav-section-label font-syne">Torre de Controle</div>

      <button
        class="nav-item"
        :class="{ active: activeSection === 'visao-geral' }"
        @click="goTo('visao-geral')"
        :title="collapsed ? 'Visão Geral' : ''"
      >
        <span class="nav-icon-bullet"></span>
        <span v-show="!collapsed" class="nav-label font-syne">Visão Geral</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: activeSection === 'operacional' }"
        @click="goTo('operacional')"
        :title="collapsed ? 'Operacional' : ''"
      >
        <span class="nav-icon-bullet"></span>
        <span v-show="!collapsed" class="nav-label font-syne">Visão Operacional</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: activeSection === 'diretoria' }"
        @click="goTo('diretoria')"
        :title="collapsed ? 'Diretoria' : ''"
      >
        <span class="nav-icon-bullet"></span>
        <span v-show="!collapsed" class="nav-label font-syne">Visão da Diretoria</span>
      </button>

      <div class="sidebar-footer">
        <span v-show="!collapsed" class="sidebar-version mono">v2.0 · TruckPag</span>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// Estado da navegação
const collapsed = ref(false)

const activeSection = computed(() => {
  if (route.path === '/') return 'vigilancia'
  return route.path.substring(1)
})

const goTo = (id) => {
  router.push({ name: id })
}
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
  width: 12px;
  height: 2px;
  background: var(--text2);
  position: relative;
}
.toggle-icon::before, .toggle-icon::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 2px;
  background: inherit;
  left: 0;
}
.toggle-icon::before { top: -4px; }
.toggle-icon::after { bottom: -4px; }

.nav-icon-bullet {
  width: 6px;
  height: 6px;
  background: var(--text3);
  border-radius: 50%;
  flex-shrink: 0;
}
.active .nav-icon-bullet {
  background: var(--orange);
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
