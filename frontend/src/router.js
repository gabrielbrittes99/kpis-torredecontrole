import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/visao-geral'
  },
  {
    path: '/visao-geral',
    name: 'visao-geral',
    component: () => import('./views/VisaoGeral.vue')
  },
  {
    path: '/operacional',
    name: 'operacional',
    component: () => import('./views/DashboardOperacional.vue')
  },
  {
    path: '/diretoria',
    name: 'diretoria',
    component: () => import('./views/DashboardDiretoria.vue')
  },

]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
