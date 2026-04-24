<template>
    <div class="page animate-in">
        <GlobalTopbar
            title="Monitoramento de Transações"
            subtitle="Visão em tempo real das transações recusadas na TruckPag"
        />

        <div class="page-body">
            <!-- ━━━━━ KPIs ━━━━━ -->
            <section class="v-block">
                <div class="section-heading">Indicadores do Dia</div>
                <div class="kpi-pro-grid" v-if="!lKpis">
                    <KpiCardPro
                        title="Volume Movimentado"
                        :value="kpis.valor_total || 0"
                        format="currency"
                    />
                    <KpiCardPro
                        title="Aprovadas"
                        :value="kpis.qtd_aprovadas || 0"
                        format="number"
                        :description="
                            (kpis.taxa_aprovacao || 0) + '% de aprovação'
                        "
                    />
                    <KpiCardPro
                        title="Recusadas"
                        :value="kpis.qtd_recusadas || 0"
                        format="number"
                        theme="primary"
                        :description="(kpis.taxa_recusa || 0) + '% de recusa'"
                    />
                    <KpiCardPro
                        title="Placas Distintas"
                        :value="kpis.veiculos_unicos || 0"
                        format="number"
                    />
                </div>
                <div v-else class="kpi-pro-grid">
                    <div v-for="i in 4" :key="i" class="skel kpi-skel" />
                </div>
            </section>

            <!-- ━━━━━ ÁREA PRINCIPAL ━━━━━ -->
            <div class="main-grid">
                <!-- FEED DE RECUSADAS -->
                <section class="v-block" style="overflow: hidden">
                    <div
                        class="section-heading"
                        style="justify-content: space-between"
                    >
                        <div
                            style="
                                display: flex;
                                align-items: center;
                                gap: 16px;
                            "
                        >
                            Últimas Transações Recusadas
                            <span class="live-badge">● AO VIVO</span>
                        </div>
                        <div class="status-row">
                            <span
                                class="status-dot"
                                :class="{ active: !lKpis }"
                            ></span>
                            <span class="dim" style="font-size: 11px">
                                {{
                                    ultimaAtualizacao
                                        ? "Atualizado " +
                                          formatTime(ultimaAtualizacao)
                                        : "Aguardando..."
                                }}
                            </span>
                        </div>
                    </div>

                    <div class="card p-0">
                        <div
                            v-if="lRecusadas"
                            class="skel"
                            style="height: 400px; margin: 24px"
                        />
                        <div v-else-if="recusadas.length === 0" class="empty">
                            Nenhuma transação recusada hoje 🎉
                        </div>
                        <div v-else class="table-wrap">
                            <table class="t-table">
                                <thead>
                                    <tr>
                                        <th style="width: 14%">Transação</th>
                                        <th style="width: 15%">
                                            Placa / Motorista
                                        </th>
                                        <th style="width: 18%">
                                            Estabelecimento
                                        </th>
                                        <th style="width: 13%">Combustível</th>
                                        <th class="right" style="width: 10%">
                                            Valor Un.
                                        </th>
                                        <th class="right" style="width: 10%">
                                            Valor Total
                                        </th>
                                        <th style="width: 20%">
                                            Motivo / Regra do Sistema
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr
                                        v-for="t in recusadas"
                                        :key="t.transacao_id"
                                        class="t-row"
                                    >
                                        <!-- Transação -->
                                        <td>
                                            <div class="t-id mono">
                                                {{ t.transacao_id }}
                                            </div>
                                            <div class="t-time">
                                                {{
                                                    formatTime(t.transacao_data)
                                                }}
                                            </div>
                                        </td>
                                        <!-- Placa -->
                                        <td>
                                            <div class="t-placa mono">
                                                {{ t.veiculo_placa || "—" }}
                                            </div>
                                            <div class="t-motorista">
                                                {{
                                                    t.motorista_nome?.split(
                                                        " ",
                                                    )[0] || ""
                                                }}
                                            </div>
                                        </td>
                                        <!-- Estabelecimento -->
                                        <td>
                                            <div class="t-posto">
                                                {{
                                                    t.estabelecimento_nome ||
                                                    "—"
                                                }}
                                            </div>
                                            <div class="t-sub">
                                                {{
                                                    t.estabelecimento_cnpj ||
                                                    "—"
                                                }}
                                            </div>
                                        </td>
                                        <!-- Combustível -->
                                        <td>
                                            <div class="t-comb">
                                                {{ t.combustivel_nome || "—" }}
                                            </div>
                                            <div class="t-sub">
                                                {{
                                                    t.litragem
                                                        ? t.litragem.toFixed(
                                                              1,
                                                          ) + " L"
                                                        : "—"
                                                }}
                                            </div>
                                        </td>
                                        <!-- Valores -->
                                        <td class="right">
                                            <div class="t-val mono">
                                                {{ fmtR(t.valor_litro) }}
                                            </div>
                                        </td>
                                        <td class="right">
                                            <div class="t-val-total mono">
                                                {{ fmtR(t.transacao_valor) }}
                                            </div>
                                        </td>
                                        <!-- Motivo e Regra -->
                                        <td>
                                            <div class="t-motivo">
                                                <span
                                                    class="status-indicator"
                                                    :class="t.semaforo"
                                                ></span>
                                                <span>{{
                                                    t.motivo_descricao
                                                }}</span>
                                            </div>
                                            <div
                                                v-if="
                                                    t.regras_sistema &&
                                                    t.regras_sistema.tipo_regra
                                                "
                                                class="t-regra-alert"
                                            >
                                                <strong
                                                    >Regra Quebrada ({{
                                                        t.regras_sistema
                                                            .tipo_regra
                                                    }}):</strong
                                                ><br />
                                                Teto:
                                                <strong
                                                    >R$
                                                    {{
                                                        t.regras_sistema.valor_regra?.toFixed(
                                                            2,
                                                        )
                                                    }}</strong
                                                ><br />
                                                Tentativa:
                                                <strong style="color: #dc2626"
                                                    >R$
                                                    {{
                                                        t.regras_sistema.valor_tentado?.toFixed(
                                                            2,
                                                        )
                                                    }}</strong
                                                >
                                                <span class="t-diff"
                                                    >(+R$
                                                    {{
                                                        (
                                                            t.regras_sistema
                                                                .valor_tentado -
                                                            t.regras_sistema
                                                                .valor_regra
                                                        ).toFixed(2)
                                                    }})</span
                                                >
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>

                <!-- SIDEBAR: RANKING DE MOTIVOS -->
                <section class="v-block side-panel">
                    <div class="section-heading">Motivos de Recusa</div>
                    <div class="card" style="padding: 24px">
                        <div
                            v-if="lMotivos"
                            class="skel"
                            style="height: 200px"
                        />
                        <div
                            v-else-if="motivos.length === 0"
                            class="empty"
                            style="height: 100px"
                        >
                            Sem dados
                        </div>
                        <div v-else class="motivos-list">
                            <div
                                v-for="m in motivos"
                                :key="m.motivo"
                                class="motivo-item"
                            >
                                <div class="motivo-header">
                                    <span
                                        class="motivo-nome"
                                        :title="m.motivo"
                                        >{{ m.motivo }}</span
                                    >
                                    <span class="motivo-qtd">{{ m.qtd }}x</span>
                                </div>
                                <div class="motivo-bar-track">
                                    <div
                                        class="motivo-bar-fill"
                                        :style="{ width: m.pct + '%' }"
                                    />
                                </div>
                                <span class="motivo-pct">{{ m.pct }}%</span>
                            </div>
                        </div>
                    </div>

                    <!-- Controle de atualização -->
                    <div class="card" style="padding: 20px; margin-top: 0">
                        <div
                            style="display: flex; gap: 8px; align-items: center"
                        >
                            <span style="font-size: 12px; color: #94a3b8"
                                >Varredura:</span
                            >
                            <select
                                v-model="intervalo"
                                class="select-intervalo"
                                @change="resetPolling"
                            >
                                <option :value="15000">15s</option>
                                <option :value="30000">30s</option>
                                <option :value="60000">1 min</option>
                                <option :value="120000">2 min</option>
                            </select>
                        </div>
                        <button
                            @click="loadAll"
                            class="btn-atualizar"
                            :disabled="lKpis"
                        >
                            {{
                                lKpis
                                    ? "Sincronizando..."
                                    : "Forçar Sincronização"
                            }}
                        </button>
                    </div>
                </section>
            </div>
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
import { ref, onMounted, onUnmounted } from "vue";
import GlobalTopbar from "../components/GlobalTopbar.vue";
import KpiCardPro from "../components/KpiCardPro.vue";
import { GRITSCH_CONFIG } from "../gritsch.config.js";

const BASE = GRITSCH_CONFIG.URLS.BACKEND;

const kpis = ref({});
const recusadas = ref([]);
const motivos = ref([]);
const ultimaAtualizacao = ref(null);
const intervalo = ref(60000);

const lKpis = ref(true);
const lRecusadas = ref(true);
const lMotivos = ref(true);

let pollingTimer = null;

const fmtR = (v) =>
    v != null
        ? Number(v).toLocaleString("pt-BR", {
              style: "currency",
              currency: "BRL",
          })
        : "—";

const formatTime = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
};

async function loadAll() {
    lKpis.value = lRecusadas.value = lMotivos.value = true;
    await Promise.allSettled([
        fetch(`${BASE}/api/gestao-transacoes/kpis-dia`)
            .then((r) => {
                if (!r.ok) throw new Error(r.statusText);
                return r.json();
            })
            .then((d) => (kpis.value = d ?? {}))
            .catch((e) => console.warn("[Transações] KPIs:", e))
            .finally(() => (lKpis.value = false)),
        fetch(`${BASE}/api/gestao-transacoes/recusadas?limit=50`)
            .then((r) => {
                if (!r.ok) throw new Error(r.statusText);
                return r.json();
            })
            .then((d) => (recusadas.value = d ?? []))
            .catch((e) => console.warn("[Transações] Recusadas:", e))
            .finally(() => (lRecusadas.value = false)),
        fetch(`${BASE}/api/gestao-transacoes/motivos-ranking`)
            .then((r) => {
                if (!r.ok) throw new Error(r.statusText);
                return r.json();
            })
            .then((d) => (motivos.value = d ?? []))
            .catch((e) => console.warn("[Transações] Motivos:", e))
            .finally(() => (lMotivos.value = false)),
    ]);
    ultimaAtualizacao.value = new Date().toISOString();
}

function resetPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
    pollingTimer = setInterval(loadAll, intervalo.value);
}

onMounted(() => {
    loadAll();
    pollingTimer = setInterval(loadAll, intervalo.value);
});

onUnmounted(() => {
    if (pollingTimer) clearInterval(pollingTimer);
});
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
}

.v-block {
    display: flex;
    flex-direction: column;
    gap: 16px;
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

.kpi-pro-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}
.card {
    background:
        linear-gradient(white, white) padding-box,
        linear-gradient(
                135deg,
                rgba(0, 0, 0, 0.09) 0%,
                rgba(0, 0, 0, 0.04) 40%,
                rgba(0, 0, 0, 0.04) 60%,
                rgba(0, 0, 0, 0.09) 100%
            )
            border-box;
    border: 1px solid transparent;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
}
.p-0 {
    padding: 0;
    overflow: hidden;
}

/* Grid principal */
.main-grid {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 24px;
    align-items: start;
}
.side-panel {
    gap: 20px;
}

/* Live badge */
.live-badge {
    font-size: 10px;
    font-weight: 800;
    color: #c41230;
    background: #fef2f2;
    padding: 4px 10px;
    border-radius: 20px;
    animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
    0%,
    100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

/* Tabela Limpa e Fluida */
.table-wrap {
    overflow: hidden;
    border-radius: 14px;
}
.t-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed; /* Força respeitar as larguras definidas, evitando scroll lateral em TVs */
}
.t-table thead th {
    background: #f8fafc;
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    text-align: left;
    padding: 12px 14px;
    border-bottom: 1px solid #e2e8f0;
}
.t-table th.right,
.t-table td.right {
    text-align: right;
}
.t-table tbody td {
    font-size: 12px; /* Otimizado para TV */
    color: #334155;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.04);
    vertical-align: top;
    word-break: break-word; /* Remove o nowrap implícito e permite quebrar */
}
.t-table tbody tr:last-child td {
    border-bottom: none;
}
.t-row {
    transition: background 0.15s;
}
.t-row:hover {
    background: #fafbfc;
}

.mono {
    font-family: "JetBrains Mono", ui-monospace, monospace;
}

/* Celulas especificas */
.t-id {
    font-weight: 700;
    color: #1e293b;
    font-size: 13px;
}
.t-time {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
}

.t-placa {
    font-weight: 800;
    color: #0f172a;
    font-size: 13px;
    letter-spacing: 0.02em;
}
.t-motorista {
    font-size: 11px;
    color: #64748b;
    margin-top: 2px;
}

.t-posto {
    font-weight: 600;
    color: #334155;
}
.t-comb {
    font-weight: 600;
    color: #334155;
}
.t-sub {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
    word-break: break-all;
}

.t-val {
    font-weight: 600;
    color: #475569;
}
.t-val-total {
    font-weight: 800;
    color: #c41230;
    font-size: 13px;
}

.t-motivo {
    font-size: 11px;
    font-weight: 600;
    color: #334155;
    display: flex;
    align-items: flex-start;
    gap: 8px;
    line-height: 1.4;
}

.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 3px;
}
.status-indicator.red {
    background: #ef4444;
    box-shadow: 0 0 0 3px #fef2f2;
}
.status-indicator.yellow {
    background: #eab308;
    box-shadow: 0 0 0 3px #fef9c3;
}
.status-indicator.green {
    background: #22c55e;
    box-shadow: 0 0 0 3px #dcfce7;
}

/* Alerta Regra embutido na tabela */
.t-regra-alert {
    margin-top: 8px;
    background: #fff1f2;
    border: 1px solid #fecdd3;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 11px;
    color: #881337;
    line-height: 1.4;
}
.t-diff {
    font-weight: 700;
    color: #dc2626;
    margin-left: 4px;
}

/* Motivos sidebar */
.motivos-list {
    display: flex;
    flex-direction: column;
    gap: 14px;
}
.motivo-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.motivo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.motivo-nome {
    font-size: 12px;
    font-weight: 600;
    color: #334155;
    word-break: break-word;
}
.motivo-qtd {
    font-size: 12px;
    font-weight: 800;
    color: #c41230;
    font-family: "JetBrains Mono", monospace;
}
.motivo-bar-track {
    height: 6px;
    background: #f1f5f9;
    border-radius: 3px;
    overflow: hidden;
}
.motivo-bar-fill {
    height: 100%;
    background: #c41230;
    border-radius: 3px;
    transition: width 0.5s ease;
}
.motivo-pct {
    font-size: 10px;
    font-weight: 600;
    color: #94a3b8;
    font-family: "JetBrains Mono", monospace;
    text-align: right;
    margin-top: -2px;
}

/* Status e controles */
.status-row {
    display: flex;
    align-items: center;
    gap: 8px;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #94a3b8;
}
.status-dot.active {
    background: #10b981;
    animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
    0%,
    100% {
        opacity: 1;
    }
    50% {
        opacity: 0.4;
    }
}

.select-intervalo {
    font-size: 12px;
    padding: 6px 10px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: white;
    color: #334155;
    cursor: pointer;
    font-weight: 600;
    flex: 1;
}

.btn-atualizar {
    margin-top: 14px;
    width: 100%;
    padding: 10px;
    background: #1e293b;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    color: white;
    cursor: pointer;
    transition: background 0.2s;
}
.btn-atualizar:hover:not(:disabled) {
    background: #0f172a;
}
.btn-atualizar:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.empty {
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    font-style: italic;
}
.skel {
    background: #f1f5f9;
    border-radius: 12px;
    animation: pulse 1.5s infinite;
}
.kpi-skel {
    height: 130px;
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

.dim {
    color: #94a3b8;
}

.footer {
    padding: 32px;
    border-top: 1px solid rgba(0, 0, 0, 0.07);
    font-size: 12px;
    color: #94a3b8;
    text-align: center;
}

.animate-in {
    animation: fadeIn 0.25s ease-out;
}
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 1200px) {
    .main-grid {
        grid-template-columns: 1fr;
    }
    .kpi-pro-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 640px) {
    .kpi-pro-grid {
        grid-template-columns: 1fr;
    }
}
</style>
