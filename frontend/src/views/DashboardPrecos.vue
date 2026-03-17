<template>
  <div class="page">

    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="section-name">Inteligência de Preços</span>
      </div>
      <div class="topbar-right">
        <div class="filter-inline">
          <label>Combustível</label>
          <select v-model="filtroCombustivel" @change="loadAll">
            <option value="">Todos</option>
            <option v-for="c in combustiveis" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
      </div>
    </header>

    <div class="page-header">
      <div>
        <h1>Inteligência de Preços</h1>
        <p class="page-sub">Evolução, benchmarks por UF e ranking de postos · histórico completo</p>
      </div>
    </div>

    <div class="page-body">

      <!-- Evolução de preço por tipo -->
      <section>
        <div class="section-heading">Evolução mensal do preço / litro</div>
        <GraficoEvolucaoPrecos :data="evolucao" :loading="lEvolucao" />
      </section>

      <!-- Preço por UF -->
      <section>
        <div class="section-heading">Preço médio por estado (UF)</div>
        <div class="uf-tabs">
          <button
            :class="{ active: filtroUF === '' }"
            @click="filtroUF = ''; loadUF()"
          >Todos</button>
          <button
            v-for="c in combustiveis"
            :key="c"
            :class="{ active: filtroUF === c }"
            @click="filtroUF = c; loadUF()"
          >{{ c }}</button>
        </div>
        <GraficoPrecoPorUF :data="precoPorUF" :loading="lUF" />
      </section>

      <!-- Variação Mensal -->
      <section>
        <div class="section-heading">Variação de preço mensal</div>
        <GraficoVariacaoMensal :data="variacao" :loading="lVariacao" />
      </section>

      <!-- Ranking postos baratos / caros -->
      <section>
        <div class="section-heading">Ranking de postos por preço médio</div>
        <div class="ranking-tabs">
          <button :class="{ active: ordemRanking === 'mais_barato' }" @click="ordemRanking = 'mais_barato'; loadRanking()">Mais baratos</button>
          <button :class="{ active: ordemRanking === 'mais_caro' }" @click="ordemRanking = 'mais_caro'; loadRanking()">Mais caros</button>
        </div>
        <div class="ranking-card">
          <TabelaRankingPostos :data="rankingPostos" :loading="lRanking" :ordem="ordemRanking" />
        </div>
      </section>

      <!-- Análise premium -->
      <section>
        <div class="section-heading">Análise de combustíveis premium</div>
        <SecaoPremium :data="premium" :loading="lPremium" />
      </section>

    </div>

    <footer class="footer">
      <span>© {{ new Date().getFullYear() }} Gritsch · Torre de Controle</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchEvolucaoPorTipo, fetchPrecoPorUF, fetchRankingPostosPreco, fetchAnalisePremium, fetchVariacaoMensal } from '../api/precos.js'
import { fetchFiltros } from '../api/combustivel.js'
import GraficoEvolucaoPrecos from '../components/GraficoEvolucaoPrecos.vue'
import GraficoPrecoPorUF    from '../components/GraficoPrecoPorUF.vue'
import GraficoVariacaoMensal from '../components/GraficoVariacaoMensal.vue'
import TabelaRankingPostos  from '../components/TabelaRankingPostos.vue'
import SecaoPremium         from '../components/SecaoPremium.vue'

const filtroCombustivel = ref('')
const filtroUF = ref('')
const combustiveis = ref([])
const ordemRanking = ref('mais_barato')

const evolucao    = ref({})
const precoPorUF  = ref([])
const rankingPostos = ref([])
const premium     = ref({})
const variacao    = ref([])

const lEvolucao  = ref(true)
const lUF        = ref(true)
const lRanking   = ref(true)
const lPremium   = ref(true)
const lVariacao  = ref(true)

function getF() {
  return { combustivel: filtroCombustivel.value || undefined }
}

async function loadUF() {
  lUF.value = true
  const combustivel = filtroUF.value || filtroCombustivel.value || undefined
  precoPorUF.value = await fetchPrecoPorUF({ combustivel }).finally(() => lUF.value = false)
}

async function loadRanking() {
  lRanking.value = true
  rankingPostos.value = await fetchRankingPostosPreco({ ...getF(), ordem: ordemRanking.value })
  lRanking.value = false
}

async function loadAll() {
  const f = getF()
  lEvolucao.value = lUF.value = lRanking.value = lPremium.value = lVariacao.value = true

  filtroUF.value = ''
  await Promise.allSettled([
    fetchEvolucaoPorTipo(f).then(d => evolucao.value = d).finally(() => lEvolucao.value = false),
    fetchPrecoPorUF({ combustivel: f.combustivel }).then(d => precoPorUF.value = d).finally(() => lUF.value = false),
    fetchRankingPostosPreco({ ...f, ordem: ordemRanking.value }).then(d => rankingPostos.value = d).finally(() => lRanking.value = false),
    fetchAnalisePremium(f).then(d => premium.value = d).finally(() => lPremium.value = false),
    fetchVariacaoMensal(f).then(d => variacao.value = d).finally(() => lVariacao.value = false),
  ])
}

onMounted(async () => {
  const filtros = await fetchFiltros()
  combustiveis.value = filtros.combustiveis || []
  await loadAll()
})
</script>

<style scoped>
.page { min-height: 100vh; display: flex; flex-direction: column; }

.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 40px; height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky; top: 0; z-index: 10;
}
.topbar-left { display: flex; align-items: center; }
.section-name { font-size: 14px; font-weight: 500; color: var(--text-2); }
.topbar-right { display: flex; align-items: center; gap: 12px; }

.filter-inline { display: flex; align-items: center; gap: 8px; }
.filter-inline label { font-size: 11px; font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .03em; }
.filter-inline select {
  background: var(--surface); border: 1px solid var(--border); color: var(--text);
  font-size: 12px; padding: 5px 10px; border-radius: 7px; cursor: pointer;
  font-family: 'Inter', sans-serif; outline: none; min-width: 140px;
}

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 32px 40px 0;
}
h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.page-sub { font-size: 13px; color: var(--text-3); margin-top: 4px; }

.page-body { padding: 28px 40px 40px; display: flex; flex-direction: column; gap: 28px; flex: 1; }

.section-heading {
  font-size: 12px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .06em;
  margin-bottom: 12px;
  display: flex; align-items: center; gap: 12px;
}
.section-heading::after { content:''; flex:1; height:1px; background: var(--border-subtle); }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.ranking-card {
  background: white; border: 1px solid var(--border); border-radius: 12px; padding: 20px;
}
.ranking-tabs, .uf-tabs {
  display: flex; gap: 4px; margin-bottom: 12px; flex-wrap: wrap;
}
.ranking-tabs button, .uf-tabs button {
  background: transparent; border: 1px solid var(--border); color: var(--text-3);
  font-size: 12px; padding: 5px 14px; border-radius: 6px; cursor: pointer;
  font-family: 'Inter', sans-serif; transition: all .15s;
}
.ranking-tabs button.active, .uf-tabs button.active {
  background: var(--accent); border-color: var(--accent); color: white;
}

.footer {
  display: flex; justify-content: space-between;
  padding: 16px 40px; border-top: 1px solid var(--border-subtle);
  font-size: 12px; color: var(--text-3);
}

@media (max-width: 1000px) { .two-col { grid-template-columns: 1fr; } }
@media (max-width: 680px) {
  .topbar, .page-header, .page-body, .footer { padding-left: 16px; padding-right: 16px; }
}
</style>
