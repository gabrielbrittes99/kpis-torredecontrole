/**
 * ═══════════════════════════════════════════════════════════════════════════
 * apiCache.js — Cache Centralizado de API
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Cache em memória com TTL para todas as chamadas de API.
 * Features:
 *   - TTL configurável por tipo de dado
 *   - Deduplicação de requests in-flight (mesma URL = 1 fetch)
 *   - Prefetch silencioso (background)
 *   - Invalidação seletiva
 */

import { GRITSCH_CONFIG } from '../gritsch.config'

const BASE = GRITSCH_CONFIG.URLS.BACKEND

// ── TTLs (milissegundos) ─────────────────────────────────────────────────────
const TTL = {
  DASHBOARD:    30 * 60 * 1000,  // 30 min — dados analíticos
  FILTROS:     120 * 60 * 1000,  // 2 horas — quase nunca mudam
  EVOLUCAO:     30 * 60 * 1000,  // 30 min — históricos
  TRANSACOES:    5 * 60 * 1000,  // 5 min — dados mais frescos
  DEFAULT:      30 * 60 * 1000,  // 30 min
}

// ── Armazém do cache ─────────────────────────────────────────────────────────
const _store = new Map()       // chave → { data, ts, ttl }
const _inflight = new Map()    // chave → Promise (dedup)

/**
 * Gera uma chave de cache a partir da URL e params.
 */
function _cacheKey(path, params = {}) {
  const sorted = Object.entries(params)
    .filter(([, v]) => v !== null && v !== undefined && v !== '')
    .sort(([a], [b]) => a.localeCompare(b))
  return `${path}|${JSON.stringify(sorted)}`
}

/**
 * Verifica se um entry do cache ainda é válido.
 */
function _isValid(entry) {
  if (!entry) return false
  return (Date.now() - entry.ts) < entry.ttl
}

/**
 * Busca com cache.
 * @param {string} path  - Caminho da API (ex: '/api/visao-geral/dashboard')
 * @param {object} params - Query params
 * @param {object} options - { ttl, force }
 * @returns {Promise<any>}
 */
export async function cachedFetch(path, params = {}, options = {}) {
  const ttl = options.ttl ?? TTL.DEFAULT
  const force = options.force ?? false
  const key = _cacheKey(path, params)

  // Cache hit (e não forçado)
  if (!force) {
    const cached = _store.get(key)
    if (_isValid(cached)) {
      return cached.data
    }
  }

  // Dedup: se já tem um fetch in-flight para a mesma chave, espera ele
  if (_inflight.has(key)) {
    return _inflight.get(key)
  }

  // Monta a URL
  const url = new URL(`${BASE}${path}`, location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v)
  })

  // Cria a promise e registra como in-flight
  const promise = fetch(url)
    .then(res => {
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      return res.json()
    })
    .then(data => {
      // Salva no cache
      _store.set(key, { data, ts: Date.now(), ttl })
      _inflight.delete(key)
      return data
    })
    .catch(err => {
      _inflight.delete(key)
      // Se tem cache antigo (expirado), retorna ele ao invés de quebrar
      const stale = _store.get(key)
      if (stale) {
        console.warn(`[Cache] Erro no fetch, usando cache stale para ${path}`, err)
        return stale.data
      }
      throw err
    })

  _inflight.set(key, promise)
  return promise
}

/**
 * Prefetch silencioso — não bloqueia, não lança erro.
 */
export function prefetch(path, params = {}, options = {}) {
  const key = _cacheKey(path, params)
  const cached = _store.get(key)
  if (_isValid(cached)) return // Já tem no cache, não precisa
  cachedFetch(path, params, options).catch(() => {})
}

/**
 * Invalida o cache de um path específico (todas as variações de params).
 */
export function invalidate(pathPattern) {
  for (const key of _store.keys()) {
    if (key.startsWith(pathPattern)) {
      _store.delete(key)
    }
  }
}

/**
 * Invalida TODO o cache.
 */
export function invalidateAll() {
  _store.clear()
  console.info('[Cache] Todo o cache foi invalidado')
}

/**
 * Retorna estatísticas do cache.
 */
export function cacheStats() {
  let valid = 0, stale = 0
  for (const entry of _store.values()) {
    if (_isValid(entry)) valid++
    else stale++
  }
  return { total: _store.size, valid, stale, inflight: _inflight.size }
}

// Expõe TTLs para uso nos módulos de API
export { TTL }
