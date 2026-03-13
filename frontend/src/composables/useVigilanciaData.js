import { ref } from 'vue'
import { GRITSCH_CONFIG } from '../gritsch.config'

export function useVigilanciaData() {
  const estado = ref({})
  const carregando = ref(false)
  const ultimaAtualizacao = ref('')

  async function fetchTudo() {
    carregando.value = true
    try {
      const resp = await fetch(`${GRITSCH_CONFIG.URLS.BACKEND}/api/torre/dashboard`)
      if (resp.ok) {
        const json = await resp.json()
        estado.value = json.data
        ultimaAtualizacao.value = new Date(json.ultima_atualizacao).toLocaleTimeString('pt-BR')
      }
    } catch (e) {
      console.error("[Vigilancia] Erro fetch:", e)
    } finally {
      carregando.value = false
    }
  }

  return { estado, carregando, ultimaAtualizacao, fetchTudo }
}
