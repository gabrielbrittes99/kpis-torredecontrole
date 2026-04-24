import { cachedFetch, TTL } from "./apiCache";

export function fetchHeroOperacional(params = {}) {
    return cachedFetch("/api/operacional/hero", params, { ttl: TTL.DASHBOARD });
}
export function fetchTopConsumidores(params = {}) {
    return cachedFetch("/api/operacional/top-consumidores", params, {
        ttl: TTL.DASHBOARD,
    });
}
export function fetchEvolucaoMensal(params = {}) {
    return cachedFetch("/api/operacional/evolucao-mensal", params, {
        ttl: TTL.EVOLUCAO,
    });
}
export function fetchVeiculosAcao(params = {}) {
    return cachedFetch("/api/operacional/veiculos-acao", params, {
        ttl: TTL.DASHBOARD,
    });
}
