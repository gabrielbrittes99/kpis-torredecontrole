import { defineStore } from 'pinia'

// Se a API "fetchFiltrosDisponiveis" estivesse num único local, usaríamos aqui.
// Por padrão do Vue3 e Vite, usaremos a que está no visaoGeral provisoriamente
import { fetchFiltrosDisponiveis } from '../api/visaoGeral.js'

export const useFiltrosStore = defineStore('filtros', {
  state: () => ({
    // Seleção atual
    selecao: {
      modoTempo: 'mes', // 'mes', 'bimestre', 'semestre', 'ano', 'personalizado'
      mes: new Date().getMonth() + 1,
      ano: new Date().getFullYear(),
      bimestre: Math.ceil((new Date().getMonth() + 1) / 2),
      semestre: (new Date().getMonth() + 1) <= 6 ? 1 : 2,
      data_inicio: null,
      data_fim: null,
      
      estado: null,
      regiao: null,
      filial: null,
      grupo: null,
      combustivel: null
    },
    
    // Opções disponíveis que vêm da API
    opcoes: {
      estados: [],
      regioes: [],
      filiais: [],
      grupos_veiculo: [],
      combustiveis: [],
      meses: [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
      ],
      bimestres: [
        '1º Bimestre (Jan-Fev)', '2º Bimestre (Mar-Abr)', '3º Bimestre (Mai-Jun)',
        '4º Bimestre (Jul-Ago)', '5º Bimestre (Set-Out)', '6º Bimestre (Nov-Dez)'
      ],
      semestres: [
        '1º Semestre (Jan-Jun)', '2º Semestre (Jul-Dez)'
      ],
      anos: [] // Será preenchido dinamicamente
    },
    
    carregandoOpcoes: false
  }),
  
  getters: {
    filtrosIniciados: (state) => state.opcoes.filiais.length > 0,
    
    // Helper para gerar params de API baseado no modo de tempo
    paramsTempo: (state) => {
      const s = state.selecao
      const p = { modo_tempo: s.modoTempo, ano: s.ano }
      
      if (s.modoTempo === 'mes') p.mes = s.mes
      else if (s.modoTempo === 'bimestre') p.bimestre = s.bimestre
      else if (s.modoTempo === 'semestre') p.semestre = s.semestre
      else if (s.modoTempo === 'personalizado') {
        p.data_inicio = s.data_inicio
        p.data_fim = s.data_fim
      }
      // 'ano' usa apenas p.ano que já está setado
      return p
    }
  },
  
  actions: {
    async loadOpcoesFiltros() {
      // Inicializa anos se vazio
      if (this.opcoes.anos.length === 0) {
        const curYear = new Date().getFullYear()
        this.opcoes.anos = [curYear, curYear - 1, curYear - 2]
      }

      if (this.filtrosIniciados || this.carregandoOpcoes) return;
      
      this.carregandoOpcoes = true
      try {
        const f = await fetchFiltrosDisponiveis()
        this.opcoes.estados = f.estados || []
        this.opcoes.regioes = f.regioes || []
        this.opcoes.filiais = f.filiais || []
        this.opcoes.grupos_veiculo = f.grupos_veiculo || []
        this.opcoes.combustiveis = f.combustiveis || []
      } catch (e) {
        console.error('[Pinia] Erro carregando opções de filtros', e)
      } finally {
        this.carregandoOpcoes = false
      }
    },
    
    limparFiltrosGlobais() {
      this.selecao.estado = null
      this.selecao.regiao = null
      this.selecao.filial = null
      this.selecao.grupo = null
      this.selecao.combustivel = null
    }
  }
})
