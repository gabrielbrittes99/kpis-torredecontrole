<template>
  <div class="page animate-in">

    <!-- Topbar -->
    <GlobalTopbar
      title="Visão Geral"
      subtitle="Indicadores Mensais de Combustível"
      :ultima-atualizacao="ultimaAtualiz"
    />

    <div v-if="carregando" class="loading-state">
      <div class="spinner"></div>
      <span>Carregando dados...</span>
    </div>

    <div v-else class="page-body">

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!-- AVISO DE VEÍCULOS SEM FILIAL -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div v-if="veiculosSemFilial.length" class="alert-box alert-warning" style="margin-bottom: 24px; padding: 16px; border-radius: 12px; border: 1px solid #f59e0b; background: #fffbeb; color: #b45309; display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 20px;">⚠️</span>
        <div>
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 2px;">Atenção: Falta de Alocação de Filial para {{ veiculosSemFilial.length }} Veículos</div>
          <div style="font-size: 12px; opacity: 0.9;">As seguintes placas registraram abastecimento mas estão sem filial definida na base: <span style="font-family: monospace; font-weight: 600;">{{ veiculosSemFilial.join(', ') }}</span></div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  FAIXA HERO — KPIs Redesenhados (Moderno e Agradável)           -->
      <div class="kpi-pro-grid">
        <KpiCardPro
          title="Gasto Total"
          :value="hero.gasto_mes || 0"
          format="currency"
          :trendValue="hero.gasto_mes_var_pct"
          :trendInvert="true"
          theme="primary"
          :description="hero.trend_label ? 'vs ' + hero.trend_label : ''"
        />
        <KpiCardPro
          title="Volume (Litros)"
          :value="hero.litros_mes || 0"
          format="number"
          unit="L"
        />
        <KpiCardPro
          title="Preço Médio"
          :value="hero.preco_medio || 0"
          format="currency"
          :decimals="3"
          unit="/ L"
        />
        <KpiCardPro
          title="Abastecimentos"
          :value="hero.total_abastecimentos || 0"
          format="number"
        />
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  BREAKDOWNS — tabelas compactas lado a lado                     -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="breakdown-row">
        <!-- Por combustível -->
        <section class="bd-card">
          <div class="bd-header">
            <span class="bd-title">Por Combustível</span>
            <span class="bd-period mono">{{ mesMesLabel }}</span>
          </div>
          <table class="bd-table">
            <thead>
              <tr>
                <th></th>
                <th>Tipo</th>
                <th class="right">Valor</th>
                <th class="right">Litros</th>
                <th class="right">R$/L</th>
                <th style="width: 100px">
                  <div class="th-bar-label">Participação</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in mixCombustivel" :key="m.grupo" class="bd-row">
                <td><span class="bd-dot" :style="{ background: combustivelColor(m.grupo) }"></span></td>
                <td class="bd-name">{{ m.grupo }}</td>
                <td class="right mono bd-val">{{ fmtR(m.valor) }}</td>
                <td class="right mono bd-sub-val">{{ fmtN(m.litros) }}</td>
                <td class="right mono bd-sub-val">{{ m.litros > 0 ? (m.valor / m.litros).toFixed(3) : '—' }}</td>
                <td>
                  <div class="bd-bar-cell">
                    <div class="bd-bar-track">
                      <div class="bd-bar-fill" :style="{ width: (m.pct_local || m.pct) + '%', background: combustivelColor(m.grupo) }"></div>
                    </div>
                    <span class="bd-pct mono">{{ m.pct_local || m.pct }}%</span>
                    <button class="btn-drill" @click="irParaOperacionalCombustivel(m.grupo)" title="Ver placas deste combustível">
                      <span class="icon-drill">→</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Por grupo de veículo -->
        <section class="bd-card">
          <div class="bd-header">
            <span class="bd-title">Por Grupo de Veículo</span>
            <span class="bd-period mono">{{ mesMesLabel }}</span>
          </div>
          <table class="bd-table">
            <thead>
              <tr>
                <th></th>
                <th>Grupo</th>
                <th class="right">Valor</th>
                <th class="right">Litros</th>
                <th class="right">Veíc.</th>
                <th class="right">km/L</th>
                <th style="width: 100px">
                  <div class="th-bar-label">Participação</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in porGrupo" :key="g.grupo" class="bd-row">
                <td><span class="bd-dot" :style="{ background: grupoColor(g.grupo) }"></span></td>
                <td class="bd-name">
                  {{ g.grupo }}
                </td>
                <td class="right mono bd-val">{{ fmtR(g.gasto) }}</td>
                <td class="right mono bd-sub-val">{{ fmtN(g.litros) }}</td>
                <td class="right mono bd-sub-val">{{ g.veiculos }}</td>
                <td class="right mono bd-sub-val">{{ g.kml ?? '—' }}</td>
                <td>
                  <div class="bd-bar-cell">
                    <div class="bd-bar-track">
                      <div class="bd-bar-fill" :style="{ width: g.pct_gasto + '%', background: grupoColor(g.grupo) }"></div>
                    </div>
                    <span class="bd-pct mono">{{ g.pct_gasto }}%</span>
                    <button class="btn-drill" @click="irParaOperacional(g.grupo)" title="Ver placas deste grupo">
                      <span class="icon-drill">→</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  GRÁFICOS (Mensal 12m e Semanal 8w)                             -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="section-title-row" style="margin-bottom: 12px;">
        <span class="section-hint">Tendência de gasto ao longo do tempo</span>
        <div class="uf-comb-tabs">
          <button :class="{ active: filtroCombTendencia === null }" :style="filtroCombTendencia === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroCombTendencia(null)">Todos</button>
          <button
            v-for="c in opcoesUFComb" :key="c"
            :class="{ active: filtroCombTendencia === c }"
            :style="filtroCombTendencia === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
            @click="setFiltroCombTendencia(c)"
          >{{ c }}</button>
        </div>
      </div>
      <div class="charts-grid-top">
        <section class="v-block charts-block">
          <div class="section-title">GASTO MENSAL (12 MESES){{ filtroLabel }}</div>
          <apexchart type="bar" height="220" :options="optMensal" :series="seriesMensal" />
        </section>
        <section class="v-block charts-block">
          <div class="section-title">GASTO SEMANAL (8 SEMANAS){{ filtroLabel }}</div>
          <apexchart type="bar" height="220" :options="optSemanal" :series="seriesSemanal" />
        </section>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  PREÇO MÉDIO POR ESTADO POR COMBUSTÍVEL                        -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <section class="v-block" style="margin-bottom: 24px;">
        <div class="section-title-row">
          <div class="section-title" style="margin-bottom:0">PREÇO MÉDIO POR ESTADO (UF)</div>
          <div class="uf-comb-tabs">
            <button :class="{ active: filtroUFComb === null }" :style="filtroUFComb === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroUF(null)">Todos</button>
            <button
              v-for="c in opcoesUFComb" :key="c"
              :class="{ active: filtroUFComb === c }"
              :style="filtroUFComb === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
              @click="setFiltroUF(c)"
            >{{ c }}</button>
          </div>
        </div>
        <GraficoPrecoPorUF :data="precoPorUF" :loading="lUF" :color="filtroUFComb ? combustivelColor(filtroUFComb) : '#3b82f6'" />
      </section>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  GRÁFICO DIÁRIO — Dias Úteis · Fim de Semana · Feriados        -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="section-title-row" style="margin-bottom: 12px;">
        <span class="section-hint">Gasto diário nos últimos 30 dias</span>
        <div class="uf-comb-tabs">
          <button :class="{ active: filtroCombDiario === null }" :style="filtroCombDiario === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroCombDiario(null)">Todos</button>
          <button
            v-for="c in opcoesUFComb" :key="c"
            :class="{ active: filtroCombDiario === c }"
            :style="filtroCombDiario === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
            @click="setFiltroCombDiario(c)"
          >{{ c }}</button>
        </div>
      </div>
      <div :class="grafDiarioFeriado.length ? 'charts-grid-three' : 'charts-grid-top'" style="margin-bottom: 24px;">
        <section class="v-block charts-block" style="margin-bottom: 0;">
          <div class="section-title" style="color: #1D4ED8;">GASTO DIAS ÚTEIS (30 DIAS)</div>
          <div v-if="grafDiarioUtil.length">
            <apexchart type="area" height="200" :options="optDiarioUtil" :series="seriesDiarioUtil" />
          </div>
          <div v-else class="empty-msg">Sem dados no período</div>
        </section>
        <section class="v-block charts-block" style="margin-bottom: 0;">
          <div class="section-title" style="color: #7C3AED;">GASTO FIM DE SEMANA (30 DIAS)</div>
          <div v-if="grafDiarioFDS.length">
            <apexchart type="area" height="200" :options="optDiarioFDS" :series="seriesDiarioFDS" />
          </div>
          <div v-else class="empty-msg">Sem dados no período</div>
        </section>
        <section v-if="grafDiarioFeriado.length" class="v-block charts-block" style="margin-bottom: 0;">
          <div class="section-title" style="color: #EA580C;">GASTO FERIADOS (30 DIAS)</div>
          <apexchart type="area" height="200" :options="optDiarioFeriado" :series="seriesDiarioFeriado" />
        </section>
      </div>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  INSIGHTS POR DIMENSÃO — Combustível · Região · Grupo · Filial  -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <div class="insights-donut-row">
        <!-- Donut: Combustível -->
        <section class="v-block insights-card">
          <div class="section-title-row" style="margin-bottom: 10px;">
            <div class="section-title" style="margin-bottom:0">GASTO POR COMBUSTÍVEL — {{ mesMesLabel }}</div>
            <div class="uf-comb-tabs" style="flex-wrap: wrap; justify-content: flex-end;">
              <button :class="{ active: filtroRegiaoMix === null }" :style="filtroRegiaoMix === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroRegiaoMix(null)">Todos</button>
              <button
                v-for="r in opcoesRegiao" :key="r"
                :class="{ active: filtroRegiaoMix === r }"
                :style="filtroRegiaoMix === r ? { background: regiaoColor(r), borderColor: regiaoColor(r), color: 'white' } : { borderColor: regiaoColor(r), color: regiaoColor(r) }"
                @click="setFiltroRegiaoMix(r)"
              >{{ r }}</button>
            </div>
          </div>
          <apexchart
            v-if="mixCombustivel.length"
            type="donut"
            height="260"
            :options="optDonutComb"
            :series="seriesDonutComb"
          />
          <div v-else class="empty-msg">Sem dados</div>
        </section>

        <!-- Donut: Região -->
        <section class="v-block insights-card">
          <div class="section-title-row" style="margin-bottom: 10px;">
            <div class="section-title" style="margin-bottom:0">GASTO POR REGIÃO — {{ mesMesLabel }}</div>
            <div class="uf-comb-tabs">
              <button :class="{ active: filtroCombRegiao === null }" :style="filtroCombRegiao === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroCombRegiao(null)">Todos</button>
              <button
                v-for="c in opcoesUFComb" :key="c"
                :class="{ active: filtroCombRegiao === c }"
                :style="filtroCombRegiao === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
                @click="setFiltroCombRegiao(c)"
              >{{ c }}</button>
            </div>
          </div>
          <apexchart
            v-if="porRegiao.length"
            type="donut"
            height="240"
            :options="optDonutRegiao"
            :series="seriesDonutRegiao"
          />
          <div v-else class="empty-msg">Sem dados</div>
        </section>
      </div>

      <!-- Barra horizontal: Grupo de Veículo -->
      <section class="v-block" style="margin-bottom: 24px;">
        <div class="section-title-row">
          <div class="section-title" style="margin-bottom:0">GASTO POR GRUPO DE VEÍCULO — {{ mesMesLabel }}</div>
          <div class="uf-comb-tabs">
            <button :class="{ active: filtroCombGrupo === null }" :style="filtroCombGrupo === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroCombGrupo(null)">Todos</button>
            <button
              v-for="c in opcoesUFComb" :key="c"
              :class="{ active: filtroCombGrupo === c }"
              :style="filtroCombGrupo === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
              @click="setFiltroCombGrupo(c)"
            >{{ c }}</button>
          </div>
        </div>
        <apexchart
          v-if="porGrupoChartSeries.length"
          type="bar"
          height="320"
          :options="optBarGrupo"
          :series="porGrupoChartSeries"
        />
        <div v-else class="empty-msg">Sem dados</div>
      </section>

      <!-- Barra horizontal: Filial (top 15) -->
      <section class="v-block" style="margin-bottom: 24px;">
        <div class="section-title-row">
          <div class="section-title" style="margin-bottom:0">GASTO POR FILIAL — {{ mesMesLabel }}</div>
          <div class="uf-comb-tabs">
            <button :class="{ active: filtroCombFilial === null }" :style="filtroCombFilial === null ? { background: TODOS_COLOR, borderColor: TODOS_COLOR, color: 'white' } : { borderColor: TODOS_COLOR, color: TODOS_COLOR }" @click="setFiltroCombFilial(null)">Todos</button>
            <button
              v-for="c in opcoesUFComb" :key="c"
              :class="{ active: filtroCombFilial === c }"
              :style="filtroCombFilial === c ? { background: combustivelColor(c), borderColor: combustivelColor(c), color: 'white' } : { borderColor: combustivelColor(c), color: combustivelColor(c) }"
              @click="setFiltroCombFilial(c)"
            >{{ c }}</button>
          </div>
        </div>
        <apexchart
          v-if="filialChartSeries.length"
          type="bar"
          :height="Math.max(280, filiaisVisiveis.slice(0,15).length * 32 + 60)"
          :options="optBarFilial"
          :series="filialChartSeries"
        />
        <div v-else class="empty-msg">Sem dados</div>
      </section>

      <!-- ══════════════════════════════════════════════════════════════════ -->
      <!--  SEÇÕES RESTAURADAS A PEDIDO DO USUÁRIO                           -->
      <!-- ══════════════════════════════════════════════════════════════════ -->
      <section class="v-block">
        <div class="section-title">DESEMPENHO POR GRUPO DE VEÍCULO — {{ mesMesLabel }}</div>
        <div class="grupo-table-wrap">
          <table class="grupo-table">
            <thead>
              <tr>
                <th>Grupo</th>
                <th class="right">R$/km</th>
                <th>km/L</th>
                <th class="right">KM Rodado</th>
                <th class="right">Veíc.</th>
                <th>Participação</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="g in porGrupo" :key="g.grupo">
                <tr class="grupo-row" :class="{ 'row-expanded': grupoExpandido === g.grupo }" @click="toggleAgressores(g.grupo)">
                  <td>
                    <span class="grupo-dot" :style="{ background: grupoColor(g.grupo) }"></span>
                    <span class="grupo-nome-tbl">{{ g.grupo }}</span>
                  </td>
                  <td class="right mono">
                    <span class="val-currency">R$</span> <span class="val-primary">{{ g.custo_km != null ? g.custo_km.toFixed(3) : '—' }}</span>
                  </td>
                  <td class="col-kml">
                    <div class="kml-modern">
                      <div class="kml-m-top">
                        <span class="kml-val mono">{{ g.kml ?? '—' }}</span>
                        <span v-if="g.kml_variacao_pct != null" class="kml-pill" :class="'pill-' + g.kml_status">
                          {{ g.kml_variacao_pct > 0 ? '▲' : '▼' }} {{ Math.abs(g.kml_variacao_pct) }}%
                        </span>
                      </div>
                      <div class="kml-m-bar-wrap" v-if="g.kml_ref && g.kml">
                        <div class="kml-m-fill" :class="'fill-' + g.kml_status" :style="{ width: Math.min((g.kml / g.kml_ref) * 100, 100) + '%' }"></div>
                        <div class="kml-m-target"></div>
                      </div>
                      <div class="kml-m-bot" v-if="g.kml_ref">
                        <span>meta {{ g.kml_ref }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="right mono metric-secondary">{{ g.km_rodado ? fmtN(g.km_rodado) : '—' }}</td>
                  <td class="right mono metric-secondary">{{ g.veiculos }}</td>
                  <td>
                    <div class="bd-bar-cell">
                      <div class="bd-bar-track">
                        <div class="bd-bar-fill" :style="{ width: g.pct_gasto + '%', background: grupoColor(g.grupo) }"></div>
                      </div>
                      <span class="bd-pct mono">{{ g.pct_gasto }}%</span>
                    </div>
                  </td>
                  <td>
                    <button class="btn-expand" :class="{ 'expanded': grupoExpandido === g.grupo }">
                      {{ grupoExpandido === g.grupo ? '▴' : '▾' }}
                    </button>
                  </td>
                </tr>
                <!-- Expandable detail row -->
                <tr v-if="grupoExpandido === g.grupo" class="agressores-row">
                  <td :colspan="8">
                    <div class="agressores-panel">
                      <div v-if="lAgressores" class="agressores-loading">Carregando dados…</div>
                      <div v-else-if="!dadosAgressores" class="agressores-empty">Sem dados disponíveis</div>
                      <template v-else>
                        <!-- Header com média e tabs -->
                        <div class="detail-header">
                          <span class="ag-avg mono">Média do grupo: <strong>{{ dadosAgressores.kml_grupo_avg }}</strong> km/L · Meta: <strong>{{ dadosAgressores.kml_meta }}</strong> km/L</span>
                        </div>
                        <div class="detail-tabs">
                          <button class="detail-tab" :class="{ active: abaDetalhe === 'destaques' }" @click.stop="abaDetalhe = 'destaques'">
                            🟢 Destaques <span class="tab-count">{{ dadosAgressores.total_destaques }}</span>
                          </button>
                          <button class="detail-tab" :class="{ active: abaDetalhe === 'agressores' }" @click.stop="abaDetalhe = 'agressores'">
                            🔴 Agressores <span class="tab-count">{{ dadosAgressores.total_agressores }}</span>
                          </button>
                        </div>

                        <!-- Aba Destaques -->
                        <div v-if="abaDetalhe === 'destaques'">
                          <div class="ag-summary text-success">
                            Economia gerada: <strong>{{ fmtR(dadosAgressores.total_economia) }}</strong>
                          </div>
                          <div v-if="dadosAgressores.destaques.length === 0" class="agressores-empty">Nenhum destaque identificado</div>
                          <table v-else class="ag-table">
                            <thead>
                              <tr>
                                <th>Placa</th><th>Modelo</th>
                                <th class="right">km/L Real</th><th class="right">Meta</th>
                                <th class="right">Δ km/L</th><th class="right">KM Rodado</th>
                                <th class="right">Economia</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="d in dadosAgressores.destaques" :key="d.placa" class="ag-row">
                                <td class="mono ag-placa">{{ d.placa }}</td>
                                <td class="ag-modelo">{{ d.modelo }}</td>
                                <td class="right mono">{{ d.kml_real }}</td>
                                <td class="right mono">{{ d.kml_meta }}</td>
                                <td class="right mono text-success">+{{ Math.abs(d.delta_kml) }}</td>
                                <td class="right mono">{{ fmtN(d.km_rodado) }}</td>
                                <td class="right mono text-success">{{ fmtR(d.economia) }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>

                        <!-- Aba Agressores -->
                        <div v-if="abaDetalhe === 'agressores'">
                          <div class="ag-summary text-danger">
                            Desperdício total: <strong>{{ fmtR(dadosAgressores.total_desperdicio) }}</strong>
                          </div>
                          <div v-if="dadosAgressores.agressores.length === 0" class="agressores-empty">Nenhum agressor identificado — todos na meta!</div>
                          <table v-else class="ag-table">
                            <thead>
                              <tr>
                                <th>Placa</th><th>Modelo</th>
                                <th class="right">km/L Real</th><th class="right">Meta</th>
                                <th class="right">Δ km/L</th><th class="right">KM Rodado</th>
                                <th class="right">Desperdício</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="a in dadosAgressores.agressores" :key="a.placa" class="ag-row">
                                <td class="mono ag-placa">{{ a.placa }}</td>
                                <td class="ag-modelo">{{ a.modelo }}</td>
                                <td class="right mono">{{ a.kml_real }}</td>
                                <td class="right mono">{{ a.kml_meta }}</td>
                                <td class="right mono" :class="a.delta_kml < -1 ? 'text-danger' : 'text-warning'">{{ a.delta_kml }}</td>
                                <td class="right mono">{{ fmtN(a.km_rodado) }}</td>
                                <td class="right mono text-danger">{{ fmtR(a.desperdicio) }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </template>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </section>

      <div class="bottom-row">
        <section class="v-block mix-block">
          <div class="section-title">MIX DE COMBUSTÍVEL — {{ mesMesLabel }}</div>
          <div class="donut-mix-wrap">
            <div class="donut-chart-container">
              <apexchart type="donut" height="200" width="200" :options="donutMixOptions" :series="donutMixSeries" />
            </div>
            <div class="donut-legend">
              <div v-for="m in mixCombustivel" :key="m.grupo" class="dl-row">
                <span class="dl-dot" :style="{ background: combustivelColor(m.grupo) }"></span>
                <span class="dl-nome">{{ m.grupo }}</span>
                <span class="dl-pct mono">{{ m.pct_local || m.pct }}%</span>
                <span class="dl-val mono">{{ fmtR(m.valor) }}</span>
              </div>
            </div>
          </div>
        </section>
        <section class="v-block filiais-block">
          <div class="section-title">GASTO POR FILIAL — {{ mesMesLabel }}</div>
          <div v-if="filiaisVisiveis.length === 0" class="empty-msg">Dados de filial não disponíveis</div>
          <div v-else class="filiais-cards">
            <div v-for="f in filiaisLimitadas" :key="f.filial" class="filial-row">
              <div class="filial-row-top">
                <div class="filial-info">
                  <span class="filial-dot" :style="{ background: combustivelColor(f.combustivel_pred) }"></span>
                  <span class="filial-nome">{{ f.filial.replace('Gritsch ', '') }}</span>
                  <span class="filial-uf mono">{{ f.estado || '—' }}</span>
                </div>
                <div class="filial-nums">
                  <span class="filial-gasto mono">{{ fmtR(f.gasto) }}</span>
                  <span class="filial-pct mono">{{ filiaisTotalGasto > 0 ? (f.gasto / filiaisTotalGasto * 100).toFixed(1) + '%' : '—' }}</span>
                  <button class="btn-drill" @click="irParaOperacionalFilial(f.filial)" title="Ver operacional desta filial">
                    <span class="icon-drill">→</span>
                  </button>
                </div>
              </div>
              <div class="filial-bar-wrap">
                <div
                  class="filial-bar-fill"
                  :style="{
                    width: filiaisTotalGasto > 0 ? Math.min((f.gasto / filiaisTotalGasto * 100), 100) + '%' : '0%',
                    background: combustivelColor(f.combustivel_pred)
                  }"
                ></div>
              </div>
              <div class="filial-meta mono">
                {{ fmtN(f.litros) }} L · {{ f.veiculos }} veíc.
                <span v-if="f.combustivel_pred" class="comb-badge" :style="{ color: combustivelColor(f.combustivel_pred) }">{{ f.combustivel_pred }}</span>
              </div>
            </div>
            <button v-if="filiaisVisiveis.length > 8" class="btn-ver-mais" @click="mostrarTodasFiliais = !mostrarTodasFiliais">
              {{ mostrarTodasFiliais ? '▴ Recolher' : '▾ Ver todas (' + filiaisVisiveis.length + ')' }}
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import VueApexCharts from 'vue3-apexcharts'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import GraficoPrecoPorUF from '../components/GraficoPrecoPorUF.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import { fetchVisaoGeralDashboard, fetchAgressores } from '../api/visaoGeral.js'
import { fetchPrecoPorUF } from '../api/precos.js'
import { useFiltrosStore } from '../stores/filtros'

const apexchart = VueApexCharts
const router = useRouter()
const store = useFiltrosStore()

function irParaOperacional(grupo) {
  store.selecao.grupo = grupo
  router.push({ name: 'operacional' })
}

function irParaOperacionalFilial(filial) {
  store.selecao.filial = filial
  router.push({ name: 'operacional' })
}

function irParaOperacionalCombustivel(comb) {
  const map = { 'Diesel': 'diesel', 'Gasolina': 'gasolina', 'Álcool': 'etanol' }
  router.push({ name: 'operacional', query: { familia: map[comb] || 'todos' } })
}

const carregando   = ref(true)
const ultimaAtualiz = ref('')
const hero          = ref({})
const porGrupo      = ref([])
const mixCombustivel = ref([])
const porRegiao      = ref([])
const filiais        = ref([])
const grafMensal     = ref([])
const grafSemanal    = ref([])
const grafDiario     = ref([])

const precoPorUF     = ref([])
const lUF            = ref(true)
const filtroUFComb   = ref(null)

// Combustíveis disponíveis para os tabs de filtro (fixos — grupos padrão)
const opcoesUFComb = ['Diesel', 'Gasolina', 'Álcool', 'Arla']
const opcoesRegiao = ['Sul', 'Sudeste', 'Centro-Oeste', 'Nordeste', 'Norte']

async function setFiltroUF(comb) {
  filtroUFComb.value = comb
  lUF.value = true
  try {
    precoPorUF.value = await fetchPrecoPorUF({
      combustivel: comb ?? store.selecao.combustivel ?? undefined,
    })
  } finally {
    lUF.value = false
  }
}

// ── Filtros locais por seção ─────────────────────────────────────────────────
const filtroCombTendencia = ref(null)  // Mensal + Semanal
const filtroCombDiario    = ref(null)  // Diário
const filtroRegiaoMix     = ref(null)  // Donut/Tabela Mix Combustível
const filtroCombRegiao    = ref(null)  // Donut Região
const filtroCombGrupo     = ref(null)  // Grupo bar + KPI cards
const filtroCombFilial    = ref(null)  // Filial bar + cards

const lTendencia   = ref(false)
const lDiario      = ref(false)
const lMixComb     = ref(false)
const lRegiao      = ref(false)
const lGrupo       = ref(false)
const lFilial      = ref(false)
const lAgressores  = ref(false)

// ── Agressores (expandable in hybrid table) ──────────────────────────────────
const grupoExpandido  = ref(null)
const dadosAgressores = ref(null)
const abaDetalhe      = ref('destaques')

async function _dashboardComb(comb) {
  return fetchVisaoGeralDashboard({ ...store.selecao, combustivel: comb || undefined })
}

async function _dashboardRegiao(reg) {
  return fetchVisaoGeralDashboard({ ...store.selecao, regiao: reg || undefined })
}

async function toggleAgressores(grupo) {
  if (grupoExpandido.value === grupo) {
    grupoExpandido.value = null
    dadosAgressores.value = null
    return
  }
  grupoExpandido.value = grupo
  abaDetalhe.value = 'destaques'
  lAgressores.value = true
  dadosAgressores.value = null
  try {
    const s = store.selecao
    dadosAgressores.value = await fetchAgressores({
      grupo,
      modo_tempo: s.modo_tempo,
      mes: s.mes,
      ano: s.ano,
      bimestre: s.bimestre,
      semestre: s.semestre,
      data_inicio: s.data_inicio,
      data_fim: s.data_fim,
    })
  } catch (e) {
    console.error('Erro ao buscar agressores:', e)
    dadosAgressores.value = null
  } finally { lAgressores.value = false }
}

async function setFiltroRegiaoMix(reg) {
  filtroRegiaoMix.value = reg
  lMixComb.value = true
  try {
    const d = await _dashboardRegiao(reg)
    const mix = d.mix_combustivel ?? []
    const totalMix = mix.reduce((s, m) => s + m.valor, 0) || 1
    mix.forEach(m => m.pct_local = (m.valor / totalMix * 100).toFixed(1))
    mixCombustivel.value = mix
  } finally { lMixComb.value = false }
}

async function setFiltroCombTendencia(comb) {
  filtroCombTendencia.value = comb
  lTendencia.value = true
  try {
    const d = await _dashboardComb(comb)
    grafMensal.value  = d.grafico_mensal  ?? []
    grafSemanal.value = d.grafico_semanal ?? []
  } finally { lTendencia.value = false }
}

async function setFiltroCombDiario(comb) {
  filtroCombDiario.value = comb
  lDiario.value = true
  try {
    const d = await _dashboardComb(comb)
    grafDiario.value = d.grafico_diario ?? []
  } finally { lDiario.value = false }
}

async function setFiltroCombRegiao(comb) {
  filtroCombRegiao.value = comb
  lRegiao.value = true
  try {
    const d = await _dashboardComb(comb)
    porRegiao.value = d.por_regiao ?? []
  } finally { lRegiao.value = false }
}

async function setFiltroCombGrupo(comb) {
  filtroCombGrupo.value = comb
  lGrupo.value = true
  try {
    const d = await _dashboardComb(comb)
    porGrupo.value = d.por_grupo_veiculo ?? []
  } finally { lGrupo.value = false }
}

async function setFiltroCombFilial(comb) {
  filtroCombFilial.value = comb
  lFilial.value = true
  try {
    const d = await _dashboardComb(comb)
    filiais.value = d.filiais ?? []
  } finally { lFilial.value = false }
}

// Filiais — exclui "Sem filial identificada" da tabela (já aparece no alerta)
const filiaisVisiveis = computed(() =>
  filiais.value.filter(f => f.filial !== 'Sem filial identificada')
)

const filiaisTotalGasto = computed(() =>
  filiaisVisiveis.value.reduce((s, f) => s + (f.gasto || 0), 0)
)
const mostrarTodasFiliais = ref(false)
const filiaisLimitadas = computed(() =>
  mostrarTodasFiliais.value ? filiaisVisiveis.value : filiaisVisiveis.value.slice(0, 8)
)

const veiculosSemFilial = computed(() => {
  const sf = filiais.value.find(f => f.filial === "Sem filial identificada")
  return sf && sf.placas_pendentes ? sf.placas_pendentes : []
})

const mesMesLabel = computed(() => {
  const s = store.selecao
  if (s.modoTempo === 'mes') return store.opcoes.meses[(s.mes ?? 1) - 1] + '/' + s.ano
  if (s.modoTempo === 'bimestre') return store.opcoes.bimestres[(s.bimestre ?? 1) - 1] + '/' + s.ano
  if (s.modoTempo === 'semestre') return store.opcoes.semestres[(s.semestre ?? 1) - 1] + '/' + s.ano
  if (s.modoTempo === 'ano') return 'Ano ' + s.ano
  if (s.modoTempo === 'personalizado') return `${s.data_inicio} a ${s.data_fim}`
  return '—'
})

const filtroLabel = computed(() => {
  let labels = []
  if (store.selecao.modoTempo !== 'mes') labels.push(store.selecao.modoTempo.toUpperCase())
  
  if (store.selecao.filial) labels.push(store.selecao.filial.toUpperCase())
  else if (store.selecao.estado) labels.push(store.selecao.estado.toUpperCase())
  else if (store.selecao.regiao) labels.push(store.selecao.regiao.toUpperCase())
  
  if (store.selecao.grupo) labels.push(store.selecao.grupo.toUpperCase())
  if (store.selecao.combustivel) labels.push(store.selecao.combustivel.toUpperCase())
  
  return labels.length > 0 ? ` — ${labels.join(' | ')}` : ''
})

const fmtR = v => v != null
  ? 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
  : '—'
const fmtN = v => v != null
  ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
  : '—'

const varClass = v => v == null ? 'badge-neutral' : v > 0 ? 'badge-red' : 'badge-green'
const varIcon  = v => v == null ? '' : v > 0 ? '▲' : '▼'

// Cor do botão "Todos" (neutro, distinto dos combustíveis)
const TODOS_COLOR = '#334155'

// ── Paleta categorial — hues distintos, sem vermelho (brand/alerta) nem verde (positivo)
const FUEL_COLORS = {
  'Diesel':   '#2563EB',  // azul
  'Gasolina': '#7C3AED',  // violeta
  'Álcool':   '#0891B2',  // teal
  'Arla':     '#64748B',  // slate — aditivo, neutro
  'Outros':   '#94A3B8',
}

const GRUPO_COLORS = {
  'Bitruck': '#1E3A5F',
  'Truck':   '#1D4ED8',
  'Toco':    '#0891B2',
  '3/4':     '#4338CA',
  'Pesado':  '#7C3AED',
  'Médio':   '#A21CAF',
  'Leve':    '#EA580C',
  'Moto':    '#B45309',
  'Outros':  '#64748B',
}

const REGIAO_COLORS = {
  'Sul':          '#1D4ED8',  // azul
  'Centro-Oeste': '#EA580C',  // laranja
  'Sudeste':      '#7C3AED',  // violeta
  'Nordeste':     '#0891B2',  // teal
  'Norte':        '#A21CAF',  // fúcsia
}

const grupoColor       = g => GRUPO_COLORS[g] ?? '#94A3B8'
const combustivelColor = g => FUEL_COLORS[g]  ?? '#94A3B8'
const regiaoColor      = r => REGIAO_COLORS[r] ?? '#94A3B8'

// Semântica preservada: verde = bom · amarelo = atenção · vermelho = crítico
const benchColor = s => s === 'ok' ? '#10b981' : s === 'alerta' ? '#f59e0b' : s === 'critico' ? '#ef4444' : '#94A3B8'

const fmtRShort = v => {
  if (v == null) return '—'
  if (v >= 1e6) return 'R$ ' + (v / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + 'M'
  if (v >= 1e3) return 'R$ ' + (v / 1e3).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + 'k'
  return 'R$ ' + v.toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

// ── Donut: Combustível ────────────────────────────────────────────────────
const seriesDonutComb = computed(() => mixCombustivel.value.map(m => m.valor))
const optDonutComb = computed(() => ({
  chart: { background: 'transparent', fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  labels: mixCombustivel.value.map(m => m.grupo),
  colors: mixCombustivel.value.map(m => FUEL_COLORS[m.grupo] ?? '#6b7280'),
  legend: { position: 'bottom', fontSize: '12px', fontFamily: 'Inter, sans-serif' },
  dataLabels: { enabled: true, formatter: (val) => val.toFixed(1) + '%', style: { fontSize: '11px' } },
  plotOptions: { pie: { donut: { size: '60%', labels: {
    show: true,
    total: { show: true, label: 'Total', fontSize: '12px',
      formatter: () => fmtRShort(mixCombustivel.value.reduce((s, m) => s + m.valor, 0)) }
  } } } },
  tooltip: { y: { formatter: v => 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) } },
  stroke: { width: 2 },
}))

// ── Donut: Mix Combustível (seção inferior) ──────────────────────────────
const donutMixSeries = computed(() => mixCombustivel.value.map(m => m.valor))
const donutMixOptions = computed(() => ({
  chart: { background: 'transparent', fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  labels: mixCombustivel.value.map(m => m.grupo),
  colors: mixCombustivel.value.map(m => FUEL_COLORS[m.grupo] ?? '#6b7280'),
  legend: { show: false },
  dataLabels: { enabled: false },
  plotOptions: { pie: { donut: { size: '72%', labels: {
    show: true,
    name: { show: false },
    value: { show: false },
    total: { show: true, label: 'Total', fontSize: '11px', color: '#94a3b8',
      formatter: () => fmtRShort(mixCombustivel.value.reduce((s, m) => s + m.valor, 0)) }
  } } } },
  tooltip: { y: { formatter: v => 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) } },
  stroke: { width: 2, colors: ['#ffffff'] },
}))

// ── Donut: Região ─────────────────────────────────────────────────────────
const seriesDonutRegiao = computed(() => porRegiao.value.map(r => r.valor))
const optDonutRegiao = computed(() => ({
  chart: { background: 'transparent', fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  labels: porRegiao.value.map(r => r.regiao),
  colors: porRegiao.value.map(r => REGIAO_COLORS[r.regiao] ?? '#6b7280'),
  legend: { position: 'bottom', fontSize: '12px', fontFamily: 'Inter, sans-serif' },
  dataLabels: { enabled: true, formatter: (val) => val.toFixed(1) + '%', style: { fontSize: '11px' } },
  plotOptions: { pie: { donut: { size: '60%', labels: {
    show: true,
    total: { show: true, label: 'Regiões', fontSize: '12px',
      formatter: () => porRegiao.value.length + ' regiões' }
  } } } },
  tooltip: {
    y: {
      formatter: (v, { seriesIndex }) => {
        const r = porRegiao.value[seriesIndex]
        return 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) +
          (r ? ` · ${r.filiais} filiais · ${r.veiculos} veíc.` : '')
      }
    }
  },
  stroke: { width: 2 },
}))

// ── Barra horizontal: Grupo de Veículo ────────────────────────────────────
const porGrupoOrdenado = computed(() =>
  [...porGrupo.value].sort((a, b) => b.gasto - a.gasto)
)
const porGrupoChartSeries = computed(() =>
  porGrupoOrdenado.value.length ? [{ name: 'Gasto', data: porGrupoOrdenado.value.map(g => g.gasto) }] : []
)
const optBarGrupo = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true, barHeight: '70%' } },
  colors: porGrupoOrdenado.value.map(g => combustivelColor(g.combustivel_pred) ?? '#3b82f6'),
  legend: { show: false },
  dataLabels: {
    enabled: true,
    formatter: (v) => fmtRShort(v),
    style: { fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
    offsetX: 4,
  },
  xaxis: {
    categories: porGrupoOrdenado.value.map(g => g.grupo),
    labels: { formatter: v => fmtRShort(v), style: { colors: '#64748b', fontSize: '10px' } },
  },
  yaxis: { labels: { style: { colors: '#374151', fontSize: '12px', fontFamily: 'Inter, sans-serif' } } },
  grid: { borderColor: '#e2e8f0', xaxis: { lines: { show: true } }, yaxis: { lines: { show: false } } },
  tooltip: {
    y: {
      formatter: (v, { dataPointIndex }) => {
        const g = porGrupoOrdenado.value[dataPointIndex]
        return 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) +
          (g ? ` · ${g.veiculos} veíc. · ${g.pct_gasto}%` : '')
      }
    }
  },
}))

// ── Barra horizontal: Filial (top 15) ────────────────────────────────────
const filiaisTop15 = computed(() => filiaisVisiveis.value.slice(0, 15))
const filialChartSeries = computed(() =>
  filiaisTop15.value.length ? [{ name: 'Gasto', data: filiaisTop15.value.map(f => f.gasto) }] : []
)
const optBarFilial = computed(() => ({
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  plotOptions: { bar: { horizontal: true, borderRadius: 4, distributed: true, barHeight: '65%' } },
  colors: filiaisTop15.value.map(f => FUEL_COLORS[f.combustivel_pred] ?? '#6b7280'),
  legend: { show: false },
  dataLabels: {
    enabled: true,
    formatter: (v) => fmtRShort(v),
    style: { fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' },
    offsetX: 4,
  },
  xaxis: {
    categories: filiaisTop15.value.map(f => f.filial.replace('Gritsch ', '')),
    labels: { formatter: v => fmtRShort(v), style: { colors: '#64748b', fontSize: '10px' } },
  },
  yaxis: { labels: { style: { colors: '#374151', fontSize: '12px', fontFamily: 'Inter, sans-serif' } } },
  grid: { borderColor: '#e2e8f0', xaxis: { lines: { show: true } }, yaxis: { lines: { show: false } } },
  tooltip: {
    y: {
      formatter: (v, { dataPointIndex }) => {
        const f = filiaisTop15.value[dataPointIndex]
        return 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) +
          (f ? ` · ${f.veiculos} veíc. · ${filiaisTotalGasto.value > 0 ? (f.gasto/filiaisTotalGasto.value*100).toFixed(1) : 0}%` : '')
      }
    }
  },
}))

const chartBase = {
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  theme: { mode: 'light' },
  tooltip: { theme: 'light', y: { formatter: v => 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) } },
  yaxis: { labels: { style: { colors: '#64748b', fontSize: '11px' }, formatter: v => 'R$ ' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v) } },
  xaxis: { labels: { style: { colors: '#64748b', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  dataLabels: { enabled: false },
}

// Cor reativa: muda conforme filtro de combustível selecionado
const corTendencia = computed(() =>
  filtroCombTendencia.value ? combustivelColor(filtroCombTendencia.value) : '#1D4ED8'
)

const optMensal = computed(() => ({
  ...chartBase,
  colors: [corTendencia.value],
  xaxis: { ...chartBase.xaxis, categories: grafMensal.value.map(d => d.label) },
  plotOptions: { bar: { borderRadius: 6 } },
}))
const seriesMensal = computed(() => [{ name: 'Gasto', data: grafMensal.value.map(d => d.valor) }])

const optSemanal = computed(() => ({
  ...chartBase,
  colors: [corTendencia.value],
  xaxis: { ...chartBase.xaxis, categories: grafSemanal.value.map(d => d.label) },
  plotOptions: { bar: { borderRadius: 6 } },
}))
const seriesSemanal = computed(() => [{ name: 'Gasto', data: grafSemanal.value.map(d => d.valor) }])

// ── Gráfico diário split por tipo_dia ────────────────────────────────────
function _getTipoDia(d) {
  // 1. Backend novo: retorna tipo_dia direto
  if (d.tipo_dia) return d.tipo_dia
  // 2. Backend novo: iso_date presente
  if (d.iso_date) {
    const dt = new Date(d.iso_date + 'T12:00:00')
    const wd = dt.getDay()
    return (wd === 0 || wd === 6) ? 'fds' : 'util'
  }
  // 3. Fallback: reconstrói data a partir do label "dd/mm" + ano corrente
  if (d.label && d.label.includes('/')) {
    const [dd, mm] = d.label.split('/')
    const year = new Date().getFullYear()
    const dt = new Date(year, parseInt(mm) - 1, parseInt(dd))
    const wd = dt.getDay()
    return (wd === 0 || wd === 6) ? 'fds' : 'util'
  }
  return 'util'
}

const grafDiarioUtil     = computed(() => grafDiario.value.filter(d => _getTipoDia(d) === 'util'))
const grafDiarioFDS      = computed(() => grafDiario.value.filter(d => _getTipoDia(d) === 'fds'))
const grafDiarioFeriado  = computed(() => grafDiario.value.filter(d => _getTipoDia(d) === 'feriado'))

const _diarioOpts = (dados, color) => ({
  ...chartBase,
  colors: [color],
  xaxis: { ...chartBase.xaxis, categories: dados.map(d => d.label) },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0 } },
  stroke: { width: 2 },
  tooltip: { theme: 'light', y: { formatter: v => 'R$ ' + Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) } },
})

const optDiarioUtil    = computed(() => _diarioOpts(grafDiarioUtil.value,    '#1D4ED8'))
const optDiarioFDS     = computed(() => _diarioOpts(grafDiarioFDS.value,     '#7C3AED'))
const optDiarioFeriado = computed(() => _diarioOpts(grafDiarioFeriado.value, '#EA580C'))

const seriesDiarioUtil    = computed(() => [{ name: 'Gasto', data: grafDiarioUtil.value.map(d => d.valor) }])
const seriesDiarioFDS     = computed(() => [{ name: 'Gasto', data: grafDiarioFDS.value.map(d => d.valor) }])
const seriesDiarioFeriado = computed(() => [{ name: 'Gasto', data: grafDiarioFeriado.value.map(d => d.valor) }])

async function load() {
  carregando.value = true
  try {
    const d = await fetchVisaoGeralDashboard(store.selecao)
    hero.value          = d.hero ?? {}
    porGrupo.value      = d.por_grupo_veiculo ?? []
    
    const mix = d.mix_combustivel ?? []
    const totalMix = mix.reduce((s, m) => s + m.valor, 0) || 1
    mix.forEach(m => m.pct_local = (m.valor / totalMix * 100).toFixed(1))
    mixCombustivel.value = mix

    porRegiao.value      = d.por_regiao ?? []
    filiais.value        = d.filiais ?? []
    grafMensal.value     = d.grafico_mensal ?? []
    grafSemanal.value    = d.grafico_semanal ?? []
    grafDiario.value     = d.grafico_diario ?? []
    ultimaAtualiz.value  = 'Atualizado ' + new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

    // Reseta todos os filtros locais ao trocar filtro global
    filtroUFComb.value        = null
    filtroCombTendencia.value = null
    filtroCombDiario.value    = null
    filtroRegiaoMix.value     = null
    filtroCombRegiao.value    = null
    filtroCombGrupo.value     = null
    filtroCombFilial.value    = null
    lUF.value = true
    try {
      precoPorUF.value = await fetchPrecoPorUF({
        combustivel: store.selecao.combustivel ?? undefined,
      })
    } catch (e) {
      console.error('[VisaoGeral] Erro Preço UF', e)
    } finally {
      lUF.value = false
    }

  } catch (e) {
    console.error('[VisaoGeral]', e)
  } finally {
    carregando.value = false
  }
}

watch(
  () => store.selecao,
  () => {
    load()
  },
  { deep: true }
)

onMounted(() => {
  load()
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════ */
/*  BASE                                                                     */
/* ═══════════════════════════════════════════════════════════════════════════ */
.page {
  min-height: 100vh;
  background: var(--void, #f8fafc);
  color: #0f172a;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
}
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }

/* ═══ Topbar ══════════════════════════════════════════════════════════════ */
/* ═══ Loading ═════════════════════════════════════════════════════════════ */
.loading-state {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 16px; color: #64748b;
}
.spinner {
  width: 32px; height: 32px; border: 3px solid #e2e8f0;
  border-top-color: #C41230; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.page-body { padding: 24px 32px; flex: 1; }

/* Icons reuse from old kpi */
.kpi-blue   { background: #eff6ff; }
.kpi-orange { background: #fff7ed; }
.kpi-green  { background: #ecfdf5; }
.kpi-teal   { background: #f0fdfa; }
.kpi-purple { background: #f5f3ff; }
.kpi-slate  { background: #f1f5f9; }

.kpi-pro-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  BREAKDOWN — tabelas compactas                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */
.breakdown-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.bd-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.bd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f8fafc;
}
.bd-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}
.bd-period {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  background: #f8fafc;
  padding: 3px 10px;
  border-radius: 6px;
}

.bd-table {
  width: 100%;
  border-collapse: collapse;
}
.bd-table th {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0 10px 10px;
  border-bottom: 1px solid #f1f5f9;
  white-space: nowrap;
}
.bd-table td {
  padding: 10px;
  vertical-align: middle;
}
.bd-row {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.bd-row.clickable {
  cursor: pointer;
}
.bd-row:hover {
  background: #f8fafc;
}
.bd-row:not(:last-child) td {
  border-bottom: 1px solid #f8fafc;
}

/* Interactive Filter States */
tbody.has-filter .bd-row.dimmed {
  opacity: 0.4;
  filter: grayscale(80%);
}
tbody.has-filter .bd-row.dimmed:hover {
  opacity: 0.6;
}
.bd-row.active {
  background: #f1f5f9;
  box-shadow: inset 2px 0 0 #C41230;
}
.bd-row.active:hover {
  background: #e2e8f0;
}

.clear-filter-btn {
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  margin-left: 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.clear-filter-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}
.right { text-align: right; }

.bd-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.bd-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
}
.bd-name-icon {
  margin-right: 4px;
}
.bd-val {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}
.bd-sub-val {
  font-size: 12px;
  color: #64748b;
}

.bd-bar-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.bd-bar-track {
  flex: 1;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}
.bd-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s cubic-bezier(0.4,0,0.2,1);
}
.bd-pct {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  min-width: 32px;
  text-align: right;
}
.th-bar-label {
  font-size: 10px;
  text-align: center;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  CHARTS GRID (Layout conforme Wireframe)                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
.charts-grid-top {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
.charts-grid-bottom {
  margin-bottom: 24px;
}
.charts-grid-three {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
.charts-block { padding: 24px; }

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  SHARED                                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */
.v-block {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.section-title {
  font-size: 11px; font-weight: 700; color: #64748b;
  letter-spacing: 0.08em; text-transform: uppercase;
  border-left: 3px solid #C41230;
  padding-left: 10px;
  margin-bottom: 20px;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  ANIMATION & RESPONSIVE                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
.animate-in { animation: fadeIn 0.25s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 1200px) {
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
  .kpi-sep:nth-child(n+6) { display: none; }
  .kpi-item:nth-child(n+8) { border-top: 1px solid #f1f5f9; }
  .breakdown-row { grid-template-columns: 1fr; }
  .charts-row { grid-template-columns: 1fr; }
  .bottom-row { grid-template-columns: 1fr; }
  .insights-donut-row { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .kpi-pro-grid { grid-template-columns: 1fr; }
  .page-body { padding: 16px; }
  .topbar { padding: 0 16px; }
}
/* ═══════════════════════════════════════════════════════════════════════════ */
/*  HYBRID TABLE: DESEMPENHO POR GRUPO                                        */
/* ═══════════════════════════════════════════════════════════════════════════ */
.grupo-table-wrap {
  overflow-x: auto; border-radius: 10px; border: 1px solid #e2e8f0;
}
.grupo-table {
  width: 100%; border-collapse: collapse; font-size: 13px;
}
.grupo-table thead tr {
  background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.grupo-table th {
  padding: 12px 14px; text-align: left; font-size: 11px; font-weight: 700;
  color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
  border-right: 1px solid #e2e8f0;
}
.grupo-table th:last-child { border-right: none; }
.grupo-table th.right, .grupo-table td.right { text-align: right; }
.grupo-row {
  border-bottom: 2px solid #f8fafc; cursor: pointer; transition: all 0.2s ease;
}
.grupo-row:hover { background: #f8fafc; transform: translateY(-1px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); position: relative; z-index: 1; }
.grupo-row.row-expanded { background: #f1f5f9; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }
.grupo-row td { 
  padding: 14px 14px; color: #334155; vertical-align: middle;
  border-right: 1px solid #f1f5f9;
}
.grupo-row td:last-child { border-right: none; }
.col-kml { min-width: 140px; }

.grupo-dot {
  display: inline-block; width: 12px; height: 12px; border-radius: 3px;
  margin-right: 12px; vertical-align: middle;
}
.grupo-nome-tbl { font-weight: 700; font-size: 14px; color: #0f172a; }
.val-currency { font-size: 11px; color: #94a3b8; font-weight: 600; margin-right: 2px; }
.val-primary { font-weight: 800; font-size: 15px; color: #0f172a; letter-spacing: -0.02em; }
.metric-secondary { font-weight: 600; color: #475569; }

/* km/L smart bar */
.kml-modern { display: flex; flex-direction: column; gap: 6px; }
.kml-m-top { display: flex; align-items: center; justify-content: space-between; }
.kml-val { font-weight: 800; color: #0f172a; font-size: 14px; letter-spacing: -0.02em; }
.kml-m-bot { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; text-align: right; margin-top: -2px; }
.kml-m-bar-wrap { 
  height: 6px; background: #f1f5f9; border-radius: 3px; position: relative; overflow: visible; 
}
.kml-m-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.fill-ok { background: #10b981; }
.fill-alerta { background: #f59e0b; }
.fill-critico { background: #ef4444; }
.kml-m-target { 
  position: absolute; right: 0; top: -3px; bottom: -3px; width: 2px; 
  background: #cbd5e1; border-radius: 1px; z-index: 2;
}

.kml-pill {
  display: inline-flex; align-items: center; gap: 2px;
  font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;
  white-space: nowrap; margin-left: 4px; border: 1px solid transparent;
}
.pill-ok { background: #ecfdf5; color: #059669; border-color: #a7f3d0; }
.pill-alerta { background: #fffbeb; color: #d97706; border-color: #fde68a; }
.pill-critico { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }

/* Participation micro-bar */
.bd-bar-cell { display: flex; align-items: center; gap: 8px; min-width: 120px; }
.bd-bar-track { flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.bd-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.bd-pct { font-size: 12px; font-weight: 600; color: #64748b; min-width: 36px; text-align: right; }

/* Expand button */
.btn-expand {
  background: none; border: none; cursor: pointer; font-size: 16px;
  color: #94a3b8; transition: all 0.15s; padding: 2px 6px;
}
.btn-expand:hover { color: #475569; }
.btn-expand.expanded { color: var(--orange); }

/* Aggressors panel */
.agressores-row td { padding: 0 !important; background: #fafbfc; }
.agressores-panel {
  padding: 16px 20px 20px; border-top: 2px solid var(--orange);
  animation: slideDown 0.2s ease;
}
@keyframes slideDown { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.agressores-loading, .agressores-empty {
  font-size: 13px; color: #94a3b8; padding: 16px; text-align: center;
}
.agressores-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px; flex-wrap: wrap; gap: 8px;
}
.ag-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.ag-total-waste { font-size: 12px; color: #dc2626; }
.ag-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ag-table thead tr { background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.ag-table th {
  padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700;
  color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;
  border-right: 1px solid #f1f5f9;
}
.ag-table th:last-child { border-right: none; }
.ag-table th.right, .ag-table td.right { text-align: right; }
.ag-row { border-bottom: 1px solid #e2e8f0; transition: background 0.15s; }
.ag-row:hover { background: #f8fafc; }
.ag-row:last-child { border-bottom: none; }
.ag-row td { 
  padding: 12px 14px; color: #334155; font-weight: 500; 
  border-right: 1px solid #f8fafc; vertical-align: middle;
}
.ag-row td:last-child { border-right: none; }
.ag-row td.right { font-weight: 700; color: #0f172a; }
.ag-placa { font-weight: 800; color: #0f172a; letter-spacing: 0.02em; font-size: 14px; }
.ag-modelo { font-size: 12px; font-weight: 600; color: #64748b; max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; margin-top: 2px; }
.ag-avg { display: block; font-size: 12px; color: #475569; margin-bottom: 4px; }
.text-danger { color: #b91c1c !important; font-weight: 700; }
.text-warning { color: #b45309 !important; font-weight: 700; }
.text-success { color: #047857 !important; font-weight: 700; }

/* Detail tabs */
.detail-header { margin-bottom: 8px; }
.detail-tabs {
  display: flex; gap: 6px; margin-bottom: 14px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;
}
.detail-tab {
  background: transparent; border: 1.5px solid #e2e8f0; color: #64748b;
  font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 20px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all .15s;
}
.detail-tab.active { background: #0f172a; color: white; border-color: #0f172a; }
.detail-tab:not(.active):hover { border-color: #94a3b8; }
.tab-count {
  display: inline-block; background: rgba(0,0,0,0.08); color: inherit;
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 10px; margin-left: 4px;
}
.detail-tab.active .tab-count { background: rgba(255,255,255,0.2); }
.ag-summary {
  font-size: 14px; font-weight: 700; padding: 10px 14px; border-radius: 8px;
  margin-bottom: 12px; border: 1px solid transparent; display: flex; align-items: center;
}
.ag-summary.text-success { background: #ecfdf5; color: #047857 !important; border-color: #a7f3d0; }
.ag-summary.text-danger { background: #fef2f2; color: #b91c1c !important; border-color: #fecaca; }

/* ── Drill buttons (used in breakdown + filials) ─────────────────────────── */
.btn-drill {
  background: none; border: none; padding: 0 4px; cursor: pointer;
  color: #94a3b8; display: flex; align-items: center; justify-content: center;
  margin-left: 4px; opacity: 0; transition: all 0.2s;
}
.bd-row:hover .btn-drill { opacity: 1; color: var(--orange); }

/* ── Insights dimensão ───────────────────────────────────────────────────── */
.insights-donut-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
.insights-card { margin-bottom: 0 !important; }

.bottom-row { display: flex; gap: 24px; align-items: flex-start; }
.mix-block, .filiais-block { flex: 1; }

/* Donut Mix */
.donut-mix-wrap { display: flex; align-items: center; gap: 16px; }
.donut-chart-container { flex-shrink: 0; width: 220px; }
.donut-legend { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.dl-row {
  display: flex; align-items: center; gap: 8px; font-size: 13px;
}
.dl-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dl-nome { font-weight: 600; color: #1e293b; min-width: 70px; }
.dl-pct { font-weight: 700; color: #0f172a; min-width: 40px; text-align: right; }
.dl-val { color: #64748b; font-size: 12px; margin-left: auto; }

/* Ver mais filiais */
.btn-ver-mais {
  display: block; width: 100%; margin-top: 12px; padding: 10px;
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
  color: #475569; font-size: 12px; font-weight: 600; cursor: pointer;
  font-family: 'Inter', sans-serif; transition: all .15s;
}
.btn-ver-mais:hover { background: #f1f5f9; color: #1e293b; }

/* ── Tabs UF Combustível ─────────────────────────────────────────────────── */
.section-title-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; gap: 16px; flex-wrap: wrap;
}
.uf-comb-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.uf-comb-tabs button {
  background: transparent; border: 1.5px solid #e2e8f0; color: #64748b;
  font-size: 11px; font-weight: 700; padding: 4px 14px; border-radius: 20px;
  cursor: pointer; font-family: 'Inter', sans-serif; transition: all .15s;
  letter-spacing: 0.03em;
}
.uf-comb-tabs button.active { color: white; }
.uf-comb-tabs button:not(.active):hover { border-color: #94a3b8; }
.section-hint { font-size: 11px; color: #94a3b8; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; }

/* ── Filiais Cards ───────────────────────────────────────────────────────── */
.filiais-cards { display: flex; flex-direction: column; gap: 10px; }
.filial-row { padding: 10px 0; border-bottom: 1px solid #f1f5f9; }
.filial-row:last-child { border-bottom: none; }
.filial-row-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.filial-info { display: flex; align-items: center; gap: 8px; }
.filial-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.filial-nome { font-size: 13px; font-weight: 600; color: #1e293b; }
.filial-uf { font-size: 11px; color: #94a3b8; margin-left: 2px; }
.filial-nums { display: flex; align-items: center; gap: 12px; }
.filial-gasto { font-size: 13px; font-weight: 700; color: #0f172a; }
.filial-pct { font-size: 12px; color: #64748b; min-width: 36px; text-align: right; }
.filial-bar-wrap { height: 5px; background: #f1f5f9; border-radius: 3px; overflow: hidden; margin-bottom: 5px; }
.filial-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.filial-meta { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 8px; }
.comb-badge { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 10px; background: #f8fafc; }
.filiais-block .btn-drill { opacity: 0.4; }
.filial-row:hover .btn-drill { opacity: 1; }

.empty-msg { font-size: 13px; color: #94a3b8; padding: 24px; text-align: center; border: 1px dashed #e2e8f0; border-radius: 8px; }

</style>
