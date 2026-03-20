<template>
  <div class="shell" :class="{ collapsed }">
    <nav class="sidebar" :class="{ collapsed }">

      <!-- Logo -->
      <div class="sidebar-header" :class="{ 'header-collapsed': collapsed }">
        <img
          src="./assets/transportes-gritsch (2).png"
          alt="Transportes Gritsch"
          class="logo-img"
          :class="{ 'logo-sm': collapsed }"
          @click="collapsed = !collapsed"
          :title="collapsed ? 'Expandir menu' : ''"
          :style="collapsed ? 'cursor:pointer' : ''"
        />
        <button v-show="!collapsed" class="collapse-btn" @click="collapsed = true" title="Recolher">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M10 3L5 8l5 5"/>
          </svg>
        </button>
      </div>

      <!-- COMBUSTÍVEL -->
      <div class="nav-group">
        <span v-show="!collapsed" class="group-label">Combustível</span>
        <div v-show="collapsed" class="group-rule" />

        <button class="nav-btn" :class="{ active: is('visao-geral') }" @click="go('visao-geral')" :title="collapsed ? 'Visão Geral' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="10" width="4" height="7" rx="1"/>
              <rect x="7" y="5"  width="4" height="12" rx="1"/>
              <rect x="13" y="1" width="4" height="16" rx="1"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Visão Geral</span>
        </button>

        <button class="nav-btn" :class="{ active: is('operacional') }" @click="go('operacional')" :title="collapsed ? 'Visão Operacional' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="6" width="10" height="6" rx="1.5"/>
              <path d="M11 9h2l2 2h1.5a.5.5 0 00.5-.5v-3a.5.5 0 00-.5-.5H13"/>
              <circle cx="4"  cy="14" r="1.5"/>
              <circle cx="13" cy="14" r="1.5"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Visão Operacional</span>
        </button>

        <button class="nav-btn" :class="{ active: is('diretoria') }" @click="go('diretoria')" :title="collapsed ? 'Visão da Diretoria' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="1,13 5,8 8,10 13,4 17,7"/>
              <polyline points="13,4 17,4 17,7"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Visão da Diretoria</span>
        </button>
      </div>

      <!-- MANUTENÇÃO -->
      <div class="nav-group">
        <span v-show="!collapsed" class="group-label">Manutenção</span>
        <div v-show="collapsed" class="group-rule" />

        <button class="nav-btn" :class="{ active: is('manutencao') }" @click="go('manutencao')" :title="collapsed ? 'Visão Geral — Manutenção' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M13.5 2a3.5 3.5 0 00-3.36 4.46L2.5 14.1a1.4 1.4 0 001.98 1.98l7.64-7.64A3.5 3.5 0 0013.5 2z"/>
              <circle cx="13.5" cy="5.5" r="1" fill="currentColor" stroke="none"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Visão Geral</span>
        </button>

        <button class="nav-btn" :class="{ active: is('manutencao-operacional') }" @click="go('manutencao-operacional')" :title="collapsed ? 'Operacional — Manutenção' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="9" cy="9" r="3"/>
              <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.22 3.22l1.42 1.42M13.36 13.36l1.42 1.42M3.22 14.78l1.42-1.42M13.36 4.64l1.42-1.42"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Visão Operacional</span>
        </button>

        <button class="nav-btn" :class="{ active: is('manutencao-diretoria') }" @click="go('manutencao-diretoria')" :title="collapsed ? 'Diretoria — Manutenção' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="2" width="12" height="14" rx="1.5"/>
              <line x1="6" y1="6"  x2="12" y2="6"/>
              <line x1="6" y1="9"  x2="12" y2="9"/>
              <line x1="6" y1="12" x2="9"  y2="12"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Visão da Diretoria</span>
        </button>
      </div>

      <!-- FKM -->
      <div class="nav-group">
        <span v-show="!collapsed" class="group-label">FKM</span>
        <div v-show="collapsed" class="group-rule" />

        <button class="nav-btn" :class="{ active: is('fkm') }" @click="go('fkm')" :title="collapsed ? 'FKM · Fechamento Mensal' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="1" width="16" height="16" rx="2"/>
              <line x1="1" y1="7"  x2="17" y2="7"/>
              <line x1="1" y1="12" x2="17" y2="12"/>
              <line x1="7" y1="7"  x2="7"  y2="17"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Fechamento Mensal</span>
        </button>
      </div>

      <div class="sidebar-spacer" />

      <!-- REFERÊNCIA -->
      <div class="nav-group nav-group--bottom">
        <button class="nav-btn" :class="{ active: is('sumario') }" @click="go('sumario')" :title="collapsed ? 'Sumário do Sistema' : ''">
          <span class="nav-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="9" cy="9" r="7"/>
              <line x1="9" y1="8" x2="9" y2="13"/>
              <circle cx="9" cy="5.5" r=".75" fill="currentColor" stroke="none"/>
            </svg>
          </span>
          <span v-show="!collapsed" class="nav-text">Sumário do Sistema</span>
        </button>

        <div v-show="!collapsed" class="sidebar-version">
          v2.1 · TruckPag + BlueFleet
        </div>
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
const route  = useRoute()
const collapsed = ref(false)

const is = (name) => {
  if (route.path === '/' && name === 'visao-geral') return true
  return route.path.substring(1).replace('/', '-') === name
}

const go = (name) => router.push({ name })
</script>

<style>
/* ── Reset ──────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--void); color: var(--text); font-family: 'Inter', sans-serif; }

/* ── Shell ──────────────────────────────────────────────────────────────── */
.shell { display: flex; min-height: 100vh; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  padding: 0;
  position: fixed;
  top: 0; left: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 100;
  transition: width 0.2s ease;
}
.sidebar.collapsed { width: 88px; }

/* ── Header ─────────────────────────────────────────────────────────────── */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 10px 14px 14px;
  border-bottom: 1px solid #f1f5f9;
  min-height: 60px;
  flex-shrink: 0;
}
.header-collapsed {
  justify-content: center;
  padding: 14px 10px;
}

/* Logo */
.logo-img {
  height: 28px;
  width: auto;
  display: block;
  flex-shrink: 0;
}
/* Colapsado: logo menor, cabe nos 88px */
.logo-sm {
  height: 22px;
}

.collapse-btn {
  width: 26px; height: 26px;
  border: none; background: none; cursor: pointer;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  color: #cbd5e1;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
  margin-left: 4px;
}
.collapse-btn:hover { background: #f1f5f9; color: #64748b; }
.collapse-btn svg { width: 14px; height: 14px; }

/* ── Nav Groups ─────────────────────────────────────────────────────────── */
.nav-group { padding: 12px 8px 4px; }
.nav-group--bottom { padding-top: 8px; border-top: 1px solid #f1f5f9; }
.collapsed .nav-group { padding: 8px 6px 4px; }

.group-label {
  display: block;
  font-size: 10px; font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.08em;
  padding: 0 8px 6px;
  white-space: nowrap;
}
.group-rule {
  height: 1px;
  background: #f1f5f9;
  margin: 0 4px 8px;
}

/* ── Nav Buttons ────────────────────────────────────────────────────────── */
.nav-btn {
  display: flex; align-items: center; gap: 8px;
  width: 100%;
  padding: 7px 8px;
  border-radius: 8px;
  background: none; border: none;
  color: #64748b;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  text-align: left;
  font-size: 13px; font-weight: 500;
  white-space: nowrap;
  margin-bottom: 1px;
}
.nav-btn:hover { background: #f8fafc; color: #1e293b; }
.nav-btn.active { background: #FDF2F4; color: #C41230; font-weight: 600; }

/* Collapsed: center the icon */
.collapsed .nav-btn {
  justify-content: center;
  padding: 8px 0;
  border-radius: 8px;
}
.collapsed .nav-btn:hover { background: #f8fafc; }
.collapsed .nav-btn.active { background: #C41230; color: #fff; }
.collapsed .nav-btn.active .nav-icon { color: #fff; }

/* ── Nav Icon ───────────────────────────────────────────────────────────── */
.nav-icon {
  width: 18px; height: 18px;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: inherit;
}
.nav-icon svg { width: 15px; height: 15px; }
.nav-btn.active .nav-icon { color: #C41230; }
.collapsed .nav-btn.active .nav-icon { color: #fff; }

.nav-text { font-size: 13px; font-weight: inherit; color: inherit; }

/* ── Spacer + Version ───────────────────────────────────────────────────── */
.sidebar-spacer { flex: 1; min-height: 8px; }
.sidebar-version {
  font-size: 10px; color: #cbd5e1;
  padding: 10px 8px 4px;
  white-space: nowrap;
}

/* ── Main ───────────────────────────────────────────────────────────────── */
.main-content {
  margin-left: 220px;
  flex: 1; min-width: 0;
  background: var(--void);
  min-height: 100vh;
  transition: margin-left 0.2s ease;
}
.collapsed .main-content { margin-left: 88px; }

@media (max-width: 768px) {
  .sidebar { width: 88px; }
  .sidebar.collapsed { width: 88px; }
  .main-content, .collapsed .main-content { margin-left: 88px; }
}
</style>
