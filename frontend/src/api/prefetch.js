/**
 * ═══════════════════════════════════════════════════════════════════════════
 * prefetch.js — Pré-carregamento Global de Dados
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dispara chamadas para TODAS as telas principais ao iniciar o app.
 * Quando o usuário clicar em qualquer aba, o dado já estará no cache.
 *
 * O prefetch é silencioso — falhas são ignoradas (os componentes
 * vão buscar novamente quando forem montados).
 */

import { prefetch } from './apiCache'

/**
 * Parâmetros padrão baseados na data atual.
 */
function defaultParams() {
  const now = new Date()
  return {
    mes: now.getMonth() + 1,
    ano: now.getFullYear(),
    modo_tempo: 'mes',
  }
}

/**
 * Pré-carrega dados de TODOS os módulos principais.
 * Chamado uma vez no App.vue onMounted.
 */
export function prefetchAllModules() {
  const p = defaultParams()

  console.info('[Prefetch] Iniciando pré-carregamento de dados para todas as telas...')

  // ── Filtros (raramente mudam, cache de 2h) ──────────────────────────────
  prefetch('/api/visao-geral/filtros-disponiveis')

  // ── Visão Geral ─────────────────────────────────────────────────────────
  prefetch('/api/visao-geral/dashboard', p)

  // ── Operacional ─────────────────────────────────────────────────────────
  prefetch('/api/operacional/evolucao-mensal', { ...p, familia: 'todos' })
  prefetch('/api/operacional/veiculos-acao', { ...p, familia: 'todos' })

  // ── Diretoria ───────────────────────────────────────────────────────────
  prefetch('/api/diretoria/kpis-estrategicos', p)
  prefetch('/api/diretoria/tendencia-12-meses', p)
  prefetch('/api/diretoria/comparativo-meses', p)
  prefetch('/api/diretoria/mix-combustiveis', p)
  prefetch('/api/diretoria/gastos-filiais', p)

  // ── Manutenção ──────────────────────────────────────────────────────────
  prefetch('/api/manutencao/filtros')
  prefetch('/api/manutencao/kpis', p)

  // ── FKM ─────────────────────────────────────────────────────────────────
  prefetch('/api/fkm/filtros')
  prefetch('/api/fkm/kpis', p)

  // ── Pedágios ────────────────────────────────────────────────────────────
  prefetch('/api/pedagios/visao-geral', p)

  // ── Preços ──────────────────────────────────────────────────────────────
  prefetch('/api/precos/preco-por-uf', p)

  // ── Benchmark ───────────────────────────────────────────────────────────
  prefetch('/api/benchmark/comparativo-frota', p)

  console.info('[Prefetch] Todas as chamadas de prefetch foram disparadas.')
}
