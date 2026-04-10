import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/visao-geral' },

  // ── Combustível ───────────────────────────────────────────────────────────
  { path: '/visao-geral',  name: 'visao-geral',  component: () => import('./views/VisaoGeral.vue') },
  { path: '/operacional',  name: 'operacional',  component: () => import('./views/DashboardOperacional.vue') },
  { path: '/diretoria',    name: 'diretoria',    component: () => import('./views/DashboardDiretoria.vue') },

  // ── Manutenção ────────────────────────────────────────────────────────────
  { path: '/manutencao',              name: 'manutencao',              component: () => import('./views/ManutencaoGeral.vue') },
  { path: '/manutencao/operacional',  name: 'manutencao-operacional',  component: () => import('./views/ManutencaoOperacional.vue') },
  { path: '/manutencao/diretoria',    name: 'manutencao-diretoria',    component: () => import('./views/ManutencaoDiretoria.vue') },

  // ── FKM ───────────────────────────────────────────────────────────────────
  { path: '/fkm', name: 'fkm', component: () => import('./views/DashboardFKM.vue') },

  // ── Pneus ──────────────────────────────────────────────────────────────────
  { path: '/pneus', name: 'pneus', component: () => import('./views/Pneus.vue') },

  // ── Referência ────────────────────────────────────────────────────────────
  { path: '/sumario', name: 'sumario', component: () => import('./views/SistemaLegenda.vue') },

  // ── Gestão de Transações ──────────────────────────────────────────────────
  { path: '/transacoes', name: 'transacoes', component: () => import('./views/GestaoTransacoes.vue') },

  // ── Pedágios ──────────────────────────────────────────────────────────────
  { path: '/pedagios', name: 'pedagios', component: () => import('./views/PedagiosGeral.vue') },

  // ── Estornos (Auditoria) ──────────────────────────────────────────────────
  { path: '/estornos', name: 'estornos', component: () => import('./views/EstornosAuditoria.vue') },

  // ── TCO (Custo Total) ─────────────────────────────────────────────────────
  { path: '/tco', name: 'tco', component: () => import('./views/TcoGeral.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
