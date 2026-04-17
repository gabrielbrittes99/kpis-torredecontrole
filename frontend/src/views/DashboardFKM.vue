<template>
  <div class="page">
    <GlobalTopbar
      title="FKM · Fechamento Mensal"
      subtitle="Custo total da frota — combustível + manutenção + km rodado"
      :showPeriod="false" :showFilters="false"
    >
      <template #center>
        <div class="topbar-filters">
          <div class="filter-group">
            <label>Mês</label>
            <select v-model="filtroMes" @change="loadAll">
              <option v-for="m in filtros.meses" :key="m" :value="m">{{ fmtMes(m) }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Filial</label>
            <select v-model="filtroFilial" @change="loadAll">
              <option value="">Todas</option>
              <option v-for="f in filtros.filiais" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Grupo</label>
            <select v-model="filtroGrupo" @change="loadAll">
              <option value="">Todos</option>
              <option v-for="g in filtros.grupos" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="filter-group">
            <label>Contrato</label>
            <select v-model="filtroContrato" @change="loadAll">
              <option value="">Todos</option>
              <option v-for="c in filtros.contratos" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>
      </template>
      <template #right>
        <button class="btn-topbar btn-matriz" @click="abrirRateioMatriz">
          Rateio Matriz
        </button>
        <button class="btn-topbar btn-upload" @click="showUpload = true">
          Enviar Fechamento
        </button>
        <button class="btn-topbar" @click="refreshCache" :disabled="refreshing">
          {{ refreshing ? 'Atualizando...' : 'Recarregar Planilha' }}
        </button>
      </template>
    </GlobalTopbar>

    <div class="page-body">

      <!-- ━━━━━ SEÇÃO 1: KPIs ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Indicadores · {{ fmtMes(filtroMes) }}</div>
        <div class="kpi-pro-grid" v-if="!lKpis">
          <KpiCardPro
            title="Custo Total da Frota"
            :value="kpis.total_geral || 0"
            format="currency"
            theme="primary"
            :description="`${fmtN(kpis.qtd_veiculos)} veículos · ${fmtN(kpis.qtd_filiais)} filiais`"
          />
          <KpiCardPro
            title="Custo / KM Total"
            :value="kpis.custo_km_total || 0"
            format="currency"
            :decimals="4"
            :description="`Comb: R$ ${fmt4(kpis.custo_km_combustivel)} / km · Man: R$ ${fmt4(kpis.custo_km_manutencao)} / km`"
          />
          <KpiCardPro
            title="Total KM Rodado"
            :value="kpis.total_km || 0"
            format="number"
            unit="km"
            :description="`Média: ${fmtN(Math.round((kpis.total_km || 0) / Math.max(kpis.qtd_veiculos || 1, 1)))} km/veículo`"
          />
          <KpiCardPro
            title="Eficiência Média"
            :value="kpis.media_kml || 0"
            format="number"
            :decimals="2"
            unit="km/L"
            :description="`${fmtN(kpis.total_litros)} litros · ${fmtR(kpis.total_combustivel)} em combustível`"
          />
        </div>
        <div v-else class="kpi-pro-grid">
          <div v-for="i in 4" :key="i" class="skel kpi-skel" />
        </div>

        <!-- Sub-KPIs: categorias -->
        <div class="cat-kpis" v-if="!lKpis && kpis.total_geral">
          <div class="cat-kpi">
            <span class="cat-label">Combustível</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_combustivel) }}</span>
            <span class="cat-pct">{{ kpis.pct_combustivel }}%</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Manutenção Geral</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_geral_manutencao) }}</span>
            <span class="cat-pct">{{ kpis.pct_manutencao }}%</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Pneus</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_pneus) }}</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Lataria e Pintura</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_lataria) }}</span>
          </div>
          <div class="cat-kpi">
            <span class="cat-label">Arla</span>
            <span class="cat-value mono">{{ fmtR(kpis.total_arla) }}</span>
          </div>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO: RECONCILIAÇÃO TRUCKPAG × DIRETO ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading" style="margin-bottom:0">
            Combustível · TruckPag vs Faturado Direto · {{ fmtMes(filtroMes) }}
          </div>
          <span v-if="reconciliacao.totais?.qtd_alertas > 0" class="section-badge badge-warn">
            {{ reconciliacao.totais.qtd_alertas }} alertas de qualidade
          </span>
        </div>

        <div v-if="lReconciliacao" class="skel" style="height:160px" />
        <template v-else-if="reconciliacao.totais">

          <!-- Summary chips -->
          <div class="recon-chips">
            <div class="recon-chip">
              <span class="recon-chip-label">Total FKM (real)</span>
              <span class="recon-chip-val">{{ fmtR(reconciliacao.totais.valor_fkm) }}</span>
            </div>
            <div class="recon-chip recon-chip-tp">
              <span class="recon-chip-label">Via TruckPag</span>
              <span class="recon-chip-val">{{ fmtR(reconciliacao.totais.valor_truckpag) }}</span>
              <span class="recon-chip-pct">{{ reconciliacao.totais.pct_truckpag }}%</span>
            </div>
            <div class="recon-chip recon-chip-direto">
              <span class="recon-chip-label">Faturado Direto</span>
              <span class="recon-chip-val">{{ fmtR(reconciliacao.totais.valor_direto) }}</span>
              <span class="recon-chip-pct">{{ (100 - reconciliacao.totais.pct_truckpag).toFixed(1) }}%</span>
            </div>
            <div class="recon-chip">
              <span class="recon-chip-label">Veículos c/ Direto</span>
              <span class="recon-chip-val">{{ reconciliacao.totais.qtd_com_direto }}</span>
              <span class="recon-chip-pct">de {{ reconciliacao.totais.qtd_veiculos }} no mês</span>
            </div>
          </div>

          <!-- Tabela por filial -->
          <div class="table-wrap" v-if="reconciliacao.resumo_filiais?.length">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Filial</th>
                  <th class="right">Total FKM</th>
                  <th class="right">TruckPag</th>
                  <th class="right">Direto</th>
                  <th class="right">% TruckPag</th>
                  <th class="right">Veículos</th>
                  <th class="right">c/ Direto</th>
                  <th class="right">Alertas</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in reconciliacao.resumo_filiais" :key="row.filial">
                  <td class="filial-cell">{{ row.filial }}</td>
                  <td class="right mono">{{ fmtR(row.total_valor_fkm) }}</td>
                  <td class="right mono">{{ fmtR(row.total_valor_truckpag) }}</td>
                  <td class="right mono" :class="row.total_valor_direto > 100 ? 'text-yellow' : ''">{{ fmtR(row.total_valor_direto) }}</td>
                  <td class="right mono">
                    <div class="pct-bar-wrap">
                      <div class="pct-bar-track">
                        <div class="pct-bar-fill" :style="{ width: Math.min(row.pct_truckpag, 100) + '%' }" />
                      </div>
                      <span :class="row.pct_truckpag >= 95 ? 'text-green' : row.pct_truckpag >= 60 ? '' : 'text-yellow'">
                        {{ row.pct_truckpag }}%
                      </span>
                    </div>
                  </td>
                  <td class="right mono">{{ row.qtd_veiculos }}</td>
                  <td class="right mono" :class="row.qtd_com_direto > 0 ? 'text-yellow' : 'text-green'">{{ row.qtd_com_direto }}</td>
                  <td class="right mono" :class="row.qtd_alertas > 0 ? 'text-red' : ''">{{ row.qtd_alertas || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Veículos com alerta de qualidade -->
          <div v-if="veiculosComAlerta.length">
            <button class="btn-toggle" @click="showAlertas = !showAlertas">
              {{ showAlertas ? '▲ Ocultar' : '▼ Ver' }} veículos com alerta ({{ veiculosComAlerta.length }})
            </button>
            <div v-if="showAlertas" class="table-wrap" style="margin-top:12px">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Placa</th>
                    <th>Filial</th>
                    <th>Combustível</th>
                    <th class="right">Total FKM</th>
                    <th class="right">TruckPag</th>
                    <th class="right">Direto</th>
                    <th class="right">% TP</th>
                    <th class="right">Preço/L impl.</th>
                    <th>Alertas</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in veiculosComAlerta" :key="v.placa">
                    <td class="placa-cell mono">{{ v.placa }}</td>
                    <td class="filial-cell">{{ v.filial }}</td>
                    <td>{{ v.tp_combustivel || '—' }}</td>
                    <td class="right mono">{{ fmtR(v.valor_fkm) }}</td>
                    <td class="right mono">{{ fmtR(v.valor_truckpag) }}</td>
                    <td class="right mono" :class="v.valor_direto > 100 ? 'text-yellow' : ''">{{ fmtR(v.valor_direto) }}</td>
                    <td class="right mono">{{ v.pct_truckpag != null ? v.pct_truckpag + '%' : '—' }}</td>
                    <td class="right mono">{{ v.preco_litro_implicito != null ? fmtR(v.preco_litro_implicito) + '/L' : '—' }}</td>
                    <td>
                      <span v-for="flag in v.flags" :key="flag" class="flag-badge" :class="'flag-' + flag">{{ flagLabel(flag) }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </template>
        <div v-else class="empty">Sem dados de reconciliação para {{ fmtMes(filtroMes) }}</div>
      </section>

      <!-- ━━━━━ SEÇÃO 2: GRÁFICOS ━━━━━ -->
      <div class="two-col">

        <!-- Distribuição por categoria -->
        <section class="v-block">
          <div class="section-heading">Composição do Custo</div>
          <div v-if="lCategorias" class="skel" style="height:280px" />
          <div v-else-if="!categorias.length" class="empty">Sem dados</div>
          <apexchart
            v-else
            type="donut"
            height="280"
            :options="donutOptions"
            :series="donutSeries"
          />
        </section>

        <!-- Evolução mensal -->
        <section class="v-block">
          <div class="section-heading">Evolução Mensal</div>
          <div v-if="lEvolucao" class="skel" style="height:280px" />
          <div v-else-if="!evolucao.length" class="empty">Sem dados históricos</div>
          <apexchart
            v-else
            type="line"
            height="280"
            :options="lineOptions"
            :series="lineSeries"
          />
        </section>
      </div>

      <!-- ━━━━━ SEÇÃO EXTRA: RESUMO POR CONTRATO ━━━━━ -->
      <section class="v-block" v-if="porContrato.length > 0">
        <div class="section-heading">Resumo por Contrato · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lContratos" class="skel" style="height:200px" />
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Contrato</th>
                <th class="right">Custo Total</th>
                <th class="right">KM Rodado</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L Médio</th>
                <th class="right">Veículos Alocados</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porContrato" :key="row.contrato">
                <td class="filial-cell" style="font-weight:600; color:var(--brand);">{{ row.contrato }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_valor) }}</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono" :class="custoKmClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.media_kml ? row.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 3: RESUMO POR FILIAL ━━━━━ -->
      <section class="v-block">
        <div class="section-heading">Resumo por Filial · {{ fmtMes(filtroMes) }}</div>
        <div v-if="lFilial" class="skel" style="height:260px" />
        <div v-else-if="!porFilial.length" class="empty">Sem dados por filial</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Filial</th>
                <th class="right">KM Rodado</th>
                <th class="right">Combustível</th>
                <th class="right">Man. Geral</th>
                <th class="right">Pneus</th>
                <th class="right">Lataria</th>
                <th class="right">Total</th>
                <th class="right">Custo/KM</th>
                <th class="right">km/L</th>
                <th class="right">Veículos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in porFilial" :key="row.filial">
                <td class="filial-cell">{{ row.filial }}</td>
                <td class="right mono">{{ fmtN(row.total_km) }}</td>
                <td class="right mono">{{ fmtR(row.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(row.total_geral_manutencao) }}</td>
                <td class="right mono">{{ fmtR(row.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(row.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(row.total_geral) }}</td>
                <td class="right mono" :class="custoKmClass(row.custo_km)">{{ fmt4(row.custo_km) }}</td>
                <td class="right mono">{{ row.media_kml ? row.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ row.qtd_veiculos }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td>TOTAL</td>
                <td class="right mono">{{ fmtN(kpis.total_km) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_geral_manutencao) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_pneus) }}</td>
                <td class="right mono">{{ fmtR(kpis.total_lataria) }}</td>
                <td class="right mono fw-bold">{{ fmtR(kpis.total_geral) }}</td>
                <td class="right mono">{{ fmt4(kpis.custo_km_total) }}</td>
                <td class="right mono">{{ kpis.media_kml ? kpis.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ kpis.qtd_veiculos }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <!-- ━━━━━ SEÇÃO 4: TOP VEÍCULOS (TCO) ━━━━━ -->
      <section class="v-block">
        <div class="section-heading-row">
          <div class="section-heading">Top Veículos por Custo Total · {{ fmtMes(filtroMes) }}</div>
          <span class="section-badge">{{ veiculos.length }} veículos</span>
        </div>
        <div v-if="lVeiculos" class="skel" style="height:260px" />
        <div v-else-if="!veiculos.length" class="empty">Sem dados de veículos</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Placa</th>
                <th>Modelo</th>
                <th>Grupo</th>
                <th>Filial</th>
                <th class="right">KM</th>
                <th class="right">km/L</th>
                <th class="right">Combustível</th>
                <th class="right">Manutenção<br><span style="font-weight:400;color:#9ca3af;font-size:.68rem">man + pneus + lataria</span></th>
                <th class="right">Total</th>
                <th class="right">Custo/km<br><span style="font-weight:400;color:#9ca3af;font-size:.68rem">total</span></th>
                <th class="right">Custo/km<br><span style="font-weight:400;color:#9ca3af;font-size:.68rem">man.</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, idx) in veiculos" :key="v.placa">
                <td class="idx-cell mono">{{ idx + 1 }}</td>
                <td class="placa-cell mono">{{ v.placa }}</td>
                <td>{{ v.modelo || '—' }}</td>
                <td><span class="grupo-badge" :class="grupoBadgeClass(v.grupo)">{{ v.grupo || '—' }}</span></td>
                <td class="filial-cell">{{ v.filial || '—' }}</td>
                <td class="right mono">{{ fmtN(v.total_km) }}</td>
                <td class="right mono">{{ v.media_kml ? v.media_kml.toFixed(2) : '—' }}</td>
                <td class="right mono">{{ fmtR(v.total_combustivel) }}</td>
                <td class="right mono">{{ fmtR(v.total_geral_manutencao) }}</td>
                <td class="right mono fw-bold">{{ fmtR(v.total_geral) }}</td>
                <td class="right mono" :class="custoKmClass(v.custo_km)">{{ fmt4(v.custo_km) }}</td>
                <td class="right mono">{{ v.custo_km_man ? fmt4(v.custo_km_man) : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

    </div>

    <!-- ━━━━━ MODAL RATEIO MATRIZ ━━━━━ -->
    <Teleport to="body">
      <div class="upload-overlay" v-if="showRateio" @click.self="showRateio = false">
        <div class="upload-modal">
          <div class="upload-header">
            <div>
              <h2>Rateio · Gritsch Matriz</h2>
              <p class="matriz-subtitle">Custos de preparação e manutenção sem filial definida — aloque para os centros de custo corretos</p>
            </div>
            <button class="upload-close" @click="showRateio = false">&times;</button>
          </div>

          <div class="upload-body" v-if="rateioLoading">
            <div class="empty">Carregando custos da Matriz...</div>
          </div>

          <div class="upload-body" v-else-if="rateioData">
            <!-- Cabeçalho com KPIs -->
            <div class="matriz-kpis">
              <div class="kpi-box" :class="rateioData.resumo.total_pendente > 0 ? 'kpi-warn' : 'kpi-total'">
                <span class="kpi-val">{{ fmtR(rateioData.resumo.total_pendente) }}</span>
                <span class="kpi-lbl">Pendente de alocação</span>
              </div>
              <div class="kpi-box kpi-total">
                <span class="kpi-val">{{ fmtR(rateioData.resumo.total_alocado) }}</span>
                <span class="kpi-lbl">Já alocado</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtR(rateioData.resumo.total) }}</span>
                <span class="kpi-lbl">Total Matriz</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ rateioData.resumo.veiculos_alocados }} / {{ rateioData.resumo.total_veiculos }}</span>
                <span class="kpi-lbl">Veículos alocados</span>
              </div>
            </div>

            <!-- Tabela de veículos -->
            <div v-if="rateioData.veiculos.length === 0" class="empty">
              Nenhum custo em GRITSCH - MATRIZ para {{ fmtMes(filtroMes) }}
            </div>
            <template v-else>
              <div class="upload-table-title">
                Veículos com custo em GRITSCH - MATRIZ
                <span class="badge-warn" v-if="rateioData.resumo.total_veiculos - rateioData.resumo.veiculos_alocados > 0">
                  {{ rateioData.resumo.total_veiculos - rateioData.resumo.veiculos_alocados }} pendentes
                </span>
                <span class="badge-ok" v-else>Todos alocados</span>
              </div>
              <div class="upload-table-wrap">
                <table class="mini-table">
                  <thead>
                    <tr>
                      <th>Placa</th>
                      <th>Modelo</th>
                      <th class="right">Manutenção</th>
                      <th class="right">Combustível</th>
                      <th class="right">Arla</th>
                      <th class="right">Total</th>
                      <th>Alocar para filial</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="v in rateioData.veiculos" :key="v.placa"
                        :class="{ 'row-alocada': v.filial_alocada, 'row-pendente': !alocacoesMatriz[v.placa] && !v.filial_alocada }">
                      <td class="mono fw-bold">{{ v.placa }}</td>
                      <td class="td-modelo">{{ v.modelo || '—' }}</td>
                      <td class="right mono">{{ fmtR(v.valor_manutencao) }}</td>
                      <td class="right mono">{{ fmtR(v.valor_combustivel) }}</td>
                      <td class="right mono">{{ v.valor_arla ? fmtR(v.valor_arla) : '—' }}</td>
                      <td class="right mono fw-bold">{{ fmtR(v.total) }}</td>
                      <td>
                        <select
                          class="select-filial"
                          :value="alocacoesMatriz[v.placa] || v.filial_alocada || ''"
                          @change="alocacoesMatriz[v.placa] = $event.target.value"
                          :class="{ 'select-ok': alocacoesMatriz[v.placa] || v.filial_alocada }"
                        >
                          <option value="">— selecionar filial —</option>
                          <option v-for="f in rateioData.filiais" :key="f.sigla" :value="f.sigla">
                            {{ f.sigla }} · {{ f.nome }}
                          </option>
                        </select>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <p class="upload-error" v-if="rateioError">{{ rateioError }}</p>
          </div>

          <div class="upload-footer" v-if="rateioData && rateioData.veiculos.length > 0">
            <span class="footer-info">
              {{ Object.values(alocacoesMatriz).filter(Boolean).length + (rateioData?.resumo.veiculos_alocados || 0) }} de {{ rateioData?.resumo.total_veiculos }} alocados
            </span>
            <button class="btn-cancel" @click="showRateio = false">Fechar</button>
            <button class="btn-confirm" @click="salvarRateio" :disabled="salvandoRateio || Object.keys(alocacoesMatriz).length === 0">
              {{ salvandoRateio ? 'Salvando...' : 'Salvar Alocações' }}
            </button>
          </div>
          <div class="upload-footer" v-else-if="rateioData">
            <button class="btn-confirm" @click="showRateio = false">Fechar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ━━━━━ MODAL UPLOAD FKM ━━━━━ -->
    <Teleport to="body">
      <div class="upload-overlay" v-if="showUpload" @click.self="cancelarUpload">
        <div class="upload-modal">
          <div class="upload-header">
            <h2>Enviar Fechamento FKM</h2>
            <button class="upload-close" @click="cancelarUpload">&times;</button>
          </div>

          <!-- ── Relatório pós-gravação ── -->
          <div class="upload-body" v-if="resultadoGravacao">
            <div class="resultado-header">
              <span class="resultado-icon">✓</span>
              <div>
                <div class="resultado-titulo">Fechamento gravado com sucesso</div>
                <div class="resultado-sub">{{ resultadoGravacao.filial_nome }} · {{ fmtMes(resultadoGravacao.ano_mes) }} · {{ resultadoGravacao.total_gravados }} veículos</div>
              </div>
            </div>

            <!-- Ajustes realizados -->
            <div v-if="resultadoGravacao.relatorio_ajustes?.length">
              <div class="upload-table-title" style="margin-bottom:8px">Ajustes realizados neste fechamento</div>
              <table class="mini-table resultado-table">
                <thead>
                  <tr>
                    <th>Placa</th>
                    <th>Decisão tomada</th>
                    <th>Observação</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="aj in resultadoGravacao.relatorio_ajustes" :key="aj.placa">
                    <td class="mono fw-bold">{{ aj.placa }}</td>
                    <td>
                      <span class="resultado-badge" :class="'rb-' + aj.tipo.split('_')[0]">{{ aj.acao }}</span>
                    </td>
                    <td class="resultado-obs">{{ aj.observacao || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pendências no sistema -->
            <div v-if="resultadoGravacao.pendencias_sistema?.length" class="pendencias-wrap">
              <div class="upload-table-title pendencias-title">
                <span>⚠ Pendências a corrigir no sistema</span>
                <span class="badge-warn">{{ resultadoGravacao.pendencias_sistema.length }}</span>
              </div>
              <p class="pendencias-hint">Estes itens foram resolvidos no FKM mas indicam inconsistências no cadastro que devem ser corrigidas:</p>
              <table class="mini-table resultado-table">
                <thead>
                  <tr><th>Placa</th><th>O que corrigir no sistema</th></tr>
                </thead>
                <tbody>
                  <tr v-for="p in resultadoGravacao.pendencias_sistema" :key="p.placa">
                    <td class="mono fw-bold warn-text">{{ p.placa }}</td>
                    <td>{{ p.pendencia }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="upload-footer" v-if="resultadoGravacao">
            <button class="btn-confirm" @click="cancelarUpload">Fechar</button>
          </div>

          <!-- Seleção de arquivo -->
          <div class="upload-body" v-else-if="!uploadResult">
            <p class="upload-hint">Selecione o arquivo da filial. Formato: <strong>FKM &lt;SIGLA&gt; &lt;MMAA&gt;.xls</strong></p>
            <p class="upload-hint">Exemplo: <code>FKM CHA 0326.xls</code> = Chapecó, Março/2026</p>
            <div class="upload-drop">
              <input ref="fileInput" type="file" accept=".xls,.xlsx" @change="handleFileUpload" :disabled="uploading" />
              <span v-if="uploading">Validando...</span>
            </div>
            <p class="upload-error" v-if="uploadError">{{ uploadError }}</p>
          </div>

          <!-- Preview / Validação -->
          <div class="upload-body" v-else>

            <!-- Cabeçalho compacto -->
            <div class="upload-cabecalho">
              <div class="cab-info">
                <span class="cab-filial">{{ uploadResult.filial }} <span class="cab-sigla">({{ uploadResult.sigla }})</span></span>
                <span class="cab-sep">·</span>
                <span>{{ fmtMes(uploadResult.ano_mes) }}</span>
                <span class="cab-sep">·</span>
                <span>{{ uploadResult.total_veiculos }} veículos</span>
                <span class="cab-sep">·</span>
                <span>{{ uploadResult.dias_uteis }} dias úteis</span>
              </div>
              <span class="cab-badge" :class="uploadStatusClass">{{ uploadStatusIcon }} {{ uploadStatusLabel }}</span>
            </div>

            <!-- Alertas compactos com ações de resolução -->
            <div class="upload-msgs" v-if="uploadChecks.filter(c => c.status !== 'ok').length">
              <div
                class="msg-pill"
                v-for="chk in uploadChecks.filter(c => c.status !== 'ok')"
                :key="chk.label"
                :class="chk.status"
              >
                <span class="pill-icon">{{ chk.icon }}</span>
                <div class="pill-body">
                  <div><strong>{{ chk.label }}</strong><span v-if="chk.detail"> — {{ chk.detail }}</span></div>

                  <!-- Ações para frota incompleta (ausentes) -->
                  <div class="pill-acoes" v-if="chk.tipo === 'faltando' && chk.placas?.length">
                    <div class="placa-acao" v-for="p in chk.placas" :key="p.placa">
                      <span class="mono">{{ p.placa }}</span>
                      <span class="pa-modelo" v-if="p.modelo">{{ p.modelo }}</span>
                      <template v-if="!getAjuste(p.placa)">
                        <button class="btn-acao" @click="setAjuste(p.placa, 'ausente_manutencao')">Em manutenção</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'ausente_sinistro')">Sinistro</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'ausente_ocioso')">Ocioso</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'ausente_admin')">Administrativo</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'outro')">Outro</button>
                        <button class="btn-acao btn-acao-remover" @click="setAjuste(p.placa, 'ausente_outra_base')">Não é desta filial</button>
                      </template>
                      <template v-else>
                        <span class="acao-resolvida" :class="getAjuste(p.placa).tipo === 'ausente_outra_base' ? 'acao-removida' : ''">
                          {{ getAjuste(p.placa).tipo === 'ausente_outra_base' ? '✗ Dispensado — outra base' : '✓ ' + _TIPO_LABEL[getAjuste(p.placa).tipo] }}
                        </span>
                        <input
                          v-if="getAjuste(p.placa).tipo === 'outro'"
                          class="acao-obs"
                          placeholder="Descreva o motivo..."
                          :value="getAjuste(p.placa).observacao"
                          @input="setAjuste(p.placa, 'outro', $event.target.value)"
                        />
                        <button class="btn-acao-desfazer" @click="removeAjuste(p.placa)">desfazer</button>
                      </template>
                    </div>
                  </div>

                  <!-- Ações para veículos baixados (vendido/devolvido) -->
                  <div class="pill-acoes" v-if="chk.tipo === 'baixado' && chk.placas?.length">
                    <div class="placa-acao" v-for="p in chk.placas" :key="p.placa">
                      <span class="mono">{{ p.placa }}</span>
                      <span class="pa-modelo" v-if="p.modelo">{{ p.modelo }}</span>
                      <template v-if="!getAjuste(p.placa)">
                        <button class="btn-acao" @click="setAjuste(p.placa, 'baixado_custo')">Confirmar custo pré-baixa</button>
                      </template>
                      <template v-else>
                        <span class="acao-resolvida">✓ Custo confirmado</span>
                        <button class="btn-acao-desfazer" @click="removeAjuste(p.placa)">desfazer</button>
                      </template>
                    </div>
                  </div>

                  <!-- Ações para transferências (já gravado em outra filial no DB) -->
                  <div class="pill-acoes" v-if="chk.tipo === 'transferencia' && chk.placas?.length">
                    <div class="placa-acao" v-for="p in chk.placas" :key="p.placa">
                      <span class="mono">{{ p.placa }}</span>
                      <span class="pa-modelo" v-if="p.modelo">{{ p.modelo }}</span>
                      <span class="pa-filial-sistema">Já em: <strong>{{ p.filial_origem }}</strong></span>
                      <template v-if="!getAjuste(p.placa)">
                        <button class="btn-acao btn-acao-manter" @click="setAjuste(p.placa, 'transferencia_manter')">Custo é desta filial</button>
                        <button class="btn-acao btn-acao-remover" @click="setAjuste(p.placa, 'transferencia_remover')">Remover do FKM</button>
                      </template>
                      <template v-else>
                        <span class="acao-resolvida" :class="getAjuste(p.placa).tipo === 'transferencia_remover' ? 'acao-removida' : ''">
                          {{ getAjuste(p.placa).tipo === 'transferencia_remover' ? '✗ Será removido' : '✓ ' + _TIPO_LABEL[getAjuste(p.placa).tipo] }}
                        </span>
                        <button class="btn-acao-desfazer" @click="removeAjuste(p.placa)">desfazer</button>
                      </template>
                    </div>
                  </div>

                  <!-- Ações para veículos sem nenhum custo -->
                  <div class="pill-acoes" v-if="chk.tipo === 'sem_custo' && chk.placas?.length">
                    <div class="placa-acao" v-for="p in chk.placas" :key="p.placa">
                      <span class="mono">{{ p.placa }}</span>
                      <span class="pa-modelo" v-if="p.modelo">{{ p.modelo }}</span>
                      <span class="pa-grupo" v-if="p.grupo">{{ p.grupo }}</span>
                      <template v-if="!getAjuste(p.placa)">
                        <button class="btn-acao" @click="setAjuste(p.placa, 'sem_custo_admin')">Administrativo</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'sem_custo_ocioso')">Encostado/ocioso</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'sem_custo_outro')">Outro</button>
                      </template>
                      <template v-else>
                        <span class="acao-resolvida">✓ {{ _TIPO_LABEL[getAjuste(p.placa).tipo] }}</span>
                        <input
                          v-if="getAjuste(p.placa).tipo === 'sem_custo_outro'"
                          class="acao-obs"
                          placeholder="Descreva o motivo..."
                          :value="getAjuste(p.placa).observacao"
                          @input="setAjuste(p.placa, 'sem_custo_outro', $event.target.value)"
                        />
                        <button class="btn-acao-desfazer" @click="removeAjuste(p.placa)">desfazer</button>
                      </template>
                    </div>
                  </div>

                  <!-- Ações para veículos com filial divergente no sistema -->
                  <div class="pill-acoes" v-if="chk.tipo === 'filial_errada' && chk.placas?.length">
                    <div class="placa-acao" v-for="p in chk.placas" :key="p.placa">
                      <span class="mono">{{ p.placa }}</span>
                      <span class="pa-modelo" v-if="p.modelo">{{ p.modelo }}</span>
                      <span class="pa-filial-sistema" :title="'Última movimentação registrada no BlueFleet até ' + uploadResult?.ano_mes">Última localização: <strong>{{ p.filial_sistema }}</strong></span>
                      <template v-if="!getAjuste(p.placa)">
                        <button class="btn-acao btn-acao-manter" @click="setAjuste(p.placa, 'filial_parcial')">Custo do período</button>
                        <button class="btn-acao" @click="setAjuste(p.placa, 'filial_errada_manter')">Sistema desatualizado</button>
                        <button class="btn-acao btn-acao-remover" @click="setAjuste(p.placa, 'filial_errada_remover')">Remover do FKM</button>
                      </template>
                      <template v-else>
                        <span class="acao-resolvida" :class="getAjuste(p.placa).tipo === 'filial_errada_remover' ? 'acao-removida' : ''">
                          {{ getAjuste(p.placa).tipo === 'filial_errada_remover' ? '✗ Será removido' : '✓ ' + _TIPO_LABEL[getAjuste(p.placa).tipo] }}
                        </span>
                        <button class="btn-acao-desfazer" @click="removeAjuste(p.placa)">desfazer</button>
                      </template>
                    </div>
                  </div>

                  <!-- Divergência manutenção BlueFleet vs FKM -->
                  <div class="pill-acoes pill-acoes-divman" v-if="chk.tipo === 'divergencia_man' && chk.placas?.length">
                    <table class="mini-table divman-table">
                      <thead>
                        <tr>
                          <th>Placa</th>
                          <th>Modelo</th>
                          <th class="right">Manutenção FKM</th>
                          <th class="right">BlueFleet</th>
                          <th class="right">Diferença</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="d in chk.placas" :key="d.placa">
                          <td class="mono warn-text">{{ d.placa }}</td>
                          <td>{{ d.modelo || '—' }}</td>
                          <td class="right mono">{{ fmtR(d.fkm_man) }}</td>
                          <td class="right mono">{{ fmtR(d.blue_man) }}</td>
                          <td class="right mono" style="color: var(--red); font-weight: 600;">+ {{ fmtR(d.diferenca) }}</td>
                        </tr>
                      </tbody>
                    </table>
                    <p class="divman-hint">
                      Verifique no BlueFleet quais OS estão faltando no FKM e atualize a planilha antes de confirmar o fechamento.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- KPIs de resumo -->
            <div class="upload-kpis" v-if="uploadResult.validacao?.resumo">
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtN(uploadResult.validacao.resumo.total_km) }}</span>
                <span class="kpi-lbl">KM Total</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtN(uploadResult.validacao.resumo.total_litros) }}</span>
                <span class="kpi-lbl">Litros</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtKml(uploadResult.validacao.resumo.total_km, uploadResult.validacao.resumo.total_litros) }}</span>
                <span class="kpi-lbl">Média km/L</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtPrecoL(uploadResult.validacao.resumo.total_valor_comb, uploadResult.validacao.resumo.total_litros) }}</span>
                <span class="kpi-lbl">Preço médio/L</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtR(uploadResult.validacao.resumo.total_valor_comb) }}</span>
                <span class="kpi-lbl">Combustível</span>
              </div>
              <div class="kpi-box">
                <span class="kpi-val">{{ fmtR(uploadResult.validacao.resumo.total_manutencao) }}</span>
                <span class="kpi-lbl">Manutenção</span>
              </div>
              <div class="kpi-box kpi-total">
                <span class="kpi-val">{{ fmtR(uploadResult.validacao.resumo.total_geral) }}</span>
                <span class="kpi-lbl">Total Geral</span>
              </div>
              <div class="kpi-box kpi-total">
                <span class="kpi-val">{{ fmtCustoKm(uploadResult.validacao.resumo.total_geral, uploadResult.validacao.resumo.total_km) }}</span>
                <span class="kpi-lbl">Custo/km</span>
              </div>
            </div>

            <!-- Tabela de veículos -->
            <div class="upload-table-title">
              Veículos
              <span class="badge-ok">{{ uploadResult.veiculos?.length }}</span>
              <span v-if="uploadResult.validacao?.placas_faltando?.length" class="badge-warn">{{ uploadResult.validacao.placas_faltando.length }} faltando</span>
            </div>
            <div class="upload-table-wrap">
              <table class="mini-table">
                <thead>
                  <tr>
                    <th class="sortable" @click="toggleSort('placa')">Placa <span class="sort-icon">{{ sortIcon('placa') }}</span></th>
                    <th class="sortable" @click="toggleSort('modelo')">Modelo <span class="sort-icon">{{ sortIcon('modelo') }}</span></th>
                    <th class="sortable" @click="toggleSort('grupo')">Grupo <span class="sort-icon">{{ sortIcon('grupo') }}</span></th>
                    <th class="sortable" @click="toggleSort('contrato')">Contrato <span class="sort-icon">{{ sortIcon('contrato') }}</span></th>
                    <th class="right sortable" @click="toggleSort('total_km')">KM <span class="sort-icon">{{ sortIcon('total_km') }}</span></th>
                    <th class="right sortable" @click="toggleSort('litros')">Litros <span class="sort-icon">{{ sortIcon('litros') }}</span></th>
                    <th class="right sortable" @click="toggleSort('kml')">km/L <span class="sort-icon">{{ sortIcon('kml') }}</span></th>
                    <th class="right sortable" @click="toggleSort('preco_l')">Preço/L <span class="sort-icon">{{ sortIcon('preco_l') }}</span></th>
                    <th class="right sortable" @click="toggleSort('valor_comb')">Combustível <span class="sort-icon">{{ sortIcon('valor_comb') }}</span></th>
                    <th class="right sortable" @click="toggleSort('custo_km_comb')">Custo/km<br><span class="th-sub">comb.</span> <span class="sort-icon">{{ sortIcon('custo_km_comb') }}</span></th>
                    <th class="right sortable" @click="toggleSort('manutencao')">Manutenção<br><span class="th-sub">man+pneus+lat.</span> <span class="sort-icon">{{ sortIcon('manutencao') }}</span></th>
                    <th class="right sortable" @click="toggleSort('total')">Total <span class="sort-icon">{{ sortIcon('total') }}</span></th>
                    <th class="right sortable" @click="toggleSort('custo_km_total')">Custo/km<br><span class="th-sub">total</span> <span class="sort-icon">{{ sortIcon('custo_km_total') }}</span></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in veiculosComMetricas" :key="v.placa" :class="{ 'row-zero': v.total === 0 }">
                    <td class="mono">{{ v.placa }}</td>
                    <td class="td-modelo">{{ v.modelo || '—' }}</td>
                    <td>{{ v.grupo }}</td>
                    <td class="td-contrato">{{ v.contrato }}</td>
                    <td class="right mono">{{ fmtN(v.total_km) }}</td>
                    <td class="right mono">{{ fmtN(v.litros) }}</td>
                    <td class="right mono" :class="v.kml_class">{{ v.kml }}</td>
                    <td class="right mono" :class="v.preco_class">{{ v.preco_l }}</td>
                    <td class="right mono">{{ fmtR(v.valor_comb) }}</td>
                    <td class="right mono">{{ v.custo_km_comb }}</td>
                    <td class="right mono">{{ fmtR(v._man_total_val) }}</td>
                    <td class="right mono" :class="{ 'cell-zero': v.total === 0 }">{{ fmtR(v.total) }}</td>
                    <td class="right mono">{{ v.custo_km_total }}</td>
                  </tr>
                </tbody>
                <tfoot v-if="uploadResult.validacao?.resumo">
                  <tr class="tfoot-row">
                    <td colspan="4"><strong>Total</strong></td>
                    <td class="right mono"><strong>{{ fmtN(uploadResult.validacao.resumo.total_km) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtN(uploadResult.validacao.resumo.total_litros) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtKml(uploadResult.validacao.resumo.total_km, uploadResult.validacao.resumo.total_litros) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtPrecoL(uploadResult.validacao.resumo.total_valor_comb, uploadResult.validacao.resumo.total_litros) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtR(uploadResult.validacao.resumo.total_valor_comb) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtCustoKm(uploadResult.validacao.resumo.total_valor_comb, uploadResult.validacao.resumo.total_km) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtR(uploadResult.validacao.resumo.total_manutencao) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtR(uploadResult.validacao.resumo.total_geral) }}</strong></td>
                    <td class="right mono"><strong>{{ fmtCustoKm(uploadResult.validacao.resumo.total_geral, uploadResult.validacao.resumo.total_km) }}</strong></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <!-- Placas faltando -->
            <div class="upload-faltando" v-if="uploadResult.validacao?.placas_faltando?.length">
              <div class="upload-table-title">
                Veículos ativos ausentes no FKM
                <span class="badge-warn">{{ uploadResult.validacao.placas_faltando.length }}</span>
              </div>
              <table class="mini-table">
                <thead><tr><th>Placa</th><th>Modelo</th><th>Situação</th></tr></thead>
                <tbody>
                  <tr v-for="p in uploadResult.validacao.placas_faltando" :key="p.placa">
                    <td class="mono warn-text">{{ p.placa }}</td>
                    <td>{{ p.modelo }}</td>
                    <td>{{ p.situacao }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p class="upload-error" v-if="uploadError">{{ uploadError }}</p>

          </div>

          <!-- Footer fixo — fora do scroll body -->
          <div class="upload-footer" v-if="uploadResult">
            <button class="btn-cancel" @click="cancelarUpload">Cancelar</button>
            <button
              class="btn-confirm"
              @click="confirmarUpload"
              :disabled="confirmando || !uploadResult.validacao?.pode_salvar"
            >
              {{ confirmando ? 'Gravando...' : (uploadResult.ja_existe ? 'Sobrescrever Fechamento' : 'Confirmar Fechamento') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import GlobalTopbar from '../components/GlobalTopbar.vue'
import KpiCardPro from '../components/KpiCardPro.vue'
import {
  fetchFkmFiltros,
  fetchFkmKpis,
  fetchFkmResumoPorFilial,
  fetchFkmCustoPorVeiculo,
  fetchFkmEvolucaoMensal,
  fetchFkmDistribuicaoCategorias,
  fetchFkmReconciliacao,
  fetchFkmRateioMatriz,
  salvarRateioMatriz,
  uploadFkmFile,
  confirmarFkmUpload,
} from '../api/fkm.js'
import { fetchContratosKpis } from '../api/contratos.js'

// ── Estado ────────────────────────────────────────────────────────────────
const filtros   = ref({ meses: [], filiais: [], grupos: [], combustiveis: [], contratos: [] })
const filtroMes = ref('')
const filtroFilial = ref('')
const filtroGrupo  = ref('')
const filtroContrato = ref('')

const kpis      = ref({})
const categorias = ref([])
const evolucao  = ref([])
const porFilial = ref([])
const veiculos  = ref([])
const porContrato = ref([])

const lKpis           = ref(true)
const lCategorias     = ref(true)
const lEvolucao       = ref(true)
const lFilial         = ref(true)
const lVeiculos       = ref(true)
const lContratos      = ref(true)
const lReconciliacao  = ref(true)
const refreshing      = ref(false)

const reconciliacao   = ref({})
const showAlertas     = ref(false)

// ── Upload FKM ───────────────────────────────────────────────────────────
const showUpload    = ref(false)
const resultadoGravacao = ref(null)  // relatório pós-confirmação

// ── Rateio Matriz ─────────────────────────────────────────────────────────
const showRateio      = ref(false)
const rateioLoading   = ref(false)
const rateioData      = ref(null)
const rateioError     = ref('')
const salvandoRateio  = ref(false)
const alocacoesMatriz = ref({})  // placa → sigla_filial (pendentes de salvar)
const uploading     = ref(false)
const confirmando   = ref(false)
const uploadResult  = ref(null)
const uploadError   = ref('')
const fileInput     = ref(null)

/// Ajustes manuais: { placa, tipo, observacao }
const ajustes = ref({})  // chave: placa

function setAjuste(placa, tipo, obs = '') {
  ajustes.value = { ...ajustes.value, [placa]: { placa, tipo, observacao: obs } }
}
function removeAjuste(placa) {
  const novo = { ...ajustes.value }
  delete novo[placa]
  ajustes.value = novo
}
function getAjuste(placa) {
  return ajustes.value[placa] || null
}

const _TIPO_LABEL = {
  ausente_manutencao:    'Em manutenção',
  ausente_sinistro:      'Sinistro',
  ausente_ocioso:        'Veículo ocioso',
  ausente_admin:         'Administrativo',
  ausente_outra_base:    'Não pertence a esta filial',
  baixado_custo:         'Custo pré-venda confirmado',
  outro:                 'Outro motivo',
  filial_parcial:        'Custo do período confirmado',
  filial_errada_manter:  'Sistema desatualizado — mantido',
  filial_errada_remover: 'Removido do FKM',
  transferencia_manter:  'Custo confirmado aqui',
  transferencia_remover: 'Removido do FKM',
  sem_custo_admin:       'Administrativo — custo zero intencional',
  sem_custo_ocioso:      'Encostado/ocioso — custo zero intencional',
  sem_custo_outro:       'Justificado',
}

async function handleFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploading.value = true
  uploadError.value = ''
  uploadResult.value = null
  ajustes.value = {}
  try {
    uploadResult.value = await uploadFkmFile(file)
    if (!uploadResult.value.sucesso) {
      uploadError.value = uploadResult.value.erro
      uploadResult.value = null
    }
  } catch (e) {
    uploadError.value = e.message || 'Erro ao enviar arquivo'
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function confirmarUpload() {
  if (!uploadResult.value?.upload_key) return
  confirmando.value = true
  try {
    const listaAjustes = Object.values(ajustes.value)
    const res = await confirmarFkmUpload(uploadResult.value.upload_key, listaAjustes)
    if (res.sucesso) {
      uploadResult.value = null
      ajustes.value = {}
      loadAll()
      // Só mostra relatório se houve ajustes; senão fecha direto
      if (res.relatorio_ajustes?.length || res.pendencias_sistema?.length) {
        resultadoGravacao.value = res
      } else {
        showUpload.value = false
      }
    } else {
      uploadError.value = res.erro
    }
  } catch (e) {
    console.error('Erro ao confirmar FKM:', e)
    uploadError.value = e.message || String(e)
  } finally {
    confirmando.value = false
  }
}

async function abrirRateioMatriz() {
  showRateio.value = true
  rateioLoading.value = true
  rateioError.value = ''
  alocacoesMatriz.value = {}
  try {
    rateioData.value = await fetchFkmRateioMatriz(filtroMes.value)
  } catch (e) {
    rateioError.value = e.message || 'Erro ao carregar dados da Matriz'
  } finally {
    rateioLoading.value = false
  }
}

async function salvarRateio() {
  const itens = Object.entries(alocacoesMatriz.value)
    .filter(([, sigla]) => sigla)
    .map(([placa, sigla]) => ({ placa, filial_destino_sigla: sigla }))
  if (!itens.length) return
  salvandoRateio.value = true
  rateioError.value = ''
  try {
    await salvarRateioMatriz(filtroMes.value, itens)
    // Recarrega para refletir alocações salvas
    rateioData.value = await fetchFkmRateioMatriz(filtroMes.value)
    alocacoesMatriz.value = {}
  } catch (e) {
    rateioError.value = e.message || 'Erro ao salvar alocações'
  } finally {
    salvandoRateio.value = false
  }
}

function cancelarUpload() {
  uploadResult.value = null
  uploadError.value = ''
  ajustes.value = {}
  resultadoGravacao.value = null
  showUpload.value = false
}

// ── Computed de validação visual ─────────────────────────────────────────
const uploadChecks = computed(() => {
  const val = uploadResult.value?.validacao
  if (!val) return []

  const alertas = val.alertas || []
  const erros   = val.erros   || []
  const checks  = []

  // 1. Frota completa
  const faltando = val.placas_faltando?.length || 0
  if (faltando === 0) {
    checks.push({ label: 'Frota completa', detail: 'Todos os veículos ativos estão no arquivo', status: 'ok', icon: '✓' })
  } else {
    checks.push({
      label: `Frota incompleta — ${faltando} ativo(s) ausente(s)`,
      detail: 'Selecione o motivo para cada veículo para incluir no fechamento:',
      status: 'warn', icon: '⚠',
      tipo: 'faltando',
      placas: val.placas_faltando,
    })
  }

  // 2. Placas reconhecidas
  const naoEncontradas = alertas.filter(a => a.includes('não encontrada no sistema'))
  checks.push(naoEncontradas.length === 0
    ? { label: 'Placas reconhecidas', detail: 'Todas as placas existem no sistema', status: 'ok', icon: '✓' }
    : { label: `${naoEncontradas.length} placa(s) não reconhecida(s)`, detail: naoEncontradas.map(a => a.split(':')[0]).join(', '), status: 'warn', icon: '⚠' }
  )

  // 3. Placas já gravadas em outra filial (transferência)
  const placasTransf = val.placas_transferencia || []
  const transferencias = alertas.filter(a => a.includes('possível transferência'))
  if (placasTransf.length > 0) {
    checks.push({
      label: `${placasTransf.length} transferência(s) detectada(s)`,
      detail: 'Placa já gravada em outra filial neste mês. Confirme se o custo é desta filial ou se deve ser removido:',
      status: 'warn', icon: '⚠',
      tipo: 'transferencia',
      placas: placasTransf,
    })
  } else if (transferencias.length > 0) {
    checks.push({ label: `${transferencias.length} transferência(s) detectada(s)`, detail: transferencias.map(a => a.split(':')[0]).join(', '), status: 'warn', icon: '⚠' })
  }

  // 4. Km negativo (bloqueante)
  const kmNeg = erros.filter(e => e.includes('km negativo'))
  checks.push(kmNeg.length === 0
    ? { label: 'Km sem negativos', detail: 'Nenhum valor de km negativo', status: 'ok', icon: '✓' }
    : { label: 'Km negativo detectado', detail: kmNeg.join(' | '), status: 'error', icon: '✗' }
  )

  // 5. Km/L dentro do esperado
  const kmlFora = alertas.filter(a => a.includes('km/L') && a.includes('fora do range'))
  checks.push(kmlFora.length === 0
    ? { label: 'Km/L dentro do esperado', detail: 'Todos os veículos com consumo normal', status: 'ok', icon: '✓' }
    : { label: `${kmlFora.length} veículo(s) com km/L fora do range`, detail: kmlFora.map(a => a.split(':')[0]).join(', '), status: 'warn', icon: '⚠' }
  )

  // 6. Combustível sem valor
  const semValor = alertas.filter(a => a.includes('litros mas valor'))
  checks.push(semValor.length === 0
    ? { label: 'Valores de combustível consistentes', detail: 'Sem litros com valor R$ 0', status: 'ok', icon: '✓' }
    : { label: 'Litros sem valor registrado', detail: semValor.map(a => a.split(':')[0]).join(', '), status: 'warn', icon: '⚠' }
  )

  // 7. Veículos sem custo
  const placasSemCusto = val.placas_sem_custo || []
  if (placasSemCusto.length > 0) {
    checks.push({
      label: `${placasSemCusto.length} veículo(s) sem nenhum custo`,
      detail: 'Justifique o motivo para manter no fechamento:',
      status: 'warn', icon: '⚠',
      tipo: 'sem_custo',
      placas: placasSemCusto,
    })
  } else {
    checks.push({ label: 'Todos os veículos com algum custo', detail: 'Nenhum veículo zerado', status: 'ok', icon: '✓' })
  }

  // 8. Preço por litro
  const precSusp = alertas.filter(a => a.includes('preço/L'))
  checks.push(precSusp.length === 0
    ? { label: 'Preço por litro normal', detail: 'Todos dentro da faixa R$3,50–R$10,00', status: 'ok', icon: '✓' }
    : { label: `${precSusp.length} veículo(s) com preço/L suspeito`, detail: precSusp.map(a => a.split(':')[0]).join(', '), status: 'warn', icon: '⚠' }
  )

  // 9. Sobrescrita de fechamento anterior
  if (uploadResult.value?.ja_existe) {
    const sobreAlerta = alertas.find(a => a.includes('vai sobrescrever'))
    checks.push({ label: 'Fechamento já existe para este mês', detail: sobreAlerta || 'O upload vai sobrescrever os dados anteriores desta filial.', status: 'warn', icon: '⚠' })
  }

  // 10. Placas vendidas/devolvidas presentes no FKM
  const vendidos = alertas.filter(a => a.includes("'Vendido'") || a.includes("'Devolvido'") || a.includes("'Disponível para Venda'"))
  if (vendidos.length > 0) {
    const placasVendidas = vendidos.map(a => {
      const placa = a.split(':')[0].trim()
      const sit = a.match(/'([^']+)'/)?.[1] || ''
      // Busca modelo na lista de veículos do preview
      const veic = uploadResult.value?.veiculos?.find(v => v.placa === placa)
      return { placa, modelo: veic?.modelo || sit }
    })
    checks.push({
      label: `${vendidos.length} veículo(s) baixado(s) presentes no FKM`,
      detail: 'Confirme se o custo é referente ao período em que o veículo ainda estava ativo:',
      status: 'warn', icon: '⚠',
      tipo: 'baixado',
      placas: placasVendidas,
    })
  }

  // 11. Placas com filial divergente no sistema (novo campo estruturado)
  const filialErrada = val.placas_filial_errada || []
  const outraFilialAlerta = alertas.filter(a => a.includes('filial divergente no sistema'))
  if (filialErrada.length > 0) {
    checks.push({
      label: `${filialErrada.length} veículo(s) com localização divergente`,
      detail: 'A última movimentação registrada no BlueFleet aponta outra filial/localização. Pode ser veículo em manutenção na Matriz, transferência, ou dado desatualizado:',
      status: 'warn', icon: '⚠',
      tipo: 'filial_errada',
      placas: filialErrada,
    })
  }

  // 12. Divergência manutenção BlueFleet vs FKM
  const divMan = val.divergencias_manutencao || []
  if (divMan.length > 0) {
    const totalDiv = divMan.reduce((s, d) => s + d.diferenca, 0)
    checks.push({
      label: `${divMan.length} veículo(s) com custo de manutenção abaixo do BlueFleet`,
      detail: `BlueFleet registra mais manutenção do que o FKM declara (total faltando: R$ ${totalDiv.toLocaleString('pt-BR', { minimumFractionDigits: 2 })})`,
      status: 'warn', icon: '⚠',
      tipo: 'divergencia_man',
      placas: divMan,
    })
  } else if (divMan !== undefined) {
    checks.push({ label: 'Manutenção alinhada com BlueFleet', detail: 'Todos os custos BlueFleet estão refletidos no FKM', status: 'ok', icon: '✓' })
  }

  // 13. Outros alertas não categorizados
  const semCustoAlerta = alertas.filter(a => a.includes('sem nenhum custo'))
  const divManAlerta = alertas.filter(a => a.includes('custo de manutenção no BlueFleet'))
  const categorizados = [
    ...naoEncontradas, ...transferencias, ...kmlFora, ...semValor, ...precSusp,
    ...vendidos, ...outraFilialAlerta, ...semCustoAlerta, ...divManAlerta,
    ...(alertas.filter(a => a.includes('vai sobrescrever'))),
    ...(alertas.filter(a => a.includes('ativo(s) no sistema não estão no FKM'))),
    ...(alertas.filter(a => a.includes('filial divergente no sistema'))),
  ]
  const outros = alertas.filter(a => !categorizados.includes(a))
  for (const a of outros) {
    checks.push({ label: 'Atenção', detail: a, status: 'warn', icon: '⚠' })
  }

  return checks
})

const uploadStatusClass = computed(() => {
  const val = uploadResult.value?.validacao
  if (!val) return ''
  if (val.erros?.length) return 'status-error'
  if (val.alertas?.length) return 'status-warn'
  return 'status-ok'
})

const uploadStatusIcon = computed(() => {
  const val = uploadResult.value?.validacao
  if (!val) return ''
  if (val.erros?.length) return '✗'
  if (val.alertas?.length) return '⚠'
  return '✓'
})

const uploadStatusLabel = computed(() => {
  const val = uploadResult.value?.validacao
  if (!val) return ''
  if (val.erros?.length) return `Bloqueado — ${val.erros.length} erro(s)`
  const warns = uploadChecks.value.filter(c => c.status !== 'ok').length
  if (warns) return `${warns} alerta(s)`
  return 'Validado'
})

// Limites km/L por grupo (mesmo do backend)
const KML_LIMITES = {
  'Leve':    [5.0, 25.0],
  'Médio':   [5.0, 18.0],
  'Pesado':  [3.0, 14.0],
  '3/4':     [2.5, 10.0],
  'Toco':    [2.0,  7.0],
  'Truck':   [1.5,  6.0],
  'Bitruck': [1.2,  5.0],
}

function fmtKml(km, litros) {
  if (!litros || litros === 0) return '—'
  return (km / litros).toFixed(2)
}
function fmtPrecoL(valor, litros) {
  if (!litros || litros === 0) return '—'
  return 'R$ ' + (valor / litros).toFixed(2)
}
function fmtCustoKm(total, km) {
  if (!km || km === 0) return '—'
  return 'R$ ' + (total / km).toFixed(2)
}

// Ordenação da tabela de veículos
const tabelaSort = ref({ col: 'grupo', dir: 'asc' })

const GRUPO_ORDEM = { 'Bitruck': 1, 'Truck': 2, 'Toco': 3, 'Pesado': 4, 'Médio': 5, '3/4': 6, 'Leve': 7 }

function toggleSort(col) {
  if (tabelaSort.value.col === col) {
    tabelaSort.value.dir = tabelaSort.value.dir === 'asc' ? 'desc' : 'asc'
  } else {
    tabelaSort.value.col = col
    tabelaSort.value.dir = col === 'grupo' ? 'asc' : 'desc'
  }
}

function sortIcon(col) {
  if (tabelaSort.value.col !== col) return '↕'
  return tabelaSort.value.dir === 'asc' ? '↑' : '↓'
}

const veiculosComMetricas = computed(() => {
  const rows = (uploadResult.value?.veiculos || []).map(v => {
    const km    = v.total_km   || 0
    const lit   = v.litros     || 0
    const comb  = v.valor_comb || 0
    const manTotal = (v.manutencao || 0) + (v.rodas_pneus || 0) + (v.lataria_pintura || 0)

    const kmlVal    = lit > 0 ? km / lit   : null
    const precoVal  = lit > 0 ? comb / lit : null
    const custoKmCombVal  = km > 0 ? comb / km    : null
    const custoKmTotalVal = km > 0 ? v.total / km : null

    let kml_class = ''
    if (kmlVal !== null) {
      const lim = KML_LIMITES[v.grupo]
      if (lim && (kmlVal < lim[0] || kmlVal > lim[1])) kml_class = 'cell-warn'
    }

    let preco_class = ''
    if (precoVal !== null && (precoVal < 3.5 || precoVal > 10.0)) preco_class = 'cell-warn'

    return {
      ...v,
      _kml_val:          kmlVal,
      _preco_val:        precoVal,
      _custo_km_comb_val:  custoKmCombVal,
      _custo_km_total_val: custoKmTotalVal,
      _man_total_val:      manTotal,
      kml:            kmlVal  !== null ? kmlVal.toFixed(2)  : '—',
      kml_class,
      preco_l:        precoVal !== null ? 'R$ ' + precoVal.toFixed(2) : '—',
      preco_class,
      custo_km_comb:  custoKmCombVal  !== null ? 'R$ ' + custoKmCombVal.toFixed(2)  : '—',
      custo_km_total: custoKmTotalVal !== null ? 'R$ ' + custoKmTotalVal.toFixed(2) : '—',
    }
  })

  const { col, dir } = tabelaSort.value
  const mult = dir === 'asc' ? 1 : -1

  return [...rows].sort((a, b) => {
    if (col === 'grupo') {
      const ga = GRUPO_ORDEM[a.grupo] ?? 99
      const gb = GRUPO_ORDEM[b.grupo] ?? 99
      if (ga !== gb) return (ga - gb) * mult
      // Dentro do mesmo grupo: custo/km total decrescente
      return ((b._custo_km_total_val ?? 0) - (a._custo_km_total_val ?? 0))
    }
    if (col === 'placa')    return a.placa.localeCompare(b.placa) * mult
    if (col === 'modelo')   return (a.modelo || '').localeCompare(b.modelo || '') * mult
    if (col === 'contrato') return (a.contrato || '').localeCompare(b.contrato || '') * mult
    const numCols = {
      total_km: 'total_km', litros: 'litros',
      kml: '_kml_val', preco_l: '_preco_val',
      valor_comb: 'valor_comb', custo_km_comb: '_custo_km_comb_val',
      manutencao: '_man_total_val', total: 'total', custo_km_total: '_custo_km_total_val',
    }
    const field = numCols[col] || col
    return ((a[field] ?? 0) - (b[field] ?? 0)) * mult
  })
})

// ── Formatadores ──────────────────────────────────────────────────────────
const fmtR = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtN = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
const fmt4 = (v) => v == null ? '—' : 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })

const fmtMes = (ym) => {
  if (!ym) return '—'
  const [ano, mes] = ym.split('-')
  const nomes = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  return `${nomes[parseInt(mes)]}/${ano}`
}

const custoKmClass = (v) => {
  if (v == null) return ''
  if (v > 1.5) return 'text-red'
  if (v > 1.0) return 'text-yellow'
  return 'text-green'
}

const grupoBadgeClass = (g) => {
  if (!g) return ''
  const lower = g.toLowerCase()
  if (['bitruck', 'truck', 'toco', '3/4'].includes(lower)) return 'badge-truck'
  if (lower === 'pesado') return 'badge-heavy'
  if (lower === 'médio' || lower === 'medio') return 'badge-medium'
  return 'badge-light'
}

// ── Reconciliação ─────────────────────────────────────────────────────────
const veiculosComAlerta = computed(() =>
  (reconciliacao.value.veiculos ?? []).filter(v => v.tem_alerta)
)

const FLAG_LABELS = {
  gap_negativo:   'Gap negativo',
  preco_suspeito: 'Preço/L suspeito',
  kml_divergente: 'km/L divergente',
  sem_truckpag:   'Sem TruckPag',
}
function flagLabel(f) { return FLAG_LABELS[f] ?? f }

// ── Gráfico Donut ─────────────────────────────────────────────────────────
const donutSeries  = computed(() => categorias.value.map(c => c.valor))
const donutOptions = computed(() => ({
  chart: { type: 'donut', background: 'transparent', fontFamily: 'Inter' },
  labels: categorias.value.map(c => c.categoria),
  colors: ['#C41230', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
  legend: { position: 'bottom', fontSize: '12px', labels: { colors: '#475569' } },
  dataLabels: { enabled: true, formatter: (val) => val.toFixed(1) + '%', style: { fontSize: '11px' } },
  plotOptions: { pie: { donut: { size: '60%', labels: { show: true, total: { show: true, label: 'Total', formatter: () => fmtR(kpis.value.total_geral) } } } } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

// ── Gráfico Linha ──────────────────────────────────────────────────────────
const lineSeries = computed(() => [
  { name: 'Total Geral', data: evolucao.value.map(e => e.total_geral) },
  { name: 'Combustível', data: evolucao.value.map(e => e.total_combustivel) },
  { name: 'Manutenção', data: evolucao.value.map(e => e.total_manutencao) },
])
const lineOptions = computed(() => ({
  chart: { type: 'line', background: 'transparent', fontFamily: 'Inter', toolbar: { show: false } },
  colors: ['#C41230', '#3b82f6', '#10b981'],
  stroke: { curve: 'smooth', width: [2.5, 2, 2] },
  xaxis: { categories: evolucao.value.map(e => fmtMes(e.ano_mes)), labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
  yaxis: { labels: { formatter: (v) => 'R$ ' + (v / 1000).toFixed(0) + 'k', style: { colors: '#94a3b8', fontSize: '11px' } } },
  grid: { borderColor: '#e2e8f0' },
  legend: { position: 'top', fontSize: '12px', labels: { colors: '#475569' } },
  tooltip: { y: { formatter: (v) => fmtR(v) } },
}))

// ── Carga de dados ────────────────────────────────────────────────────────
const params = () => {
  const p = {}
  if (filtroMes.value)    p.ano_mes = filtroMes.value
  if (filtroFilial.value) p.filial  = filtroFilial.value
  if (filtroGrupo.value)  p.grupo   = filtroGrupo.value
  if (filtroContrato.value) p.contrato = filtroContrato.value
  return p
}

const loadAll = async () => {
  const p = params()
  lKpis.value = lCategorias.value = lFilial.value = lVeiculos.value = lContratos.value = lReconciliacao.value = true
  showAlertas.value = false

  // Reconciliação: passa só ano_mes, filial e contrato (sem grupo — TruckPag não tem esse filtro)
  const pRecon = {}
  if (filtroMes.value)     pRecon.ano_mes  = filtroMes.value
  if (filtroFilial.value)  pRecon.filial   = filtroFilial.value
  if (filtroContrato.value) pRecon.contrato = filtroContrato.value

  Promise.all([
    fetchFkmKpis(p).then(d => { kpis.value = d; lKpis.value = false }).catch(() => lKpis.value = false),
    fetchFkmDistribuicaoCategorias(p).then(d => { categorias.value = d; lCategorias.value = false }).catch(() => lCategorias.value = false),
    fetchFkmResumoPorFilial(p).then(d => { porFilial.value = d; lFilial.value = false }).catch(() => lFilial.value = false),
    fetchFkmCustoPorVeiculo({ ...p, limit: 50 }).then(d => { veiculos.value = d; lVeiculos.value = false }).catch(() => lVeiculos.value = false),
    fetchContratosKpis({ ano_mes: p.ano_mes, contrato: p.contrato }).then(d => { porContrato.value = d; lContratos.value = false }).catch(() => lContratos.value = false),
    fetchFkmReconciliacao(pRecon).then(d => { reconciliacao.value = d; lReconciliacao.value = false }).catch(() => lReconciliacao.value = false),
  ])
}

const loadEvolucao = async () => {
  lEvolucao.value = true
  const p = {}
  if (filtroFilial.value) p.filial = filtroFilial.value
  if (filtroGrupo.value)  p.grupo  = filtroGrupo.value
  fetchFkmEvolucaoMensal(p)
    .then(d => { evolucao.value = d; lEvolucao.value = false })
    .catch(() => lEvolucao.value = false)
}

const refreshCache = async () => {
  refreshing.value = true
  try {
    await fetch(`${import.meta.env.VITE_API_URL}/api/fkm/cache/refresh`, { method: 'POST' })
    await init()
  } finally {
    refreshing.value = false
  }
}

const init = async () => {
  const f = await fetchFkmFiltros()
  filtros.value = f
  if (f.meses.length && !filtroMes.value) filtroMes.value = f.meses[0]
  await Promise.all([loadAll(), loadEvolucao()])
}

onMounted(init)
</script>

<style scoped>
.page { min-height: 100vh; background: #f8fafc; }


/* ── Page body ── */
.page-body {
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1600px;
}

/* ── KPI grid ── */
.kpi-pro-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

/* ── Sub KPIs de categoria ── */
.cat-kpis {
  display: flex; gap: 0; border-top: none; padding-top: 16px;
  flex-wrap: wrap; position: relative;
}
.cat-kpis::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(to right, transparent, rgba(0,0,0,0.10) 20%, rgba(0,0,0,0.10) 80%, transparent); }
.cat-kpi {
  flex: 1; min-width: 120px;
  display: flex; flex-direction: column; gap: 3px;
  padding: 0 20px 0 0;
  border-right: 1px solid rgba(0,0,0,0.04);
}
.cat-kpi:last-child { border-right: none; }
.cat-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.cat-value { font-size: 14px; font-weight: 700; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
.cat-pct { font-size: 11px; font-weight: 600; color: #C41230; }

/* ── Two col ── */
.two-col { display: grid; grid-template-columns: 1fr 1.6fr; gap: 20px; }

/* ── Section heading ── */
.section-heading {
  font-size: 12px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 16px;
}
.section-heading-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-heading-row .section-heading { margin-bottom: 0; }
.section-badge {
  background: #f1f5f9; border-radius: 6px; padding: 2px 8px;
  font-size: 11px; font-weight: 700; color: #64748b;
}

/* ── Table ── */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.data-table th {
  background: #f8fafc; border-bottom: 1px solid rgba(0,0,0,0.07); padding: 8px 12px;
  font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;
  white-space: nowrap;
}
.data-table td { padding: 9px 12px; border-bottom: 1px solid rgba(0,0,0,0.04); color: #1e293b; white-space: nowrap; }
.data-table tbody tr:hover { background: #fafafa; }
.data-table tfoot tr { background: #f8fafc; }
.data-table tfoot td { padding: 10px 12px; font-weight: 700; font-size: 12px; border-top: 2px solid #e2e8f0; }
.right { text-align: right; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; }
.fw-bold { font-weight: 700; }

.idx-cell { color: #94a3b8; font-size: 11px; width: 32px; }
.placa-cell { font-weight: 700; color: #0f172a; letter-spacing: 0.05em; }
.filial-cell { color: #475569; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }

.text-red { color: #dc2626; font-weight: 700; }
.text-yellow { color: #d97706; font-weight: 600; }
.text-green { color: #059669; }

/* Grupo badges */
.grupo-badge { display: inline-block; padding: 2px 7px; border-radius: 5px; font-size: 10px; font-weight: 700; }
.badge-truck   { background: #fef3c7; color: #92400e; }
.badge-heavy   { background: #fee2e2; color: #991b1b; }
.badge-medium  { background: #dbeafe; color: #1e40af; }
.badge-light   { background: #d1fae5; color: #065f46; }

/* ── Reconciliação ── */
.recon-chips {
  display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px;
}
.recon-chip {
  flex: 1; min-width: 160px;
  background: #f8fafc;
  border: 1px solid rgba(0,0,0,0.07);
  border-radius: 12px; padding: 14px 18px;
  display: flex; flex-direction: column; gap: 4px;
}
.recon-chip-tp   { border-top: 3px solid #2563eb; }
.recon-chip-direto { border-top: 3px solid #f59e0b; }
.recon-chip-label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.recon-chip-val   { font-size: 18px; font-weight: 800; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
.recon-chip-pct   { font-size: 12px; font-weight: 700; color: #64748b; }

.pct-bar-wrap { display: flex; align-items: center; gap: 8px; }
.pct-bar-track { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 60px; }
.pct-bar-fill  { height: 100%; background: #2563eb; border-radius: 3px; transition: width 0.4s ease; }

.btn-toggle {
  background: none; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 6px 14px; font-size: 12px; font-weight: 600; color: #64748b;
  cursor: pointer; margin-top: 12px; transition: all 0.15s;
}
.btn-toggle:hover { background: #f8fafc; border-color: #cbd5e1; }

.flag-badge {
  display: inline-block; padding: 2px 7px; border-radius: 5px;
  font-size: 10px; font-weight: 700; margin-right: 4px; white-space: nowrap;
}
.flag-gap_negativo   { background: #fef2f2; color: #dc2626; }
.flag-preco_suspeito { background: #fff7ed; color: #ea580c; }
.flag-kml_divergente { background: #fffbeb; color: #d97706; }
.flag-sem_truckpag   { background: #eff6ff; color: #2563eb; }

.badge-warn { background: #fff7ed; color: #ea580c; border: 1px solid rgba(234,88,12,0.2); }

/* ── Utilitários ── */
.empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 40px 0; }
.skel { background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }
.kpi-skel { height: 120px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

@media (max-width: 1200px) {
  .two-col { grid-template-columns: 1fr; }
  .kpi-pro-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .page-body { padding: 16px; }
  .kpi-pro-grid { grid-template-columns: 1fr; }
}

/* ── Upload Modal ── */
.btn-upload { background: #f97316 !important; color: #fff !important; font-weight: 600; }
.btn-upload:hover { background: #ea580c !important; }

.upload-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  overflow-y: auto; z-index: 9999;
  display: flex; align-items: flex-start; justify-content: center;
  padding: 32px 16px;
}
.upload-modal {
  background: #fff; border-radius: 14px; width: 100%; max-width: 1200px;
  display: flex; flex-direction: column;
  box-shadow: 0 32px 80px rgba(0,0,0,.28);
  margin: auto;
}
.upload-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0;
  background: #fff;
}
.upload-header h2 { margin: 0; font-size: .97rem; color: #111827; font-weight: 700; }
.upload-close {
  background: none; border: none; font-size: 1.3rem; cursor: pointer;
  color: #9ca3af; width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; transition: all .12s;
}
.upload-close:hover { background: #f3f4f6; color: #374151; }
.upload-body {
  padding: 16px 20px;
  display: flex; flex-direction: column; gap: 10px;
}
.upload-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 12px 20px; border-top: 1px solid #e5e7eb;
  background: #f9fafb; flex-shrink: 0;
}

/* Arquivo — seleção */
.upload-hint { color: #6b7280; margin: 0 0 6px; font-size: 0.88rem; }
.upload-hint code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: .83rem; }
.upload-drop { margin: 12px 0; }
.upload-drop input[type="file"] { font-size: 0.9rem; }

/* Cabeçalho compacto */
.upload-cabecalho {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: #f8fafc; border-radius: 10px;
  border: 1px solid #e5e7eb; flex-shrink: 0;
}
.cab-info { display: flex; align-items: center; gap: 8px; font-size: .875rem; color: #374151; flex-wrap: wrap; }
.cab-filial { font-weight: 700; color: #111827; font-size: .9rem; }
.cab-sigla  { font-weight: 400; color: #6b7280; }
.cab-sep    { color: #d1d5db; user-select: none; }
.cab-badge  { font-size: .76rem; font-weight: 700; padding: 4px 11px; border-radius: 20px; white-space: nowrap; flex-shrink: 0; }
.cab-badge.status-ok    { background: #dcfce7; color: #166534; }
.cab-badge.status-warn  { background: #fef3c7; color: #92400e; }
.cab-badge.status-error { background: #fee2e2; color: #991b1b; }

/* Alertas */
.upload-msgs { display: flex; flex-direction: column; gap: 6px; }
.msg-pill {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 14px; border-radius: 8px; font-size: .82rem; border-left: 4px solid;
}
.msg-pill.warn  { background: #fffbeb; border-color: #f59e0b; color: #78350f; }
.msg-pill.error { background: #fef2f2; border-color: #ef4444; color: #7f1d1d; }
.pill-icon { font-size: .9rem; margin-top: 1px; flex-shrink: 0; }

/* KPIs */
.upload-kpis { display: flex; gap: 6px; flex-wrap: wrap; }
.kpi-box {
  display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 90px;
  padding: 9px 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e5e7eb;
}
.kpi-box.kpi-total { background: #f0fdf4; border-color: #86efac; }
.kpi-val { font-size: .9rem; font-weight: 700; color: #111827; font-family: 'JetBrains Mono', monospace; }
.kpi-total .kpi-val { color: #16a34a; }
.kpi-lbl { font-size: .7rem; color: #6b7280; white-space: nowrap; margin-top: 1px; }

/* Título da tabela */
.upload-table-title {
  font-size: .73rem; font-weight: 700; text-transform: uppercase; letter-spacing: .6px;
  color: #6b7280; display: flex; align-items: center; gap: 8px;
}
.badge-ok   { background: #dcfce7; color: #166534; font-size: .72rem; padding: 1px 7px; border-radius: 10px; font-weight: 700; }
.badge-warn { background: #fef3c7; color: #92400e; font-size: .72rem; padding: 1px 7px; border-radius: 10px; font-weight: 700; }

/* Tabela principal */
.upload-table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 8px; }
.mini-table { width: 100%; border-collapse: collapse; font-size: .78rem; }
.mini-table th {
  text-align: left; padding: 7px 10px; border-bottom: 2px solid #e5e7eb;
  font-weight: 600; color: #374151; white-space: nowrap; background: #f9fafb;
  position: sticky; top: 0; z-index: 1;
}
.mini-table th .th-sub { font-weight: 400; color: #9ca3af; font-size: .7rem; }
.mini-table th.sortable { cursor: pointer; user-select: none; }
.mini-table th.sortable:hover { background: #f0f4f8; }
.sort-icon { color: #9ca3af; font-size: .7rem; margin-left: 2px; }
.mini-table td { padding: 5px 10px; border-bottom: 1px solid #f3f4f6; color: #374151; }
.mini-table tbody tr:hover td { background: #f9fafb; }
.mini-table .right { text-align: right; }
.mini-table .mono  { font-family: 'JetBrains Mono', monospace; }
.mini-table .td-contrato { max-width: 130px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mini-table .td-modelo   { max-width: 110px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #6b7280; font-size: .76rem; }

/* Tfoot */
.tfoot-row td { border-top: 2px solid #d1d5db; background: #f3f4f6 !important; padding: 6px 10px; }

/* Células com destaque */
.cell-warn { color: #d97706 !important; font-weight: 700; }
.cell-zero { color: #9ca3af !important; }
.row-zero td { color: #9ca3af; }
.warn-text { color: #d97706 !important; font-weight: 600; }

/* Placas faltando */
.upload-faltando {
  border: 1px solid #fde68a; border-radius: 8px; overflow: hidden;
}
.upload-faltando .upload-table-title {
  padding: 8px 12px; background: #fffbeb; margin: 0; border-bottom: 1px solid #fde68a;
}
.upload-faltando .mini-table { font-size: .77rem; }
.upload-faltando .mini-table th { background: #fffbeb; }
.upload-faltando .mini-table td { padding: 5px 12px; }

/* ── Pill body + ações de resolução ── */
.pill-body { display: flex; flex-direction: column; gap: 6px; flex: 1; }

.pill-acoes { display: flex; flex-direction: column; gap: 5px; margin-top: 4px; }
.pill-acoes-divman { gap: 0; }
.divman-table { margin-top: 4px; width: 100%; }
.divman-hint {
  margin: 6px 0 0; padding: 6px 10px;
  font-size: .76rem; color: #b45309;
  background: rgba(251,191,36,.08); border-radius: 4px;
  border-left: 2px solid #f59e0b;
}

.placa-acao {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  padding: 4px 8px; background: rgba(255,255,255,0.6); border-radius: 5px;
  border: 1px solid rgba(0,0,0,0.06);
  font-size: .79rem;
}

.pa-modelo {
  color: #9ca3af; font-size: .75rem; flex-shrink: 0;
}

.btn-acao {
  padding: 3px 10px; border-radius: 5px;
  border: 1px solid #d1d5db; background: #fff;
  color: #374151; font-size: .76rem; font-weight: 600;
  cursor: pointer; transition: all .12s;
  white-space: nowrap;
}
.btn-acao:hover { background: #f3f4f6; border-color: #9ca3af; }

.pa-filial-sistema, .pa-grupo {
  font-size: .75rem; color: #6b7280; flex-shrink: 0;
  background: #f3f4f6; padding: 2px 7px; border-radius: 4px;
}
.pa-filial-sistema strong { color: #374151; }

.btn-acao-manter  { border-color: #86efac; color: #166534; }
.btn-acao-manter:hover { background: #f0fdf4; border-color: #4ade80; }
.btn-acao-remover { border-color: #fca5a5; color: #991b1b; }
.btn-acao-remover:hover { background: #fef2f2; border-color: #f87171; }

.acao-resolvida {
  color: #16a34a; font-weight: 700; font-size: .78rem; flex-shrink: 0;
}
.acao-removida {
  color: #dc2626 !important;
}

.acao-obs {
  flex: 1; min-width: 140px; padding: 3px 8px;
  border: 1px solid #d1d5db; border-radius: 5px;
  font-size: .76rem; color: #374151; background: #fff;
  outline: none;
}
.acao-obs:focus { border-color: #f97316; }

.btn-acao-desfazer {
  padding: 2px 8px; border-radius: 5px;
  border: 1px solid #e5e7eb; background: transparent;
  color: #9ca3af; font-size: .72rem;
  cursor: pointer; transition: all .12s;
}
.btn-acao-desfazer:hover { color: #ef4444; border-color: #fca5a5; background: #fef2f2; }

/* Erro */
.upload-error { color: #dc2626; font-weight: 500; font-size: .88rem; }

/* ── Rateio Matriz ── */
.btn-matriz {
  background: #7c3aed !important; color: #fff !important; font-weight: 600;
}
.btn-matriz:hover { background: #6d28d9 !important; }

.matriz-subtitle {
  margin: 2px 0 0; font-size: .76rem; color: #9ca3af; font-weight: 400;
}

.matriz-kpis { display: flex; gap: 6px; flex-wrap: wrap; }
.kpi-box.kpi-warn { background: #fff7ed; border-color: #fed7aa; }
.kpi-box.kpi-warn .kpi-val { color: #c2410c; }

.select-filial {
  font-size: .78rem; padding: 4px 8px; border: 1px solid #d1d5db;
  border-radius: 6px; color: #374151; background: #fff;
  width: 100%; min-width: 180px; cursor: pointer;
  outline: none; transition: border-color .12s;
}
.select-filial:focus { border-color: #7c3aed; }
.select-filial.select-ok { border-color: #86efac; background: #f0fdf4; color: #15803d; }

.row-pendente td { background: #fffbeb; }
.row-alocada td  { background: #f0fdf4; }

.footer-info {
  flex: 1; font-size: .8rem; color: #6b7280; align-self: center;
}

/* ── Resultado / Relatório pós-gravação ── */
.resultado-header {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 16px; background: #f0fdf4; border-radius: 10px;
  border: 1px solid #86efac;
}
.resultado-icon {
  width: 36px; height: 36px; background: #16a34a; color: #fff;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; font-weight: 700; flex-shrink: 0;
}
.resultado-titulo { font-size: .95rem; font-weight: 700; color: #15803d; }
.resultado-sub    { font-size: .8rem; color: #4ade80; margin-top: 2px; color: #166534; }

.resultado-table { margin-top: 0; }
.resultado-obs { color: #6b7280; font-style: italic; font-size: .75rem; }

.resultado-badge {
  display: inline-block; padding: 2px 9px; border-radius: 5px;
  font-size: .75rem; font-weight: 600; white-space: nowrap;
  background: #f1f5f9; color: #475569;
}
.resultado-badge.rb-ausente  { background: #eff6ff; color: #1d4ed8; }
.resultado-badge.rb-baixado  { background: #fef3c7; color: #92400e; }
.resultado-badge.rb-filial   { background: #fdf4ff; color: #7e22ce; }
.resultado-badge.rb-transfer { background: #fff7ed; color: #c2410c; }
.resultado-badge.rb-sem      { background: #f0fdf4; color: #15803d; }

.pendencias-wrap {
  border: 1px solid #fde68a; border-radius: 8px; overflow: hidden;
}
.pendencias-title {
  padding: 8px 12px; background: #fffbeb; margin: 0;
  border-bottom: 1px solid #fde68a;
}
.pendencias-hint {
  margin: 8px 12px; font-size: .78rem; color: #78350f;
}
.pendencias-wrap .mini-table th { background: #fffbeb; }
.pendencias-wrap .mini-table td { padding: 5px 12px; }

/* Botões footer */
.btn-cancel {
  padding: 7px 18px; border: 1px solid #d1d5db; border-radius: 7px;
  background: #fff; cursor: pointer; color: #374151; font-size: .87rem; font-weight: 500;
  transition: all .12s;
}
.btn-cancel:hover { background: #f3f4f6; border-color: #9ca3af; }
.btn-confirm {
  padding: 7px 22px; border: none; border-radius: 7px;
  background: #16a34a; color: #fff; font-weight: 700; cursor: pointer; font-size: .87rem;
  transition: background .12s;
}
.btn-confirm:hover { background: #15803d; }
.btn-confirm:disabled { background: #9ca3af; cursor: not-allowed; }
</style>
