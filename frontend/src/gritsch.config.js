export const GRITSCH_CONFIG = {
  URLS: {
    BACKEND: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  },
  TTLS: {
    TRANSACOES: 1 * 60 * 1000,    // Reduzido para 1 min para maior frescor em teste
    PRECOS:      4 * 60 * 60 * 1000, 
    ANP:        24 * 60 * 60 * 1000, 
    PROJECAO:    5 * 60 * 1000,      // 5 min
    MERCADO:     1 * 60 * 60 * 1000, 
  },
  THRESHOLDS: {
    POSTO_CARO_PCT: 5,        
    CONSUMO_ANORMAL_PCT: 15,  // Reduzido threshold para disparar mais alertas em teste
    ORCAMENTO_ESTOURO_PCT: 1, // Reduzido para garantir que o semáforo mude em teste
  },
  ESTADOS_OPERACAO: ['PR', 'SC']
}
