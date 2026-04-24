<template>
    <div class="page animate-in">
        <GlobalTopbar
            title="Visão Operacional"
            subtitle="Inteligência de compras, geografia e volume de abastecimento"
        />

        <div class="page-body">
            <!-- ━━━━━ SELETOR DE FAMÍLIA ━━━━━ -->
            <div class="fuel-selector-bar">
                <button
                    v-for="f in FAMILIAS_LIST"
                    :key="f.key"
                    class="fuel-tab"
                    :class="{ active: familiaFiltro === f.key }"
                    @click="
                        familiaFiltro = f.key;
                        loadAll();
                    "
                >
                    {{ f.label }}
                </button>
            </div>

            <!-- ━━━━━ HERO OPERACIONAL ━━━━━ -->
            <div class="kpi-pro-grid">
                <KpiCardPro
                    title="Gasto Total"
                    :value="hero.gasto_total || 0"
                    format="currency"
                    theme="primary"
                    :period="mesMesLabel"
                    :loading="lHero"
                />
                <KpiCardPro
                    title="Volume Abastecido"
                    :value="hero.volume_total || 0"
                    format="number"
                    unit="L"
                    :period="mesMesLabel"
                    :loading="lHero"
                />
                <KpiCardPro
                    title="Preço Médio Pago"
                    :value="hero.preco_medio || 0"
                    format="currency"
                    :decimals="3"
                    unit="/ L"
                    :period="mesMesLabel"
                    :loading="lHero"
                />
                <KpiCardPro
                    title="Custo por KM"
                    :value="hero.custo_km || 0"
                    format="currency"
                    :decimals="2"
                    unit="/ km"
                    :period="mesMesLabel"
                    :loading="lHero"
                />
                <KpiCardPro
                    title="Postos Ativos"
                    :value="hero.postos_ativos || 0"
                    format="number"
                    :period="mesMesLabel"
                    description="Rede de abastecimento utilizada"
                    :loading="lHero"
                />
            </div>

            <!-- ━━━━━ GEOGRAFIA E PREÇO ━━━━━ -->
            <div class="two-col align-stretch">
                <!-- Mapa de Preços -->
                <section class="v-block flex-col">
                    <div class="section-title-row">
                        <div class="section-heading" style="flex: 1; margin: 0">
                            Preço Médio por Estado (UF)
                        </div>
                    </div>
                    <MapaPrecoUF
                        :data="precoPorUF"
                        :loading="lPrecoUF"
                        :color="corFamilia"
                        class="flex-1"
                    />
                </section>

                <!-- Evolução Mensal Inteligente -->
                <section class="v-block flex-col">
                    <div class="section-title-row">
                        <div class="section-heading" style="flex: 1; margin: 0">
                            Custo/km vs Preço do Combustível
                        </div>
                    </div>
                    <div class="chart-container flex-1">
                        <div v-if="lEvolucao" class="skel fill-skel" />
                        <div v-else-if="!evolucao.length" class="empty">
                            Sem dados
                        </div>
                        <apexchart
                            v-else
                            type="line"
                            height="100%"
                            width="100%"
                            :options="evolucaoOpts"
                            :series="evolucaoSeries"
                        />
                    </div>
                </section>
            </div>

            <!-- ━━━━━ ANÁLISE DE POSTOS ━━━━━ -->
            <section class="v-block">
                <div class="section-title-row">
                    <div class="section-heading" style="flex: 1; margin: 0">
                        Inteligência de Postos · Top 10
                    </div>
                </div>
                <div class="postos-grid">
                    <div class="posto-panel">
                        <div class="posto-panel-title">
                            <div
                                style="
                                    display: flex;
                                    align-items: center;
                                    gap: 10px;
                                "
                            >
                                <span class="posto-icon posto-icon-blue"
                                    >L</span
                                >
                                Top Parceiros (Maior Volume)
                            </div>
                        </div>
                        <div class="table-wrap">
                            <TabelaRankingPostos
                                :data="postosMaiorVolume"
                                :loading="lPostosVolume"
                                ordem="maior_volume"
                            />
                        </div>
                    </div>

                    <div class="posto-panel">
                        <div class="posto-panel-title">
                            <div
                                style="
                                    display: flex;
                                    align-items: center;
                                    gap: 10px;
                                "
                            >
                                <span class="posto-icon posto-icon-orange"
                                    >▲</span
                                >
                                Alertas de Preço (Mais Caros)
                            </div>
                        </div>
                        <div class="table-wrap">
                            <TabelaRankingPostos
                                :data="postosMaisCaros"
                                :loading="lPostosCaros"
                                ordem="mais_caro"
                            />
                        </div>
                    </div>
                </div>
            </section>

            <!-- ━━━━━ TOP CONSUMIDORES (VEÍCULOS) ━━━━━ -->
            <section class="v-block">
                <div class="section-title-row">
                    <div class="section-heading" style="flex: 1; margin: 0">
                        Veículos de Maior Volumetria
                    </div>
                </div>
                <div class="table-wrap">
                    <table class="veiculos-table">
                        <thead>
                            <tr>
                                <th>Veículo</th>
                                <th>Operação</th>
                                <th>Região / Cidade</th>
                                <th class="right">Volume (L)</th>
                                <th class="right">Preço Médio</th>
                                <th class="right">Desempenho</th>
                                <th class="right">Custo Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-if="lTop" v-for="i in 5" :key="'skel' + i">
                                <td colspan="7">
                                    <div
                                        class="skel"
                                        style="height: 40px; width: 100%"
                                    ></div>
                                </td>
                            </tr>
                            <tr v-else-if="!topConsumidores.length">
                                <td colspan="7" class="empty">
                                    Sem dados encontrados para o período
                                </td>
                            </tr>
                            <tr
                                v-else
                                v-for="v in topConsumidores"
                                :key="v.placa"
                                class="v-row"
                            >
                                <!-- Coluna 1: Veículo -->
                                <td>
                                    <div class="v-placa mono">
                                        {{ v.placa }}
                                    </div>
                                    <div class="v-modelo">
                                        {{ v.modelo || "Modelo não informado" }}
                                    </div>
                                </td>
                                <!-- Coluna 2: Operação -->
                                <td>
                                    <div class="v-motorista">
                                        {{
                                            v.motorista ||
                                            "Motorista não informado"
                                        }}
                                    </div>
                                    <div class="v-filial">
                                        Grupo: {{ v.grupo }} · {{ v.filial }}
                                    </div>
                                </td>
                                <!-- Coluna 3: Local -->
                                <td>
                                    <div class="v-cidade">
                                        {{
                                            v.cidade_principal ||
                                            "Não informada"
                                        }}
                                    </div>
                                </td>
                                <!-- Coluna 4: Volume -->
                                <td class="right">
                                    <div class="v-bold">
                                        {{
                                            (
                                                v.total_litros || 0
                                            ).toLocaleString("pt-BR")
                                        }}
                                        L
                                    </div>
                                </td>
                                <!-- Coluna 5: Preço Médio -->
                                <td class="right">
                                    <div class="text-muted mono">
                                        R$ {{ (v.preco_medio || 0).toFixed(3) }}
                                    </div>
                                </td>
                                <!-- Coluna 6: Desempenho -->
                                <td class="right">
                                    <div class="v-bold mono">
                                        {{
                                            v.custo_km
                                                ? "R$ " +
                                                  v.custo_km.toFixed(2) +
                                                  "/km"
                                                : "—"
                                        }}
                                    </div>
                                    <div class="v-kml mono">
                                        {{
                                            v.km_litro
                                                ? v.km_litro.toFixed(2) +
                                                  " km/L"
                                                : ""
                                        }}
                                    </div>
                                </td>
                                <!-- Coluna 7: Valor Total -->
                                <td class="right">
                                    <div class="v-bold text-danger mono">
                                        R$
                                        {{
                                            (v.total_valor || 0).toLocaleString(
                                                "pt-BR",
                                                {
                                                    minimumFractionDigits: 2,
                                                    maximumFractionDigits: 2,
                                                },
                                            )
                                        }}
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </div>

        <footer class="footer">
            <span
                >© {{ new Date().getFullYear() }} Gritsch · Torre de
                Controle</span
            >
        </footer>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useFiltrosStore } from "../stores/filtros";
import { useRoute } from "vue-router";
import VueApexCharts from "vue3-apexcharts";
import GlobalTopbar from "../components/GlobalTopbar.vue";
import KpiCardPro from "../components/KpiCardPro.vue";
import TabelaRankingPostos from "../components/TabelaRankingPostos.vue";
import MapaPrecoUF from "../components/MapaPrecoUF.vue";
import {
    fetchHeroOperacional,
    fetchTopConsumidores,
    fetchEvolucaoMensal,
} from "../api/operacional.js";
import { fetchRankingPostosPreco, fetchPrecoPorUF } from "../api/precos.js";

const apexchart = VueApexCharts;
const store = useFiltrosStore();
const route = useRoute();

const familiaFiltro = ref(route.query.familia || "todos");
const FAMILIAS_LIST = [
    { key: "todos", label: "Geral" },
    { key: "diesel", label: "Diesel" },
    { key: "gasolina", label: "Gasolina" },
    { key: "etanol", label: "Etanol" },
];

const FAM_TO_COMB = {
    diesel: "Diesel",
    gasolina: "Gasolina",
    etanol: "Álcool",
};
const COMB_COLORS = {
    todos: "#C41230",
    diesel: "#2563EB",
    gasolina: "#7C3AED",
    etanol: "#0891B2",
};

const corFamilia = computed(
    () => COMB_COLORS[familiaFiltro.value] || "#C41230",
);

const mesMesLabel = computed(() => {
    const s = store.selecao;
    if (s.modoTempo === "mes")
        return store.opcoes.meses[(s.mes ?? 1) - 1] + "/" + s.ano;
    if (s.modoTempo === "ano") return "Ano " + s.ano;
    return "Período";
});

// ── State ────────────────────────────────────────────────────────────────────
const hero = ref({});
const precoPorUF = ref([]);
const evolucao = ref([]);
const postosMaiorVolume = ref([]);
const postosMaisCaros = ref([]);
const topConsumidores = ref([]);

const lHero = ref(true);
const lPrecoUF = ref(true);
const lEvolucao = ref(true);
const lPostosVolume = ref(true);
const lPostosCaros = ref(true);
const lTop = ref(true);

// ── Charts ───────────────────────────────────────────────────────────────────
const evolMeses = computed(() =>
    evolucao.value.map((r) => {
        const [ano, mes] = r.ano_mes.split("-");
        const nomes = [
            "",
            "Jan",
            "Fev",
            "Mar",
            "Abr",
            "Mai",
            "Jun",
            "Jul",
            "Ago",
            "Set",
            "Out",
            "Nov",
            "Dez",
        ];
        return `${nomes[+mes]}/${ano.slice(2)}`;
    }),
);

const evolucaoOpts = computed(() => ({
    chart: {
        toolbar: { show: false },
        zoom: { enabled: false },
        background: "transparent",
        fontFamily: "Inter, sans-serif",
    },
    colors: [corFamilia.value, "#f59e0b"],
    stroke: { width: [3, 3], curve: "smooth", dashArray: [0, 4] },
    fill: {
        type: ["gradient", "solid"],
        gradient: { shadeIntensity: 1, opacityFrom: 0.25, opacityTo: 0.02 },
    },
    xaxis: {
        categories: evolMeses.value,
        labels: { style: { fontSize: "11px", colors: "#94a3b8" } },
        axisBorder: { show: false },
        axisTicks: { show: false },
    },
    yaxis: [
        {
            title: {
                text: "Custo/km (R$)",
                style: { color: corFamilia.value, fontWeight: 600 },
            },
            labels: {
                style: { colors: corFamilia.value },
                formatter: (v) => (v ? `R$ ${v.toFixed(2)}` : ""),
            },
        },
        {
            opposite: true,
            title: {
                text: "Preço/L (R$)",
                style: { color: "#b45309", fontWeight: 600 },
            },
            labels: {
                style: { colors: "#b45309" },
                formatter: (v) => (v ? `R$ ${v.toFixed(3)}` : ""),
            },
        },
    ],
    grid: { borderColor: "#f1f5f9", strokeDashArray: 4 },
    tooltip: { theme: "light" },
    legend: {
        position: "top",
        horizontalAlign: "right",
        fontSize: "12px",
        markers: { radius: 12 },
    },
}));

const evolucaoSeries = computed(() => [
    {
        name: "Custo/km",
        type: "area",
        data: evolucao.value.map((r) =>
            r.custo_km != null ? +r.custo_km.toFixed(4) : null,
        ),
    },
    {
        name: "Preço/L",
        type: "line",
        data: evolucao.value.map((r) =>
            r.preco_litro != null ? +r.preco_litro.toFixed(4) : null,
        ),
    },
]);

function buildParams() {
    return {
        ...store.paramsTempo,
        familia: familiaFiltro.value,
        grupo: store.selecao.grupo,
        filial: store.selecao.filial,
        estado: store.selecao.estado,
        regiao: store.selecao.regiao,
    };
}

async function loadAll() {
    const p = buildParams();
    const combustivel =
        familiaFiltro.value !== "todos"
            ? FAM_TO_COMB[familiaFiltro.value]
            : undefined;

    lHero.value =
        lPrecoUF.value =
        lEvolucao.value =
        lPostosVolume.value =
        lPostosCaros.value =
        lTop.value =
            true;

    Promise.allSettled([
        fetchHeroOperacional(p)
            .then((d) => (hero.value = d || {}))
            .finally(() => (lHero.value = false)),
        fetchPrecoPorUF({ ...p, combustivel })
            .then((d) => (precoPorUF.value = d || []))
            .finally(() => (lPrecoUF.value = false)),
        fetchEvolucaoMensal(p)
            .then((d) => (evolucao.value = Array.isArray(d) ? d : []))
            .finally(() => (lEvolucao.value = false)),
        fetchRankingPostosPreco({
            ...p,
            combustivel,
            ordem: "maior_volume",
            limit: 10,
        })
            .then((d) => (postosMaiorVolume.value = d))
            .finally(() => (lPostosVolume.value = false)),
        fetchRankingPostosPreco({
            ...p,
            combustivel,
            ordem: "mais_caro",
            limit: 10,
        })
            .then((d) => (postosMaisCaros.value = d))
            .finally(() => (lPostosCaros.value = false)),
        fetchTopConsumidores({ ...p, limit: 15 })
            .then((d) => (topConsumidores.value = d))
            .finally(() => (lTop.value = false)),
    ]);
}

watch(
    () => store.selecao,
    () => loadAll(),
    { deep: true },
);
onMounted(() => loadAll());
</script>

<style scoped>
.page {
    background-color: #f8fafc;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    color: #0f172a;
}
.page-body {
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 32px;
    flex: 1;
}

.fuel-selector-bar {
    display: flex;
    gap: 12px;
    background: #f1f5f9;
    padding: 6px;
    border-radius: 12px;
    align-self: flex-start;
}
.fuel-tab {
    background: transparent;
    border: none;
    padding: 8px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
}
.fuel-tab:hover {
    color: #1e293b;
    background: rgba(255, 255, 255, 0.5);
}
.fuel-tab.active {
    background: #c41230;
    color: white;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.fuel-tab.active:nth-child(2) {
    background: #2563eb;
}
.fuel-tab.active:nth-child(3) {
    background: #7c3aed;
}
.fuel-tab.active:nth-child(4) {
    background: #0891b2;
}

.v-block {
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}
.section-heading {
    font-size: 12px;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    display: flex;
    align-items: center;
    gap: 16px;
}
.section-heading::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e2e8f0;
}

.section-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.kpi-pro-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
}

.two-col {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 20px;
}
.align-stretch {
    align-items: stretch;
}
.flex-col {
    display: flex;
    flex-direction: column;
}
.flex-1 {
    flex: 1;
}

.chart-container {
    min-height: 450px;
    display: flex;
    flex-direction: column;
}

/* Grid específica para postos permitindo que encolha */
.postos-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 24px;
}
.posto-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
}
.posto-panel-title {
    font-size: 13px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.posto-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 900;
}
.posto-icon-blue {
    background: #eff6ff;
    color: #2563eb;
}
.posto-icon-orange {
    background: #fff7ed;
    color: #ea580c;
}

/* Tabela Veículos Restyled */
.table-wrap {
    overflow-x: auto;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background: white;
}
.veiculos-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    min-width: 800px;
}
.veiculos-table th {
    background: #f8fafc;
    padding: 14px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    border-bottom: 1px solid #e2e8f0;
}
.veiculos-table th.right {
    text-align: right;
}
.v-row {
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.15s;
}
.v-row:hover {
    background: #f8fafc;
}
.v-row td {
    padding: 14px 16px;
    color: #334155;
    vertical-align: middle;
}
.v-row td.right {
    text-align: right;
}

.v-placa {
    font-weight: 800;
    color: #0f172a;
    font-size: 14px;
    letter-spacing: 0.02em;
}
.v-modelo {
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
    margin-top: 2px;
}
.v-motorista {
    font-weight: 700;
    color: #334155;
    font-size: 13px;
}
.v-filial {
    font-size: 11px;
    font-weight: 500;
    color: #64748b;
    margin-top: 2px;
}
.v-cidade {
    font-weight: 600;
    color: #475569;
}

.v-bold {
    font-weight: 800;
    color: #0f172a;
    font-size: 14px;
}
.text-muted {
    color: #64748b;
    font-weight: 600;
}
.text-danger {
    color: #c41230;
}
.v-kml {
    font-size: 11px;
    color: #10b981;
    font-weight: 700;
    margin-top: 2px;
}
.mono {
    font-family: "JetBrains Mono", ui-monospace, monospace;
}

.skel {
    background: #f1f5f9;
    border-radius: 8px;
    animation: pulse 1.5s infinite;
}
.fill-skel {
    height: 100%;
    min-height: 450px;
    width: 100%;
}
@keyframes pulse {
    0%,
    100% {
        opacity: 0.6;
    }
    50% {
        opacity: 1;
    }
}

.empty {
    padding: 40px;
    text-align: center;
    color: #94a3b8;
    font-style: italic;
}

.footer {
    padding: 32px;
    border-top: 1px solid rgba(0, 0, 0, 0.07);
    font-size: 12px;
    color: #94a3b8;
    text-align: center;
}

/* Media Queries properly implemented to wrap to single column */
@media (max-width: 1200px) {
    .kpi-pro-grid {
        grid-template-columns: repeat(3, 1fr);
    }
    .two-col {
        grid-template-columns: 1fr;
    }
    .postos-grid {
        grid-template-columns: 1fr;
    }
}
@media (max-width: 768px) {
    .kpi-pro-grid {
        grid-template-columns: 1fr;
    }
    .page-body {
        padding: 16px;
    }
}
</style>
