<template>
  <div class="gp-page">
    <header class="gp-header">
      <h1>Gestão de Pneus</h1>
      <div class="gp-kpis" v-if="dash">
        <div class="kpi-card"><span class="kpi-val">{{ dash.total_pneus }}</span><span class="kpi-lbl">Total Pneus</span></div>
        <div class="kpi-card kpi-green"><span class="kpi-val">{{ dash.em_estoque }}</span><span class="kpi-lbl">Em Estoque</span></div>
        <div class="kpi-card kpi-blue"><span class="kpi-val">{{ dash.em_uso }}</span><span class="kpi-lbl">Em Uso</span></div>
        <div class="kpi-card kpi-red"><span class="kpi-val">{{ dash.descartados }}</span><span class="kpi-lbl">Descartados</span></div>
        <div class="kpi-card kpi-yellow"><span class="kpi-val">R$ {{ fmtN(dash.valor_estoque) }}</span><span class="kpi-lbl">Valor Estoque</span></div>
      </div>
    </header>



    <!-- TABS -->
    <nav class="gp-tabs">
      <button v-for="t in tabs" :key="t.id" class="gp-tab" :class="{ active: tab === t.id }" @click="tab = t.id">
        {{ t.label }}
      </button>
    </nav>

    <!-- TAB: ALOCAÇÕES (NOVA) -->
    <section v-if="tab === 'alocacoes'" class="gp-section alocacao-layout">
      <!-- SIDEBAR BUSCA -->
      <div class="aloc-sidebar">
        <div class="search-box">
          <label>Buscar Veículo</label>
          <input v-model="searchVeiculo" placeholder="Placa ou Frota..." class="stock-input" />
        </div>
        
        <div class="aloc-veiculo-list">
          <div v-for="v in filteredVeiculos" :key="v.id" 
               class="aloc-v-card" :class="{ active: veiculoDetail?.id === v.id }"
               @click="openVeiculoDetail(v)">
            <div class="v-card-icon">🚛</div>
            <div class="v-card-info">
              <span class="v-placa">{{ v.placa }}</span>
              <span class="v-modelo">{{ v.modelo }}</span>
            </div>
            <div class="v-card-status">
               <span class="badge" :class="v.pneus_alocados === v.total_posicoes ? 'badge-green' : 'badge-yellow'">
                 {{ v.pneus_alocados }}/{{ v.total_posicoes }}
               </span>
            </div>
          </div>
          <div v-if="!filteredVeiculos.length" class="empty-mini">Nenhum veículo encontrado</div>
        </div>
      </div>

      <!-- ÁREA DE TRABALHO -->
      <div class="aloc-workbench">
        <div v-if="veiculoDetail" class="workbench-content">
          <header class="workbench-header">
            <div class="wb-info">
              <h2>{{ veiculoDetail.placa }}</h2>
              <span class="badge badge-purple">{{ veiculoDetail.km_atual.toLocaleString('pt-BR') }} KM</span>
              <span class="vd-config-badge">{{ configLabel(veiculoDetail.tipo) }}</span>
            </div>
            <div class="wb-actions">
               <button class="btn-sm" @click="openVeiculoForm(veiculoDetail)">Editar Cadastro</button>
            </div>
          </header>

          <div class="gp-move-container workbench-inner">
             <!-- DIAGRAMA -->
             <div class="gp-vehicle-canvas">
                <div class="vehicle-diagram-area">
                  <div class="chassis-box">
                    <div class="placa-box">
                      <div class="placa-br">BRASIL</div>
                      <div class="placa-num">{{ veiculoDetail.placa }}</div>
                    </div>
                    <div class="chassis-vertical-line"></div>
                  </div>

                  <div class="axles-container">
                    <div v-for="eixo in veiculoDetail.config?.eixos" :key="eixo.num" class="axle-row">
                      <div class="axle-visual">
                        <div class="wheels-side side-esq">
                          <div v-for="pos in eixo.posicoes.filter(p => p.includes('ESQ'))" :key="pos" 
                               class="tire-drop-zone"
                               :class="{ occupied: veiculoDetail.pneus[pos], 'drag-over': dragOverPos === pos }"
                               @dragover.prevent="dragOverPos = pos"
                               @dragleave="dragOverPos = null"
                               @drop="handleDropOnSlot(pos)"
                               @click="handleTireClick(pos)">
                            <div v-if="veiculoDetail.pneus[pos]" class="tire-item in-vehicle" 
                                 draggable="true" @dragstart="handleDragStartFromVehicle($event, pos, veiculoDetail.pneus[pos])">
                              <div class="tire-id">{{ veiculoDetail.pneus[pos].numero_fogo }}</div>
                            </div>
                            <div v-else class="tire-placeholder"><span>+</span></div>
                          </div>
                        </div>
                        <div class="axle-bar"></div>
                        <div :class="['center-shape', eixo.num === 1 ? 'shape-diamond' : 'shape-circle']"></div>
                        <div class="wheels-side side-dir">
                          <div v-for="pos in eixo.posicoes.filter(p => p.includes('DIR'))" :key="pos" 
                               class="tire-drop-zone"
                               :class="{ occupied: veiculoDetail.pneus[pos], 'drag-over': dragOverPos === pos }"
                               @dragover.prevent="dragOverPos = pos"
                               @dragleave="dragOverPos = null"
                               @drop="handleDropOnSlot(pos)"
                               @click="handleTireClick(pos)">
                            <div v-if="veiculoDetail.pneus[pos]" class="tire-item in-vehicle"
                                 draggable="true" @dragstart="handleDragStartFromVehicle($event, pos, veiculoDetail.pneus[pos])">
                              <div class="tire-id">{{ veiculoDetail.pneus[pos].numero_fogo }}</div>
                            </div>
                            <div v-else class="tire-placeholder"><span>+</span></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="spare-container" v-if="veiculoDetail.config?.estepes?.length">
                    <div class="spare-title">Estepes</div>
                    <div v-for="pos in veiculoDetail.config.estepes" :key="pos" 
                         class="tire-drop-zone spare-zone"
                         :class="{ occupied: veiculoDetail.pneus[pos], 'drag-over': dragOverPos === pos }"
                         @dragover.prevent="dragOverPos = pos"
                         @dragleave="dragOverPos = null"
                         @drop="handleDropOnSlot(pos)"
                         @click="handleTireClick(pos)">
                      <div v-if="veiculoDetail.pneus[pos]" class="tire-item in-vehicle"
                           draggable="true" @dragstart="handleDragStartFromVehicle($event, pos, veiculoDetail.pneus[pos])">
                        <div class="tire-id">{{ veiculoDetail.pneus[pos].numero_fogo }}</div>
                      </div>
                      <div v-else class="tire-placeholder"><span>+</span></div>
                    </div>
                  </div>
                </div>
             </div>

             <!-- ALMOXARIFADO (LADO) -->
             <div class="gp-stock-panel">
                <div class="stock-header">
                  <h4>Almoxarifado 📦</h4>
                  <span class="stock-count">{{ pneusEstoqueFilial.length }}</span>
                </div>
                <div class="stock-filters" style="padding: 0 15px 10px;">
                  <select v-model="almoxarifadoFilialId" class="filter-select" style="width:100%; min-width:0; padding: 6px;" @change="loadEstoqueAlmoxarifado">
                    <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
                  </select>
                </div>
                <div class="search-stock">
                  <input v-model="searchStock" placeholder="Buscar pneu no estoque..." class="stock-input" style="padding: 6px;" />
                </div>
                <div class="stock-list" @dragover.prevent @drop="handleDropOnRemoval('estoque')">
                  <div v-for="p in filteredStock" :key="p.id" 
                       class="tire-card-stock" 
                       :class="{ 'tire-pending': p.recebido === 0, 'tire-new': (Number(p.vida) == 1 || String(p.vida).startsWith('1')) && p.recebido === 1 }"
                       draggable="true" @dragstart="handleDragStartFromStock($event, p)">
                    <div class="tire-mini-visual"></div>
                    <div class="tire-card-info">
                      <span class="t-fogo">{{ p.numero_fogo }}</span>
                      <span class="t-desc">{{ p.marca }} {{ p.medida }}</span>
                      <span class="t-status">Vida: {{ p.vida }}ª | {{ p.sulco_atual }}mm</span>
                    </div>
                  </div>
                  <div v-if="!filteredStock.length" class="empty-stock">Sem pneus</div>
                </div>
                <div class="removal-zone sucata-drop" :class="{ 'drag-over': dragOverRemoval }" 
                     @dragover.prevent="dragOverRemoval = true" @dragleave="dragOverRemoval = false" 
                     @drop="handleDropOnRemoval('sucata')">
                  <span class="icon">🗑️</span>
                  <span class="label">ARRASTE PARA SUCATA</span>
                </div>
             </div>
          </div>
        </div>
        <div v-else class="empty-state" style="border:none; background:transparent;">
          <div class="select-v-prompt">
            <span class="prompt-icon">🚛</span>
            <h3>Selecione um veículo para iniciar</h3>
            <p>Utilize a barra de pesquisa à esquerda para selecionar uma placa.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB: FILIAIS -->
    <section v-if="tab === 'filiais'" class="gp-section">
      <div class="sec-toolbar">
        <h2>Filiais</h2>
        <button class="btn-primary" @click="openFilialForm()">+ Nova Filial</button>
      </div>
      <table class="gp-table" v-if="filiais.length">
        <thead><tr><th>Nome</th><th>UF</th><th>Ações</th></tr></thead>
        <tbody>
          <tr v-for="f in filiais" :key="f.id">
            <td><strong>{{ f.nome }}</strong></td>
            <td>{{ f.estado }}</td>
            <td class="td-actions">
              <button class="btn-sm" @click="openFilialForm(f)">Editar</button>
              <button class="btn-sm btn-danger" @click="removeFilial(f)">Excluir</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">Nenhuma filial cadastrada</div>
    </section>

    <!-- TAB: VEÍCULOS -->
    <section v-if="tab === 'veiculos'" class="gp-section">
      <div class="sec-toolbar">
        <h2>Veículos</h2>
        <select v-model="filtroFilialV" @change="loadVeiculos" class="filter-select">
          <option value="">Todas as filiais</option>
          <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
        </select>
        <button class="btn-primary" @click="openVeiculoForm()">+ Novo Veículo</button>
      </div>
      <div class="table-responsive" v-if="veiculos.length">
        <table class="gp-table">
          <thead><tr><th>Placa</th><th>Frota</th><th>Modelo</th><th>Tipo</th><th>Filial</th><th>Pneus</th><th>Odômetro</th><th>Ações</th></tr></thead>
        <tbody>
           <tr v-for="v in veiculos" :key="v.id">
            <td>
              <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 17h4V5H2v12h3"/><path d="M20 17h2v-9h-4V5h-4v12h3"/><path d="M10 9h4"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>
                <strong>{{ v.placa }}</strong>
              </div>
            </td>
            <td>{{ v.frota }}</td>
            <td>{{ v.modelo }}</td>
            <td>
              <select class="inline-select" v-model="v.tipo" @change="saveVeiculoInline(v)">
                <option v-for="(cfg, key) in vehicleConfigs" :key="key" :value="key">{{ cfg.nome }}</option>
              </select>
            </td>
            <td>
              <select class="inline-select" v-model="v.filial_id" @change="saveVeiculoInline(v)">
                <option :value="null">— Sem Filial —</option>
                <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
              </select>
            </td>
            <td><span class="badge" :class="v.pneus_alocados === v.total_posicoes ? 'badge-green' : 'badge-yellow'">{{ v.pneus_alocados }}/{{ v.total_posicoes }}</span></td>
            <td>
              <span v-if="v.km_atual" class="badge badge-purple" style="font-weight: 800">{{ (v.km_atual || 0).toLocaleString('pt-BR') }} <span style="font-size: 9px; opacity: 0.8">KM</span></span>
              <span v-else style="color: var(--text3); font-size: 11px;">Sem dados</span>
            </td>
            <td class="td-actions">
              <button class="btn-sm" @click="openVeiculoForm(v)">Editar</button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <div v-else class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 16px;"><path d="M10 17h4V5H2v12h3"/><path d="M20 17h2v-9h-4V5h-4v12h3"/><path d="M10 9h4"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>
        <p>Nenhum veículo cadastrado na base de dados.</p>
        <p style="font-size: 11px; color: var(--text3); margin-top: 4px;">Utilize a Sincronização SQL Server ou cadastre manualmente.</p>
      </div>
    </section>

    <!-- TAB: ESTOQUE -->
    <section v-if="tab === 'estoque'" class="gp-section">
      <div class="sec-toolbar">
        <h2>Gerenciar Pneus</h2>
        <div style="display: flex; gap: 12px; margin-left: auto;">
          <select v-model="filtroFilialP" @change="loadPneus" class="filter-select">
            <option value="">Todas as filiais</option>
            <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
          </select>
          <select v-model="filtroStatus" @change="loadPneus" class="filter-select">
            <option value="">Todos os status</option>
            <option value="estoque">Em Estoque</option>
            <option value="em_uso">Em Uso</option>
            <option value="descarte">Descartados</option>
            <option value="recapagem">Em Recapagem</option>
          </select>
          <button class="btn-primary" @click="openPneuForm()" style="box-shadow: 0 4px 12px rgba(196,18,48,0.25);">+ Registrar Pneu</button>
        </div>
      </div>
      <div class="table-responsive" v-if="pneusList.length">
        <table class="gp-table">
          <thead><tr><th>N.Fogo</th><th>Marca</th><th>Modelo</th><th>Medida</th><th>Vida</th><th>Fornecedor</th><th>NF</th><th>Valor Unit.</th><th>Performance</th><th>Status</th><th>Filial</th><th>Veículo</th><th>Ações</th></tr></thead>
        <tbody>
          <tr v-for="p in pneusList" :key="p.id" :class="{'row-disabled': p.status === 'descarte'}">
            <td>
              <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M5 5l1.5 1.5"/><path d="M17.5 17.5L19 19"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="M5 19l1.5-1.5"/><path d="M17.5 6.5L19 5"/></svg>
                <strong>{{ p.numero_fogo }}</strong>
              </div>
            </td>
            <td>{{ p.marca }}</td>
            <td>{{ p.modelo }}</td>
            <td>{{ p.medida }}</td>
            <td><span class="vida-badge">{{ p.vida }}ª</span></td>
            <td>{{ p.fornecedor || '—' }}</td>
            <td>{{ p.nf || '—' }}</td>
            <td><strong>R$ {{ fmtN(p.valor) }}</strong></td>
            <td>
              <div style="display:flex; flex-direction:column; gap:4px; font-size:11px;">
                <span v-if="p.km_total" class="badge badge-blue">{{ (p.km_total || 0).toLocaleString('pt-BR') }} km</span>
                <span v-if="p.cpk" class="badge badge-purple">CPK: R$ {{ p.cpk.toFixed(4) }}</span>
                <span v-if="!p.km_total && !p.cpk" style="color:var(--text3)">0 km rodados</span>
              </div>
            </td>
            <td>
              <span class="badge" :class="statusClass(p.status)">{{ statusLabel(p.status) }}</span>
              <span v-if="p.recebido === 0" class="badge badge-yellow" style="margin-top: 4px; display: block; font-size: 9px;">EM TRÂNSITO</span>
            </td>
            <td>{{ p.filial_nome || '—' }}</td>
            <td>{{ p.veiculo_placa || '—' }}</td>
            <td class="td-actions">
              <button v-if="p.recebido === 0" class="btn-sm btn-accent" @click="doConfirmarRecebimento(p)">Confirmar Chegada</button>
              <button v-if="p.status === 'estoque' && p.recebido === 1" class="btn-sm" @click="openTransferirModal(p)">Transferir</button>
              <button class="btn-sm" @click="openPneuForm(p)">Editar</button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
      <div v-else class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 16px;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M5 5l1.5 1.5"/></svg>
        <p>Nenhum pneu atende aos filtros atuais.</p>
        <p style="font-size: 11px; color: var(--text3); margin-top: 4px;">Clique em "Registrar Pneu" para iniciar o inventário.</p>
      </div>
    </section>

    <!-- TAB: SUCATA -->
    <section v-if="tab === 'sucata'" class="gp-section">
      <div class="sec-toolbar" style="gap: 12px;">
        <div class="toolbar-left">
          <h2>Gestão de Sucata</h2>
          <p class="sec-subtitle">Validação e controle de pneus descartados ou em fim de vida</p>
        </div>
        <div class="toolbar-right" style="display:flex; gap: 12px; align-items: center;">
          <div class="filter-box">
             <input v-model="searchSucata" placeholder="🔍 Buscar Nº Fogo..." class="filter-select select-premium" style="width: 200px; padding-left: 14px;" />
          </div>
          <div class="filter-box">
             <select v-model="filtroFilialSucata" class="filter-select" style="min-width: 220px;">
                <option value="">🏢 Todas as Origens</option>
                <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
             </select>
          </div>
        </div>
      </div>

      <div class="sucata-grid">
        <!-- Pendentes -->
        <div class="sucata-column">
          <div class="col-header">
            <h3>📥 Aguardando Chegada</h3>
            <span class="badge badge-yellow">{{ pneusSucataPendentes.length }}</span>
          </div>
          <div class="sucata-cards">
            <div v-for="p in pneusSucataPendentes" :key="p.id" class="sucata-card pending">
              <div class="s-card-id">{{ p.numero_fogo }}</div>
              <div class="s-card-info">
                <span class="s-tire-name">{{ p.marca }} {{ p.medida }}</span>
                <div class="s-origin-badge">
                  <span class="lbl">Vem de:</span>
                  <span class="val">{{ p.filial_origem_nome || (p.filial_nome?.toUpperCase().includes('SUCATA') ? '—' : p.filial_nome) }}</span>
                </div>
              </div>
              <button class="btn-confirm-arrival" @click="doConfirmarRecebimento(p)">Confirmar Chegada</button>
            </div>
            <div v-if="!pneusSucataPendentes.length" class="empty-sucata">Nenhum pneu em trânsito para sucata</div>
          </div>
        </div>

        <!-- Confirmados -->
        <div class="sucata-column">
          <div class="col-header">
            <h3>✅ Sucata Processada</h3>
            <span class="badge badge-green">{{ pneusSucataConfirmados.length }}</span>
          </div>
          <div class="sucata-cards">
            <div v-for="p in pneusSucataConfirmados" :key="p.id" class="sucata-card done">
              <div class="s-card-id">{{ p.numero_fogo }}</div>
              <div class="s-card-info">
                <span class="s-tire-name">{{ p.marca }} {{ p.medida }}</span>
                <div class="s-origin-badge">
                  <span class="lbl">Veio de:</span>
                  <span class="val">{{ p.filial_origem_nome || (p.filial_nome?.toUpperCase().includes('SUCATA') ? '—' : p.filial_nome) }}</span>
                </div>
              </div>
              <div class="s-card-actions" style="display: flex; gap: 8px; align-items: center;">
                <span class="badge badge-green">Validado</span>
                <button class="btn-recicladora" @click="openReciclagemModal(p)" title="Enviar para Recicladora">♻️ Enviar</button>
              </div>
            </div>
            <div v-if="!pneusSucataConfirmados.length" class="empty-sucata">Nenhuma sucata processada</div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB: HISTÓRICO -->
    <section v-if="tab === 'historico'" class="gp-section">
      <div class="sec-toolbar">
        <div class="toolbar-left">
          <h2>Histórico de Movimentações</h2>
          <p class="sec-subtitle">Registro cronológico de todas as operações de pneus</p>
        </div>
        
        <div class="toolbar-right" style="display: flex; gap: 12px; align-items: center;">
          <div class="search-box-pill">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            <input v-model="searchMov" placeholder="Buscar Placa ou N. Fogo..." />
          </div>

          <select v-model="filtroTipoMov" @change="loadMovs" class="filter-select">
            <option value="">Todos os tipos</option>
            <option value="entrada_estoque">📥 Entrada Estoque</option>
            <option value="alocacao">🚛 Alocação (Vaga)</option>
            <option value="remocao">🔧 Remoção (Retirada)</option>
            <option value="descarte">🗑️ Descarte</option>
            <option value="recebimento_sucata">✅ Confirmação Sucata</option>
            <option value="transferencia">🔄 Transferência</option>
            <option value="recapagem">♻️ Recapagem</option>
            <option value="rodizio">🔄 Rodízio / Troca</option>
          </select>
        </div>
      </div>

      <div class="timeline-container" v-if="filteredMovs.length">
        <div v-for="m in filteredMovs" :key="m.id" class="timeline-item">
          <div class="tl-date">
            <span class="tl-day">{{ new Date(m.criado_em).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) }}</span>
            <span class="tl-time">{{ new Date(m.criado_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', hour12: false }) }}</span>
          </div>
          
          <div class="tl-icon-box" :class="movClass(m.tipo)">
            {{ movIcon(m.tipo) }}
          </div>

          <div class="tl-content">
            <div class="tl-header">
              <span class="tl-type">{{ movLabel(m.tipo) }}</span>
              <span class="tl-pneu">Pneu: <strong>{{ m.numero_fogo || '—' }}</strong></span>
            </div>
            
            <div class="tl-details">
              <div v-if="m.veiculo_placa" class="tl-detail-item">
                <span class="tl-label">Veículo</span>
                <span class="tl-val">🚛 {{ m.veiculo_placa }}</span>
              </div>
              <div v-if="m.posicao" class="tl-detail-item">
                <span class="tl-label">Posição</span>
                <span class="tl-val">📍 {{ posLabel(m.posicao, m.veiculo_tipo) }}</span>
              </div>
              <div v-if="m.km_momento" class="tl-detail-item">
                <span class="tl-label">KM Momento</span>
                <span class="tl-val">🛣️ {{ fmtN(m.km_momento) }} km</span>
              </div>
            </div>

            <div v-if="m.observacao" class="tl-obs">
              <span class="obs-icon">💬</span>
              {{ m.observacao }}
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 16px;"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M12 7v5l3 3"/></svg>
        <p>Nenhuma movimentação encontrada com os filtros atuais.</p>
      </div>
    </section>

    <!-- TAB: RECICLADORA -->
    <section v-if="tab === 'recicladora'" class="gp-section">
      <div class="sec-toolbar">
        <div class="toolbar-left">
          <h2>♻️ Lotes de Reciclagem</h2>
          <p class="sec-subtitle">Acompanhamento de pneus enviados para descarte/compra</p>
        </div>
      </div>

      <div class="lotes-container">
        <div v-for="l in lotesReciclagem" :key="l.id" class="lote-card">
          <div class="lote-header">
            <div class="lote-title">
              <span class="lote-icon">📦</span>
              <div class="lote-names">
                <h3>{{ l.numero_lote }}</h3>
                <span class="lote-date">Envio: {{ new Date(l.data_envio).toLocaleDateString('pt-BR') }}</span>
              </div>
            </div>
            <div class="lote-finance">
              <div class="finance-item" v-if="l.valor_total > 0">
                <span class="lbl">Total Lote:</span>
                <span class="val">{{ l.valor_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }}</span>
              </div>
              <div class="finance-item" v-if="l.valor_pneu > 0">
                <span class="lbl">Por Pneu:</span>
                <span class="val">{{ l.valor_pneu.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }}</span>
              </div>
               <button class="btn-lote-valor" @click="openValorLoteModal(l)" style="margin-right: 8px;">
                {{ l.valor_total > 0 ? '✏️ Editar Valor' : '💰 Informar Valor' }}
              </button>
              <button class="btn-lote-valor" @click="imprimirLote(l)" style="background: #f8fafc; border-color: #cbd5e1;">
                🖨️ Relatório
              </button>
            </div>
          </div>
          <div class="lote-pneus">
            <table class="gp-table mini">
              <thead>
                <tr>
                  <th>N. Fogo</th>
                  <th>Marca/Modelo</th>
                  <th>Filial Origem</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in l.pneus" :key="p.id">
                  <td><strong>{{ p.numero_fogo }}</strong></td>
                  <td>{{ p.marca }} {{ p.modelo }}</td>
                  <td>{{ p.filial_origem_nome || 'N/A' }}</td>
                  <td><span class="badge badge-purple">Reciclagem</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="!lotesReciclagem.length" class="empty-state">Nenhum lote de reciclagem encontrado</div>
      </div>
    </section>

    <!-- TAB: FINANCEIRO -->
    <section v-if="tab === 'financeiro'" class="gp-section">
      <div class="sec-toolbar">
        <div class="toolbar-left">
          <h2>💰 Retorno Financeiro</h2>
          <p class="sec-subtitle">Calculo de créditos por filial referente as carcaças recicladas</p>
        </div>
        <div class="toolbar-right" style="display: flex; gap: 12px;">
          <input type="month" v-model="filtroMesFinanceiro" class="filter-select" />
          <select v-model="filtroFilialFinanceiro" class="filter-select">
            <option value="">Todas as Filiais</option>
            <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
          </select>
        </div>
      </div>

      <div class="financeiro-dashboard">
        <div class="fin-card-main">
          <div class="fin-stat">
            <span class="lbl">Total Arrecadado no Período</span>
            <span class="val big">{{ relatorioFinanceiro.total_geral.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }}</span>
          </div>
          <div class="fin-stat">
            <span class="lbl">Total de Pneus</span>
            <span class="val">{{ relatorioFinanceiro.detalhes.length }}</span>
          </div>
        </div>

        <div class="fin-grid">
          <div class="fin-table-box">
            <h3>Retorno por Filial</h3>
            <table class="gp-table">
              <thead>
                <tr>
                  <th>Filial</th>
                  <th class="text-center">Qtd Pneus</th>
                  <th class="text-right">Valor p/ Receber</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in relatorioFinanceiro.resumo_filiais" :key="r.nome">
                  <td><strong>{{ r.nome }}</strong></td>
                  <td class="text-center">{{ r.pneus }}</td>
                  <td class="text-right text-green"><strong>{{ r.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }}</strong></td>
                </tr>
                <tr v-if="!relatorioFinanceiro.resumo_filiais.length">
                  <td colspan="3" class="text-center opacity-50">Nenhum retorno encontrado para este filtro</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- MODAL: FILIAL FORM -->
    <div v-if="showFilialModal" class="modal-overlay" @click.self="showFilialModal = false">
      <div class="modal-box">
        <h3>{{ editingFilial ? 'Editar Filial' : 'Nova Filial' }}</h3>
        <div class="form-group"><label>Nome</label><input v-model="filialForm.nome" placeholder="Nome da filial" /></div>
        <div class="form-row">
          <div class="form-group"><label>UF (Estado)</label><input v-model="filialForm.estado" maxlength="2" placeholder="Ex: SP, PR" /></div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showFilialModal = false">Cancelar</button>
          <button class="btn-primary" @click="saveFilial" :disabled="!filialForm.nome">Salvar</button>
        </div>
      </div>
    </div>

    <!-- MODAL: VEÍCULO FORM -->
    <div v-if="showVeiculoModal" class="modal-overlay" @click.self="showVeiculoModal = false">
      <div class="modal-box">
        <header class="modal-header-gp">
          <h3>{{ editingVeiculo ? 'Editar Veículo' : 'Novo Veículo' }}</h3>
        </header>
        
        <div class="form-row">
          <div class="form-group">
            <label style="display: flex; justify-content: space-between;">
              Placa 
              <span v-if="!editingVeiculo && veiculoForm.placa && veiculoForm.placa.length >= 7" 
                    @click="buscarPlacaSQL()" 
                    style="color: var(--brand); cursor: pointer; text-transform: none; font-size: 11px;">
                🔍 Autocompletar (SQL)
              </span>
            </label>
            <input v-model="veiculoForm.placa" placeholder="ABC1D23" @blur="buscarPlacaSQL" />
          </div>
          <div class="form-group"><label>Frota</label><input v-model="veiculoForm.frota" placeholder="000" /></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Marca</label><input v-model="veiculoForm.marca" placeholder="Ex: Scania, Volvo" /></div>
          <div class="form-group"><label>Modelo</label><input v-model="veiculoForm.modelo" placeholder="Ex: R450" /></div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Configuração de Eixos</label>
            <select v-model="veiculoForm.tipo" class="select-premium">
              <option v-for="(cfg, key) in vehicleConfigs" :key="key" :value="key">
                {{ cfg.nome }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Filial Responsável</label>
            <select v-model="veiculoForm.filial_id">
              <option :value="null">— Selecione —</option>
              <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
            </select>
          </div>
        </div>

        <!-- Preview da Configuração -->
        <div class="config-preview-box" v-if="veiculoForm.tipo && vehicleConfigs[veiculoForm.tipo]">
          <div class="preview-info">
            <div class="p-item">
              <span class="p-icon">🚛</span>
              <span class="p-text"><strong>{{ vehicleConfigs[veiculoForm.tipo].eixos.length }}</strong> Eixos</span>
            </div>
            <div class="p-item">
              <span class="p-icon">🛞</span>
              <span class="p-text"><strong>{{ countPneus(veiculoForm.tipo) }}</strong> Pneus no total</span>
            </div>
          </div>
          <p class="preview-desc">Esta configuração inclui {{ vehicleConfigs[veiculoForm.tipo].estepes.length }} estepe(s).</p>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showVeiculoModal = false">Cancelar</button>
          <button class="btn-primary" @click="saveVeiculo" :disabled="!veiculoForm.placa || !veiculoForm.tipo">
            Confirmar Cadastro
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL: PNEU FORM -->
    <div v-if="showPneuModal" class="modal-overlay" @click.self="showPneuModal = false">
      <div class="modal-box">
        <h3>{{ editingPneu ? 'Editar Pneu' : 'Novo Pneu' }}</h3>
        
        <div class="form-group" v-if="!editingPneu">
          <label>Modelo Pré-Cadastrado</label>
          <select class="select-premium" v-model="modeloSelecionado" @change="fillModelo">
            <option :value="null">— Selecione para preencher marca/medida —</option>
            <option v-for="(m, i) in modelosPreCadastrados" :key="i" :value="m">
              {{ m.marca }} {{ m.modelo ? '- ' + m.modelo : '' }} ({{ m.medida }})
            </option>
          </select>
        </div>

        <div class="form-row">
          <div class="form-group"><label>N. Fogo</label><input v-model="pneuForm.numero_fogo" placeholder="Número de fogo" /></div>
          <div class="form-group"><label>DOT</label><input v-model="pneuForm.dot" placeholder="Ex: 2024" /></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Marca</label><input v-model="pneuForm.marca" placeholder="Bridgestone, Pirelli..." /></div>
          <div class="form-group"><label>Modelo</label><input v-model="pneuForm.modelo" /></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Medida</label><input v-model="pneuForm.medida" placeholder="295/80R22.5" /></div>
          <div class="form-group"><label>Vida</label><input type="number" v-model.number="pneuForm.vida" min="1" max="5" /></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Valor (R$)</label><input type="number" v-model.number="pneuForm.valor" step="0.01" /></div>
          <div class="form-group"><label>Sulco (mm)</label><input type="number" v-model.number="pneuForm.sulco_atual" step="0.1" /></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Fornecedor</label><input v-model="pneuForm.fornecedor" placeholder="Nome do Fornecedor" /></div>
          <div class="form-group"><label>NF Fiscal</label><input v-model="pneuForm.nf" placeholder="Número da Nota" /></div>
        </div>
        <div class="form-group">
          <label>Filial</label>
          <select v-model="pneuForm.filial_id">
            <option :value="null">— Selecione —</option>
            <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showPneuModal = false">Cancelar</button>
          <button class="btn-primary" @click="savePneu" :disabled="!pneuForm.numero_fogo || !pneuForm.marca || !pneuForm.medida || !pneuForm.filial_id">Salvar</button>
        </div>
      </div>
    </div>

    <!-- MODAL: DETALHE DO VEÍCULO (EIXOS) -->
    <div v-if="showEixosModal" class="modal-overlay" @click.self="showEixosModal = false">
      <div class="modal-box modal-expanded">
        <header class="modal-header-gp">
          <div>
            <h3>{{ veiculoDetail?.placa }} — {{ veiculoDetail?.modelo }}</h3>
            <span class="vd-config-badge">{{ configLabel(veiculoDetail?.tipo) }}</span>
          </div>
          <button class="btn-close" @click="showEixosModal = false">&times;</button>
        </header>

        <div class="gp-move-container">
          <!-- LADO ESQUERDO: DIAGRAMA DO VEÍCULO -->
          <div class="gp-vehicle-canvas">
            <div class="vehicle-diagram-area">
              <!-- CHASSIS -->
              <div class="chassis-box">
                <div class="placa-box">
                  <div class="placa-br">BRASIL</div>
                  <div class="placa-num">{{ veiculoDetail?.placa || 'AAA-1234' }}</div>
                </div>
                <div class="chassis-vertical-line"></div>
              </div>

              <div class="axles-container">
                <div v-for="eixo in veiculoDetail?.config?.eixos" :key="eixo.num" class="axle-row">
                  <div class="axle-visual">
                    <div class="wheels-side side-esq">
                      <div v-for="pos in eixo.posicoes.filter(p => p.includes('ESQ'))" :key="pos" 
                           class="tire-drop-zone"
                           :class="{ occupied: veiculoDetail.pneus[pos], 'drag-over': dragOverPos === pos }"
                           @dragover.prevent="dragOverPos = pos"
                           @dragleave="dragOverPos = null"
                           @drop="handleDropOnSlot(pos)"
                           @click="handleTireClick(pos)">
                        
                        <div v-if="veiculoDetail.pneus[pos]" class="tire-item in-vehicle" 
                             draggable="true" @dragstart="handleDragStartFromVehicle($event, pos, veiculoDetail.pneus[pos])">
                          <div class="tire-id">{{ veiculoDetail.pneus[pos].numero_fogo }}</div>
                        </div>
                        <div v-else class="tire-placeholder">
                          <span>+</span>
                        </div>
                      </div>
                    </div>

                    <div class="axle-bar"></div>
                    <div :class="['center-shape', eixo.num === 1 ? 'shape-diamond' : 'shape-circle']"></div>

                    <div class="wheels-side side-dir">
                      <div v-for="pos in eixo.posicoes.filter(p => p.includes('DIR'))" :key="pos" 
                           class="tire-drop-zone"
                           :class="{ occupied: veiculoDetail.pneus[pos], 'drag-over': dragOverPos === pos }"
                           @dragover.prevent="dragOverPos = pos"
                           @dragleave="dragOverPos = null"
                           @drop="handleDropOnSlot(pos)"
                           @click="handleTireClick(pos)">
                        
                        <div v-if="veiculoDetail.pneus[pos]" class="tire-item in-vehicle"
                             draggable="true" @dragstart="handleDragStartFromVehicle($event, pos, veiculoDetail.pneus[pos])">
                          <div class="tire-id">{{ veiculoDetail.pneus[pos].numero_fogo }}</div>
                        </div>
                        <div v-else class="tire-placeholder">
                          <span>+</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Estepes -->
              <div class="spare-container" v-if="veiculoDetail?.config?.estepes?.length">
                <div class="spare-title">Estepes</div>
                <div v-for="pos in veiculoDetail.config.estepes" :key="pos" 
                     class="tire-drop-zone spare-zone"
                     :class="{ occupied: veiculoDetail.pneus[pos], 'drag-over': dragOverPos === pos }"
                     @dragover.prevent="dragOverPos = pos"
                     @dragleave="dragOverPos = null"
                     @drop="handleDropOnSlot(pos)"
                     @click="handleTireClick(pos)">
                  
                  <div v-if="veiculoDetail.pneus[pos]" class="tire-item in-vehicle"
                       draggable="true" @dragstart="handleDragStartFromVehicle($event, pos, veiculoDetail.pneus[pos])">
                    <div class="tire-id">{{ veiculoDetail.pneus[pos].numero_fogo }}</div>
                  </div>
                  <div v-else class="tire-placeholder"><span>+</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- LADO DIREITO: ESTOQUE (ALMOXARIFADO) -->
          <div class="gp-stock-panel">
            <div class="stock-header">
              <h4>Almoxarifado</h4>
              <span class="stock-count">{{ pneusEstoqueFilial.length }} pneus</span>
            </div>
            
            <div class="form-group" style="margin-bottom: 12px; margin-top: -6px;">
              <select v-model="almoxarifadoFilialId" class="select-premium" @change="loadEstoqueAlmoxarifado">
                <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
              </select>
            </div>
            
            <div class="search-stock">
              <input v-model="searchStock" placeholder="Buscar pneu no estoque..." class="stock-input" />
            </div>

            <div class="stock-list" @dragover.prevent @drop="handleDropOnRemoval('estoque')">
              <div v-for="p in filteredStock" :key="p.id" 
                   class="tire-card-stock" 
                   :class="{ 'tire-pending': p.recebido === 0, 'tire-new': Number(p.vida) === 1 && p.recebido === 1 }"
                   draggable="true" 
                   @dragstart="handleDragStartFromStock($event, p)">
                <div class="tire-mini-visual"></div>
                <div class="tire-card-info">
                  <span class="t-fogo">{{ p.numero_fogo }}</span>
                  <span class="t-desc">{{ p.marca }} {{ p.medida }}</span>
                  <span class="t-status">Vida: {{ p.vida }}ª | {{ p.sulco_atual }}mm</span>
                </div>
              </div>
              <div v-if="!filteredStock.length" class="empty-stock">
                Nenhum pneu disponível nesta filial
              </div>
            </div>

            <!-- Área de Remoção (Lixeira) -->
            <div class="removal-zone sucata-drop" :class="{ 'drag-over': dragOverRemoval }"
                 @dragover.prevent="dragOverRemoval = true"
                 @dragleave="dragOverRemoval = false"
                 @drop="handleDropOnRemoval('sucata')">
              <span class="icon">🗑️</span>
              <span class="label">ARRANTE PARA SUCATA</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL: ALOCAR PNEU -->
    <div v-if="showAlocarModal" class="modal-overlay" @click.self="showAlocarModal = false">
      <div class="modal-box">
        <h3>Alocar Pneu</h3>
        <p v-if="alocarCtx.fromEixo">Posição: <strong>{{ posLabel(alocarCtx.posicao, veiculoDetail?.tipo) }}</strong> no veículo <strong>{{ veiculoDetail?.placa }}</strong></p>
        <div class="form-group" v-if="!alocarCtx.fromEixo">
          <label>Veículo</label>
          <select v-model="alocarForm.veiculo_id" @change="loadPosDisponiveis">
            <option :value="null">— Selecione —</option>
            <option v-for="v in veiculos" :key="v.id" :value="v.id">{{ v.placa }} — {{ v.modelo }}</option>
          </select>
        </div>
        <div class="form-group" v-if="!alocarCtx.fromEixo && alocarForm.veiculo_id">
          <label>Posição</label>
          <select v-model="alocarForm.posicao">
            <option value="">— Selecione —</option>
            <option v-for="p in posDisponiveis" :key="p" :value="p">{{ posLabel(p, currentSelectedVeiculoTipo) }}</option>
          </select>
        </div>
        <div class="form-group" v-if="alocarCtx.fromEixo">
          <label>Pneu (estoque da filial)</label>
          <select v-model="alocarForm.pneu_id">
            <option :value="null">— Selecione —</option>
            <option v-for="p in pneusEstoqueFilial" :key="p.id" :value="p.id">{{ p.numero_fogo }} — {{ p.marca }} {{ p.medida }}</option>
          </select>
        </div>
        <div class="form-group"><label>KM Instalação</label><input type="number" v-model.number="alocarForm.km_instalacao" /></div>
        <div class="form-group"><label>Observação</label><input v-model="alocarForm.observacao" /></div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showAlocarModal = false">Cancelar</button>
          <button class="btn-primary" @click="doAlocar">Confirmar</button>
        </div>
      </div>
    </div>

    <!-- MODAL: REMOVER PNEU -->
    <div v-if="showRemoverModal" class="modal-overlay" @click.self="showRemoverModal = false">
      <div class="modal-box">
        <h3>Remover Pneu</h3>
        <p>Pneu: <strong>{{ removerCtx?.numero_fogo }}</strong> ({{ removerCtx?.marca }} {{ removerCtx?.medida }})</p>
        <div class="form-group">
          <label>Destino</label>
          <select v-model="removerForm.destino">
            <option value="estoque">Voltar ao Estoque</option>
            <option value="descarte">Descarte</option>
            <option value="recapagem">Recapagem</option>
          </select>
        </div>
        <div class="form-group">
          <label>Estoque Destino (Filial)</label>
          <select v-model="removerForm.filial_destino_id">
            <option v-for="f in filiais" :key="f.id" :value="f.id">{{ f.nome }}</option>
          </select>
        </div>
        <div class="form-group"><label>KM Atual</label><input type="number" v-model.number="removerForm.km_momento" /></div>
        <div class="form-group"><label>Observação</label><input v-model="removerForm.observacao" /></div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showRemoverModal = false">Cancelar</button>
          <button class="btn-primary btn-danger" @click="doRemover">Confirmar Remoção</button>
        </div>
      </div>
    </div>

    <!-- MODAL: TRANSFERIR -->
    <div v-if="showTransferirModal" class="modal-overlay" @click.self="showTransferirModal = false">
      <div class="modal-box">
        <h3>Transferir Pneu</h3>
        <p>Pneu: <strong>{{ transferirCtx?.numero_fogo }}</strong> — Filial atual: {{ transferirCtx?.filial_nome }}</p>
        <div class="form-group">
          <label>Filial Destino</label>
          <select v-model="transferirForm.filial_destino_id">
            <option :value="null">— Selecione —</option>
            <option v-for="f in filiais.filter(x => x.id !== transferirCtx?.filial_id)" :key="f.id" :value="f.id">{{ f.nome }}</option>
          </select>
        </div>
        <div class="form-group"><label>Observação</label><input v-model="transferirForm.observacao" /></div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showTransferirModal = false">Cancelar</button>
          <button class="btn-primary" @click="doTransferir" :disabled="!transferirForm.filial_destino_id">Confirmar</button>
        </div>
      </div>
    </div>

    <!-- TOAST -->
    <!-- MODAL: RODÍZIO -->
    <div v-if="showRodizioModal" class="modal-overlay" @click.self="showRodizioModal = false">
      <div class="modal-box">
        <h3>🔄 Rodízio de Pneus</h3>
        <p v-if="rodizioCtx" style="font-size: 13px; color: var(--text2); margin-bottom: 20px;">
          {{ rodizioCtx.isSwap ? 'Trocando pneus entre as posições:' : 'Movendo pneu para nova posição:' }}<br>
          <strong>{{ posLabel(rodizioCtx.oldPos) }} ➔ {{ posLabel(rodizioCtx.pos) }}</strong>
        </p>

        <div class="form-group">
          <label>KM Atual do Veículo</label>
          <input type="number" v-model="rodizioForm.km_momento" class="stock-input" />
        </div>

        <div class="form-group">
          <label>Observação</label>
          <textarea v-model="rodizioForm.observacao" class="stock-input" rows="2"></textarea>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showRodizioModal = false">Cancelar</button>
          <button class="btn-primary" @click="doRodizio">Confirmar Rodízio</button>
        </div>
      </div>
    </div>

    <!-- MODAL: ENVIAR PARA RECICLAGEM -->
    <div v-if="showReciclagemModal" class="modal-overlay" @click.self="showReciclagemModal = false">
      <div class="modal-box">
        <h3>♻️ Enviar para Recicladora</h3>
        <p>Pneu: <strong>{{ reciclagemCtx?.numero_fogo }}</strong> ({{ reciclagemCtx?.marca }} {{ reciclagemCtx?.medida }})</p>
        
        <div class="form-group">
          <label>Data de Envio</label>
          <input type="date" v-model="reciclagemForm.data_envio" class="stock-input" />
        </div>

        <div class="form-group">
          <label>Observação (Opcional)</label>
          <input v-model="reciclagemForm.observacao" class="stock-input" placeholder="Ex: NF de venda, transportadora..." />
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showReciclagemModal = false">Cancelar</button>
          <button class="btn-primary" @click="doEnviarParaRecicladora">Confirmar Envio</button>
        </div>
      </div>
    </div>

    <!-- MODAL: VALOR DO LOTE -->
    <div v-if="showValorLoteModal" class="modal-overlay" @click.self="showValorLoteModal = false">
      <div class="modal-box">
        <h3>💰 Informar Valor do Lote</h3>
        <p>Lote: <strong>{{ valorLoteCtx?.numero_lote }}</strong></p>
        <p style="font-size: 13px; color: var(--text2);">O valor total será dividido entre os <strong>{{ valorLoteCtx?.pneus.length }} pneus</strong> do lote.</p>
        
        <div class="form-group" style="margin-top: 16px;">
          <label>Valor Total Recebido (R$)</label>
          <input type="number" v-model="valorLoteForm.valor_total" class="stock-input" step="0.01" />
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showValorLoteModal = false">Cancelar</button>
          <button class="btn-primary" @click="doAtualizarValorLote">Salvar Valor</button>
        </div>
      </div>
    </div>


    <!-- ELEMENTO PARA IMPRESSÃO (OCULTO NA TELA) -->
    <div id="printable-lote" class="print-only" v-if="loteImpressao">
      <div class="print-header">
        <div class="print-logo-box">
          <img src="../assets/transportes-gritsch (2).png" alt="Logo Gritsch" class="print-logo-img">
        </div>
        <div class="print-header-info">
          <strong>TRANSPORTES GRITSCH LTDA</strong><br>
          RUA FRANCISCO NUNES, 1990 - PRADO VELHO<br>
          80215-202 - CURITIBA / PR<br>
          Fone: (41) 30721100<br>
          nao_responder@grupogritsch.com.br
        </div>
        <div class="print-doc-type">
          <strong>MANIFESTO DE ENVIO</strong><br>
          RECICLAGEM DE PNEUS
        </div>
      </div>

      <div class="print-body">
        <div class="print-summary">
          <p><strong>Lote:</strong> {{ loteImpressao.numero_lote }}</p>
          <p><strong>Data de Envio:</strong> {{ new Date(loteImpressao.data_envio).toLocaleDateString('pt-BR') }}</p>
          <p><strong>Quantidade:</strong> {{ loteImpressao.pneus.length }} pneus</p>
        </div>

        <table class="print-table">
          <thead>
            <tr>
              <th style="width: 20%">N. FOGO</th>
              <th style="width: 50%">MARCA / MODELO</th>
              <th style="width: 30%">OBSERVAÇÃO</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in loteImpressao.pneus" :key="p.id">
              <td>{{ p.numero_fogo }}</td>
              <td>{{ p.marca }} {{ p.modelo }}</td>
              <td>____________________</td>
            </tr>
          </tbody>
        </table>

        <div class="print-footer">
          <div class="print-signature">
            <div class="sig-line"></div>
            <p>Responsável Gritsch (Expedição)</p>
          </div>
          <div class="print-signature">
            <div class="sig-line"></div>
            <p>Responsável Recicladora (Recebimento)</p>
            <p style="font-size: 10px; opacity: 0.7;">Nome Legível / RG</p>
          </div>
        </div>
        
        <div class="print-date-footer">
          Gerado em: {{ new Date().toLocaleString('pt-BR') }} - Sistema KPIs Torre de Controle
        </div>
      </div>
    </div>


    <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  fetchVehicleConfigs, fetchFiliais, createFilial, updateFilial, deleteFilial,
  fetchVeiculos, fetchVeiculo, createVeiculo, updateVeiculo,
  fetchPneusList, createPneu, updatePneu as updatePneuApi,
  alocarPneu, removerPneu, transferirPneu,
  fetchMovimentacoes, fetchGPDashboard,
  sincronizarSqlServer, fetchPlanilhaPneus, fetchBuscaVeiculoSql,
  confirmarRecebimento, rodizioPneu,
  fetchLotesReciclagem, enviarParaReciclagem, atualizarValorLote, fetchRelatorioFinanceiroReciclagem
} from '../api/gestaoPneus.js'

const tabs = [
  { id: 'alocacoes', label: 'Alocações' },
  { id: 'veiculos', label: 'Veículos' },
  { id: 'estoque', label: 'Estoque' },
  { id: 'sucata', label: 'Sucata' },
  { id: 'recicladora', label: 'Recicladora' },
  { id: 'financeiro', label: 'Financeiro' },
  { id: 'filiais', label: 'Filiais' },
  { id: 'historico', label: 'Histórico' },
]
const tab = ref('alocacoes')
const toast = ref(null)
const dash = ref(null)
const loteImpressao = ref(null)

const rodizioCtx = ref(null)
const showRodizioModal = ref(false)
const rodizioForm = ref({ km_momento: 0, observacao: '' })

// Data
const filiais = ref([])
const veiculos = ref([])
const pneusList = ref([])
const pneusGeral = ref([])
const movs = ref([])
const vehicleConfigs = ref({})
const planilhaPneus = ref([])
const modeloSelecionado = ref(null)

// Filters
const filtroFilialV = ref('')
const filtroFilialP = ref('')
const filtroStatus = ref('')
const filtroTipoMov = ref('')
const filtroFilialSucata = ref('')
const searchSucata = ref('')
const filtroFilialFinanceiro = ref('')
const filtroMesFinanceiro = ref(new Date().toISOString().slice(0, 7))

// Modals
const showFilialModal = ref(false)
const showVeiculoModal = ref(false)
const showPneuModal = ref(false)
const showEixosModal = ref(false)
const showAlocarModal = ref(false)
const showRemoverModal = ref(false)
const showTransferirModal = ref(false)
const showReciclagemModal = ref(false)
const showValorLoteModal = ref(false)

// Edit states
const editingFilial = ref(null)
const editingVeiculo = ref(null)
const editingPneu = ref(null)
const veiculoDetail = ref(null)
const lotesReciclagem = ref([])
const relatorioFinanceiro = ref({ resumo_filiais: [], detalhes: [], total_geral: 0 })
const reciclagemCtx = ref(null)
const valorLoteCtx = ref(null)

// Forms
const filialForm = ref({ nome: '', estado: '' })
const veiculoForm = ref({ placa: '', frota: '', modelo: '', marca: '', tipo: 'truck', filial_id: null })
const pneuForm = ref({ numero_fogo: '', marca: '', modelo: '', medida: '', dot: '', valor: 0, vida: 1, filial_id: null, sulco_atual: 0 })
const reciclagemForm = ref({ data_envio: new Date().toISOString().split('T')[0], observacao: '' })
const valorLoteForm = ref({ valor_total: 0 })
const alocarForm = ref({ pneu_id: null, veiculo_id: null, posicao: '', km_instalacao: 0, observacao: '' })
const alocarCtx = ref({ fromEixo: false, posicao: '' })
const removerForm = ref({ pneu_id: null, destino: 'estoque', filial_destino_id: null, km_momento: 0, observacao: '' })
const removerCtx = ref(null)
const transferirForm = ref({ filial_destino_id: null, observacao: '' })
const transferirCtx = ref(null)
const posDisponiveis = ref([])
const pneusEstoqueFilial = ref([])
const almoxarifadoFilialId = ref(null)

// Drag & Drop state
const draggedPneu = ref(null)
const dragSource = ref(null) // 'stock' or 'vehicle'
const dragOldPos = ref(null)
const dragOverPos = ref(null)
const dragOverRemoval = ref(false)
const searchStock = ref('')
const searchVeiculo = ref('')
const searchMov = ref('')

const filteredVeiculos = computed(() => {
  if (!searchVeiculo.value) return veiculos.value
  const s = searchVeiculo.value.toLowerCase()
  return veiculos.value.filter(v => 
    v.placa.toLowerCase().includes(s) || 
    (v.frota && v.frota.toLowerCase().includes(s)) ||
    (v.modelo && v.modelo.toLowerCase().includes(s))
  )
})

const pneusSucataPendentes = computed(() => {
  let list = pneusGeral.value.filter(p => p.recebido === 0 && (p.status === 'descarte' || (p.filial_nome || '').toUpperCase().includes('SUCATA')))
  if (filtroFilialSucata.value) {
    list = list.filter(p => p.filial_origem_id === Number(filtroFilialSucata.value))
  }
  if (searchSucata.value) {
    const s = searchSucata.value.toLowerCase()
    list = list.filter(p => p.numero_fogo.toLowerCase().includes(s))
  }
  return list
})
const pneusSucataConfirmados = computed(() => {
  let list = pneusGeral.value.filter(p => p.recebido === 1 && !p.lote_id && (p.status === 'descarte' || (p.filial_nome || '').toUpperCase().includes('SUCATA')))
  if (filtroFilialSucata.value) {
    list = list.filter(p => p.filial_origem_id === Number(filtroFilialSucata.value))
  }
  if (searchSucata.value) {
    const s = searchSucata.value.toLowerCase()
    list = list.filter(p => p.numero_fogo.toLowerCase().includes(s))
  }
  return list
})

const filteredStock = computed(() => {
  if (!searchStock.value) return pneusEstoqueFilial.value
  const s = searchStock.value.toLowerCase()
  return pneusEstoqueFilial.value.filter(p => 
    p.numero_fogo.toLowerCase().includes(s) || 
    p.marca.toLowerCase().includes(s) || 
    p.medida.toLowerCase().includes(s)
  )
})

const modelosPreCadastrados = computed(() => {
  const map = {}
  planilhaPneus.value.forEach(p => {
    if (!p.marca || !p.medida) return
    const key = `${p.marca.trim()}|${(p.modelo || '').trim()}|${p.medida.trim()}`
    if (!map[key]) {
      map[key] = { marca: p.marca.trim(), modelo: (p.modelo || '').trim(), medida: p.medida.trim() }
    }
  })
  return Object.values(map).sort((a, b) => a.marca.localeCompare(b.marca) || a.medida.localeCompare(b.medida))
})

const filteredMovs = computed(() => {
  if (!searchMov.value) return movs.value
  const s = searchMov.value.toLowerCase()
  return movs.value.filter(m => 
    (m.numero_fogo && m.numero_fogo.toLowerCase().includes(s)) || 
    (m.veiculo_placa && m.veiculo_placa.toLowerCase().includes(s)) ||
    (m.observacao && m.observacao.toLowerCase().includes(s))
  )
})

const currentSelectedVeiculoTipo = computed(() => {
  if (!alocarForm.value.veiculo_id) return null
  const v = veiculos.value.find(x => x.id === alocarForm.value.veiculo_id)
  return v?.tipo
})

// Drag & Drop handlers
function handleDragStartFromStock(event, pneu) {
  event.dataTransfer.effectAllowed = 'move'
  draggedPneu.value = pneu
  dragSource.value = 'stock'
}

function handleDragStartFromVehicle(event, pos, pneu) {
  event.dataTransfer.effectAllowed = 'move'
  draggedPneu.value = pneu
  dragSource.value = 'vehicle'
  dragOldPos.value = pos
}

async function handleDropOnSlot(pos) {
  const p = draggedPneu.value
  const source = dragSource.value
  dragOverPos.value = null
  
  if (!p) return

  try {
    if (source === 'stock') {
      if (veiculoDetail.value.pneus[pos]) {
        showToast('Esta posição já está ocupada. Remova o pneu atual primeiro.', 'error')
        return
      }
      alocarCtx.value = { fromEixo: true, posicao: pos }
      alocarForm.value = { pneu_id: p.id, veiculo_id: veiculoDetail.value.id, posicao: pos, km_instalacao: 0, observacao: 'Montado via diagrama' }
      showAlocarModal.value = true
    } 
    else if (source === 'vehicle') {
      const oldPos = dragOldPos.value
      if (oldPos === pos) return
      
      const isSwap = !!veiculoDetail.value.pneus[pos]
      rodizioCtx.value = { oldPos, pos, isSwap }
      rodizioForm.value = { 
        km_momento: veiculoDetail.value.km_atual || 0, 
        observacao: isSwap ? 'Troca de pneus' : 'Mudança de posição' 
      }
      showRodizioModal.value = true
    }
  } catch(e) { showToast(e.message, 'error') }
  
  draggedPneu.value = null
  dragSource.value = null
}

async function handleDropOnRemoval(target = 'estoque') {
  const p = draggedPneu.value
  const source = dragSource.value
  dragOverRemoval.value = false
  
  if (!p) return

  // CASO 1: Removendo do veículo
  if (source === 'vehicle') {
    removerCtx.value = p
    removerForm.value = { 
      pneu_id: p.id, 
      destino: target === 'sucata' ? 'descarte' : 'estoque', 
      filial_destino_id: veiculoDetail.value?.filial_id || p.filial_id, 
      km_momento: veiculoDetail.value?.km_atual || 0, 
      observacao: target === 'sucata' ? 'Remoção direta para sucata' : '' 
    }
    if (target === 'sucata') {
      const sucata = filiais.value.find(f => f.nome?.toUpperCase().includes('SUCATA'))
      if (sucata) {
        removerForm.value.filial_destino_id = sucata.id
      } else {
        showToast('Filial "SUCATA" não encontrada. Verifique o cadastro de filiais.', 'error')
        return
      }
    }
    showRemoverModal.value = true
  } 
  // CASO 2: Já está no estoque local e foi arrastado para a lixeira de Sucata
  else if (source === 'stock' && target === 'sucata') {
    const sucata = filiais.value.find(f => f.nome?.toUpperCase().includes('SUCATA'))
    if (!sucata) {
      showToast('Filial "SUCATA" não encontrada. Verifique o cadastro de filiais.', 'error')
      return
    }
    removerCtx.value = p
    removerForm.value = { 
      pneu_id: p.id, 
      destino: 'descarte', 
      filial_destino_id: sucata.id, 
      km_momento: 0, 
      observacao: 'Descarte direto do almoxarifado' 
    }
    showRemoverModal.value = true
  }
  
  draggedPneu.value = null
  dragSource.value = null
}

// Helpers
const fmtN = (v) => v ? Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'


const fmtDate = (d) => d ? new Date(d).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
const configLabel = (t) => vehicleConfigs.value[t]?.nome || t
const countPneus = (tipo) => {
  const cfg = vehicleConfigs.value[tipo]
  if (!cfg) return 0
  const eixos = cfg.eixos.reduce((acc, e) => acc + e.posicoes.length, 0)
  return eixos + cfg.estepes.length
}
const statusLabel = (s) => ({ estoque: 'Estoque', em_uso: 'Em Uso', descarte: 'Descartado', recapagem: 'Recapagem' }[s] || s)
const statusClass = (s) => ({ estoque: 'badge-green', em_uso: 'badge-blue', descarte: 'badge-red', recapagem: 'badge-yellow' }[s] || '')
const movLabel = (t) => ({ entrada_estoque: 'Entrada', alocacao: 'Alocação', remocao: 'Remoção', descarte: 'Descarte', transferencia: 'Transferência', recapagem: 'Recapagem', recebimento_sucata: 'Confirmação Sucata', rodizio: 'Rodízio / Troca' }[t] || t)
const movClass = (t) => ({ entrada_estoque: 'badge-green', alocacao: 'badge-blue', remocao: 'badge-yellow', descarte: 'badge-red', transferencia: 'badge-purple', recapagem: 'badge-yellow', recebimento_sucata: 'badge-green', rodizio: 'badge-purple' }[t] || '')
const movIcon = (t) => ({ entrada_estoque: '📥', alocacao: '🚛', remocao: '🔧', descarte: '🗑️', transferencia: '🔄', recapagem: '♻️', recebimento_sucata: '✅', rodizio: '🔄' }[t] || '📄')
const posLabel = (pos, type = null) => {
  if (!pos) return '—'
  
  // Nomes base
  const labels = {
    E1_ESQ: '1º Dianteiro LE',
    E1_DIR: '1º Dianteiro LD',
    E2_ESQ: '2º Dianteiro LE',
    E2_DIR: '2º Dianteiro LD',
    ESTEPE_1: 'Estepe 1',
    ESTEPE_2: 'Estepe 2'
  }

  if (labels[pos]) return labels[pos]

  // Lógica para Truck e Bitruck (E2, E3, E4)
  const isBitruck = type === 'bitruck'
  
  if (pos.startsWith('E2')) {
    // No Bitruck E2 é direcional simples, mas no Truck/Toco é Tração Dupla
    if (isBitruck) return pos.includes('ESQ') ? '2º Dianteiro LE' : '2º Dianteiro LD'
    return 'Tração ' + (pos.includes('ESQ') ? 'LE ' : 'LD ') + (pos.includes('INT') ? 'Int' : 'Fora')
  }

  if (pos.startsWith('E3')) {
    // No Bitruck E3 é Tração, no Truck E3 é o Eixo Truck
    const base = isBitruck ? 'Tração ' : 'Truck '
    return base + (pos.includes('ESQ') ? 'LE ' : 'LD ') + (pos.includes('INT') ? 'Int' : 'Fora')
  }

  if (pos.startsWith('E4')) {
    // No Bitruck E4 é o Eixo Truck
    return 'Truck ' + (pos.includes('ESQ') ? 'LE ' : 'LD ') + (pos.includes('INT') ? 'Int' : 'Fora')
  }

  return pos
}

function showToast(msg, type = 'success') {
  toast.value = { msg, type }
  setTimeout(() => toast.value = null, 3000)
}

// Load data
async function loadAll() {
  try { vehicleConfigs.value = await fetchVehicleConfigs() } catch(e) { console.error(e) }
  try { filiais.value = await fetchFiliais() } catch(e) { console.error(e) }
  try { dash.value = await fetchGPDashboard() } catch(e) { console.error(e) }
  loadVeiculos()
  loadPneus()
  loadPneusGeral()
  loadMovs()
  try { planilhaPneus.value = await fetchPlanilhaPneus() } catch(e) { console.error(e) }
}
async function loadVeiculos() { try { veiculos.value = await fetchVeiculos({ filial_id: filtroFilialV.value }) } catch(e) { console.error(e) } }
async function loadPneus() { try { pneusList.value = await fetchPneusList({ filial_id: filtroFilialP.value, status: filtroStatus.value }) } catch(e) { console.error(e) } }
async function loadPneusGeral() { try { pneusGeral.value = await fetchPneusList({}) } catch(e) { console.error(e) } }
async function loadMovs() { try { movs.value = await fetchMovimentacoes({ tipo: filtroTipoMov.value }) } catch(e) { console.error(e) } }
async function refreshDash() { try { dash.value = await fetchGPDashboard() } catch(e) {} }

// Filiais CRUD
function openFilialForm(f = null) {
  editingFilial.value = f
  filialForm.value = f ? { nome: f.nome, estado: f.estado || '' } : { nome: '', estado: '' }
  showFilialModal.value = true
}
async function saveFilial() {
  try {
    if (editingFilial.value) await updateFilial(editingFilial.value.id, filialForm.value)
    else await createFilial(filialForm.value)
    showFilialModal.value = false
    showToast(editingFilial.value ? 'Filial atualizada!' : 'Filial criada!')
    filiais.value = await fetchFiliais()
    refreshDash()
  } catch(e) { showToast(e.message, 'error') }
}
async function removeFilial(f) {
  if (!confirm(`Desativar a filial "${f.nome}"?`)) return
  try { await deleteFilial(f.id); filiais.value = await fetchFiliais(); showToast('Filial desativada!'); refreshDash() }
  catch(e) { showToast(e.message, 'error') }
}

// Veículos CRUD
function openVeiculoForm(v = null) {
  editingVeiculo.value = v
  veiculoForm.value = v ? { placa: v.placa, frota: v.frota || '', modelo: v.modelo || '', marca: v.marca || '', tipo: v.tipo || 'truck', filial_id: v.filial_id } : { placa: '', frota: '', modelo: '', marca: '', tipo: 'truck', filial_id: null }
  showVeiculoModal.value = true
}

async function buscarPlacaSQL() {
  if (editingVeiculo.value) return; // Não autocompleta se já estiver editando
  const p = veiculoForm.value.placa;
  if (!p || p.length < 7) return;
  
  try {
    const res = await fetchBuscaVeiculoSql(p);
    if (res) {
      if (res.modelo) veiculoForm.value.modelo = res.modelo;
      if (res.marca) veiculoForm.value.marca = res.marca;
      if (res.frota) veiculoForm.value.frota = res.frota;
      if (res.tipo) veiculoForm.value.tipo = res.tipo;
      if (res.filial_id) veiculoForm.value.filial_id = res.filial_id;
      showToast('Veículo encontrado no SQL! Cadastrando automaticamente...', 'success');
      await saveVeiculo();
    }
  } catch (e) {
    if (e.message && e.message.includes('não encontrado')) {
      showToast('Veículo não encontrado no SQL. Preencha manualmente.', 'info');
    } else {
      console.error(e);
      showToast('Erro ao buscar placa no SQL.', 'error');
    }
  }
}

async function saveVeiculo() {
  try {
    if (editingVeiculo.value) await updateVeiculo(editingVeiculo.value.id, veiculoForm.value)
    else await createVeiculo(veiculoForm.value)
    showVeiculoModal.value = false
    showToast(editingVeiculo.value ? 'Veículo atualizado!' : 'Veículo criado!')
    loadVeiculos()
    refreshDash()
  } catch(e) { showToast(e.message, 'error') }
}
async function saveVeiculoInline(v) {
  try {
    await updateVeiculo(v.id, { placa: v.placa, frota: v.frota, modelo: v.modelo, marca: v.marca, tipo: v.tipo, filial_id: v.filial_id })
    showToast('Veículo salvo com sucesso!')
    loadVeiculos() // Recarrega para obter contagens atualizadas
  } catch(e) {
    showToast(e.message, 'error')
    loadVeiculos() // Reverte
  }
}

async function loadEstoqueAlmoxarifado() {
  if (!almoxarifadoFilialId.value) {
    pneusEstoqueFilial.value = []
    return
  }
  try {
    pneusEstoqueFilial.value = await fetchPneusList({ filial_id: almoxarifadoFilialId.value, status: 'estoque' })
  } catch(e) { pneusEstoqueFilial.value = [] }
}

// Veículo Detail (Eixos)
async function openVeiculoDetail(v) {
  try {
    veiculoDetail.value = await fetchVeiculo(v.id)
    searchStock.value = ''
    almoxarifadoFilialId.value = veiculoDetail.value.filial_id
    await loadEstoqueAlmoxarifado()
    if (tab.value !== 'alocacoes') {
      showEixosModal.value = true
    }
  } catch(e) { showToast(e.message, 'error') }
}

// Handle Tire Click
async function handleTireClick(pos) {
  const pneu = veiculoDetail.value?.pneus?.[pos]
  if (pneu) {
    openRemoverModal(pneu)
  } else {
    // Alocar pneu
    alocarCtx.value = { fromEixo: true, posicao: pos }
    alocarForm.value = { pneu_id: null, veiculo_id: veiculoDetail.value.id, posicao: pos, km_instalacao: veiculoDetail.value?.km_atual || 0, observacao: '' }
    try { pneusEstoqueFilial.value = await fetchPneusList({ filial_id: veiculoDetail.value.filial_id, status: 'estoque' }) }
    catch(e) { pneusEstoqueFilial.value = [] }
    showAlocarModal.value = true
  }
}

// Pneus CRUD
function openPneuForm(p = null) {
  editingPneu.value = p
  modeloSelecionado.value = null
  pneuForm.value = p 
    ? { numero_fogo: p.numero_fogo, marca: p.marca, modelo: p.modelo || '', medida: p.medida, dot: p.dot || '', valor: p.valor || 0, vida: p.vida || 1, sulco_atual: p.sulco_atual || 0, filial_id: p.filial_id, nf: p.nf || '', fornecedor: p.fornecedor || '' } 
    : { numero_fogo: '', marca: '', modelo: '', medida: '', dot: '', valor: 0, vida: 1, sulco_atual: 0, filial_id: null, nf: '', fornecedor: '' }
  showPneuModal.value = true
}

function fillModelo() {
  if (modeloSelecionado.value) {
    pneuForm.value.marca = modeloSelecionado.value.marca || ''
    pneuForm.value.modelo = modeloSelecionado.value.modelo || ''
    pneuForm.value.medida = modeloSelecionado.value.medida || ''
  }
}

async function savePneu() {
  try {
    if (editingPneu.value) await updatePneuApi(editingPneu.value.id, pneuForm.value)
    else await createPneu(pneuForm.value)
    showPneuModal.value = false
    showToast(editingPneu.value ? 'Pneu atualizado!' : 'Pneu cadastrado!')
    loadPneus()
    refreshDash()
  } catch(e) { showToast(e.message, 'error') }
}

// Alocar
function openAlocarModal(p) {
  alocarCtx.value = { fromEixo: false, posicao: '' }
  alocarForm.value = { pneu_id: p.id, veiculo_id: null, posicao: '', km_instalacao: 0, observacao: '' }
  showAlocarModal.value = true
}
async function loadPosDisponiveis() {
  if (!alocarForm.value.veiculo_id) { posDisponiveis.value = []; return }
  try {
    const v = await fetchVeiculo(alocarForm.value.veiculo_id)
    if (!alocarCtx.value.fromEixo) alocarForm.value.km_instalacao = v.km_atual || 0
    const cfg = v.config
    const all = []
    cfg.eixos.forEach(e => all.push(...e.posicoes))
    all.push(...cfg.estepes)
    posDisponiveis.value = all.filter(p => !v.pneus[p])
  } catch(e) { posDisponiveis.value = [] }
}
async function doAlocar() {
  try {
    await alocarPneu(alocarForm.value)
    showAlocarModal.value = false
    showToast('Pneu alocado!')
    loadPneus(); loadVeiculos(); refreshDash(); await loadEstoqueAlmoxarifado();
    if (veiculoDetail.value) { 
      veiculoDetail.value = await fetchVeiculo(veiculoDetail.value.id) 
    }
  } catch(e) { showToast(e.message, 'error') }
}

// Remover
function openRemoverModal(p) {
  removerCtx.value = p
  removerForm.value = { pneu_id: p.id, destino: 'estoque', filial_destino_id: veiculoDetail.value?.filial_id || p.filial_id, km_momento: veiculoDetail.value?.km_atual || 0, observacao: '' }
  showRemoverModal.value = true
}
async function doRemover() {
  try {
    await removerPneu({ pneu_id: removerCtx.value.id, ...removerForm.value })
    showRemoverModal.value = false
    showToast('Pneu removido!')
    loadPneus(); loadVeiculos(); refreshDash()
    if (veiculoDetail.value) { 
      veiculoDetail.value = await fetchVeiculo(veiculoDetail.value.id) 
      await loadEstoqueAlmoxarifado()
    }
  } catch(e) { showToast(e.message, 'error') }
}

async function doRodizio() {
  try {
    if (rodizioForm.value.km_momento <= 0) {
      showToast('Por favor, informe um KM válido.', 'error')
      return
    }
    await rodizioPneu({
      veiculo_id: veiculoDetail.value.id,
      pos_origem: rodizioCtx.value.oldPos,
      pos_destino: rodizioCtx.value.pos,
      km_momento: rodizioForm.value.km_momento,
      observacao: rodizioForm.value.observacao
    })
    showRodizioModal.value = false
    showToast('Rodízio realizado com sucesso!')
    veiculoDetail.value = await fetchVeiculo(veiculoDetail.value.id)
    loadPneus(); loadVeiculos(); refreshDash(); await loadEstoqueAlmoxarifado()
  } catch(e) { showToast(e.message, 'error') }
}

// Transferir
function openTransferirModal(p) {
  transferirCtx.value = p
  transferirForm.value = { filial_destino_id: null, observacao: '' }
  showTransferirModal.value = true
}
async function doTransferir() {
  try {
    await transferirPneu({ pneu_id: transferirCtx.value.id, ...transferirForm.value })
    showTransferirModal.value = false
    showToast('Pneu transferido!')
    loadPneus(); refreshDash()
  } catch(e) { showToast(e.message, 'error') }
}

// Reciclagem
async function loadLotes() { try { lotesReciclagem.value = await fetchLotesReciclagem() } catch(e) { console.error(e) } }
async function loadFinanceiro() { 
  try { 
    relatorioFinanceiro.value = await fetchRelatorioFinanceiroReciclagem({ 
      mes: filtroMesFinanceiro.value, 
      filial_id: filtroFilialFinanceiro.value 
    }) 
  } catch(e) { console.error(e) } 
}

function openReciclagemModal(p) {
  reciclagemCtx.value = p
  reciclagemForm.value = { data_envio: new Date().toISOString().split('T')[0], observacao: '' }
  showReciclagemModal.value = true
}

async function doEnviarParaRecicladora() {
  try {
    const pId = reciclagemCtx.value.id
    await enviarParaReciclagem({
      pneu_id: pId,
      data_envio: reciclagemForm.value.data_envio,
      observacao: reciclagemForm.value.observacao
    })
    // Atualização otimista: remove da lista local na hora
    pneusGeral.value = pneusGeral.value.filter(p => p.id !== pId)
    
    showReciclagemModal.value = false
    showToast('Pneu enviado para reciclagem!')
    await loadPneusGeral(); loadPneus(); refreshDash()
  } catch(e) { showToast(e.message, 'error') }
}

function openValorLoteModal(lote) {
  valorLoteCtx.value = lote
  valorLoteForm.value = { valor_total: lote.valor_total || 0 }
  showValorLoteModal.value = true
}

function imprimirLote(lote) {
  loteImpressao.value = lote
  setTimeout(() => {
    window.print()
    loteImpressao.value = null
  }, 300)
}

async function doAtualizarValorLote() {
  try {
    await atualizarValorLote({
      lote_id: valorLoteCtx.value.id,
      valor_total: valorLoteForm.value.valor_total
    })
    showValorLoteModal.value = false
    showToast('Lote atualizado com sucesso!')
    loadLotes()
  } catch(e) { showToast(e.message, 'error') }
}

async function doConfirmarRecebimento(p) {
  if (!confirm(`Confirmar que o pneu ${p.numero_fogo} CHEGOU na filial ${p.filial_nome || ''}?`)) return
  try {
    await confirmarRecebimento(p.id)
    
    // Atualização otimista local
    const pIndex = pneusGeral.value.findIndex(px => px.id === p.id)
    if (pIndex !== -1) {
      pneusGeral.value[pIndex].recebido = 1
      pneusGeral.value[pIndex].status = 'descarte'
    }

    showToast('Recebimento confirmado!')
    await loadPneusGeral()
    loadPneus(); refreshDash(); await loadEstoqueAlmoxarifado();
    if (veiculoDetail.value) { 
       veiculoDetail.value = await fetchVeiculo(veiculoDetail.value.id) 
    }
  } catch(e) { showToast(e.message, 'error') }
}

async function mandarPneuParaSucata(p) {
  const sucataFilial = filiais.value.find(f => f.nome.toUpperCase().includes('SUCATA'))
  if (!sucataFilial) {
    showToast('Não encontrei uma filial com o nome "SUCATA". Crie uma primeiro.', 'error')
    return
  }
  if (!confirm(`Deseja enviar o pneu ${p.numero_fogo} para a filial SUCATA?`)) return
  try {
    await transferirPneu({ pneu_id: p.id, filial_destino_id: sucataFilial.id, observacao: 'Enviado para sucata via atalho' })
    showToast('Pneu enviado para a fila de recebimento da Sucata!')
    loadPneus(); loadPneusGeral(); refreshDash()
  } catch(e) { showToast(e.message, 'error') }
}

watch(tab, (t) => { 
  if (t === 'historico') loadMovs() 
  if (t === 'sucata') loadPneusGeral()
  if (t === 'recicladora') loadLotes()
  if (t === 'financeiro') loadFinanceiro()
})
watch([filtroMesFinanceiro, filtroFilialFinanceiro], () => {
  if (tab.value === 'financeiro') loadFinanceiro()
})

watch(() => removerForm.value.destino, (val) => {
  if (val === 'descarte') {
    const sucata = filiais.value.find(f => f.nome.toUpperCase().includes('SUCATA'))
    if (sucata) removerForm.value.filial_destino_id = sucata.id
  }
})

onMounted(loadAll)
</script>

<style scoped>
.gp-page { padding: 28px 32px; width: 100%; max-width: none; }
.gp-header h1 { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 16px; }



/* KPI Cards */
.gp-kpis { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 32px; }
.kpi-card { background: #fff; border: 1px solid var(--border); border-radius: 16px; padding: 20px 24px; min-width: 160px; flex: 1; display: flex; flex-direction: column; gap: 6px; box-shadow: var(--shadow-sm); transition: transform 0.2s ease, box-shadow 0.2s ease; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.kpi-val { font-size: 26px; font-weight: 800; color: var(--text); line-height: 1.1; letter-spacing: -0.02em; }
.kpi-lbl { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text3); }
.kpi-green .kpi-val { color: var(--green); }
.kpi-blue .kpi-val { color: var(--blue); }
.kpi-red .kpi-val { color: var(--red); }
.kpi-yellow .kpi-val { color: var(--yellow); }



/* Tabs */
.gp-tabs { display: flex; gap: 4px; background: #fff; border-radius: 12px; padding: 6px; border: 1px solid var(--border); margin-bottom: 24px; width: fit-content; box-shadow: var(--shadow-sm); }
.gp-tab { padding: 8px 20px; border: none; background: none; border-radius: 8px; font-size: 13px; font-weight: 600; color: var(--text2); cursor: pointer; transition: all 0.2s; }
.gp-tab:hover { background: var(--s3); color: var(--text); }
.gp-tab.active { background: var(--brand); color: #fff; box-shadow: var(--shadow-sm); }

/* Section */
.gp-section { background: #fff; border: 1px solid var(--border); border-radius: 20px; padding: 32px; box-shadow: var(--shadow-sm); transition: box-shadow 0.2s; }
.gp-section:hover { box-shadow: var(--shadow-md); }
.sec-toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.sec-toolbar h2 { font-size: 16px; font-weight: 700; margin-right: auto; }

/* Tables */
.table-responsive { width: 100%; overflow-x: auto; padding-bottom: 8px; border-radius: 8px; }
.table-responsive::-webkit-scrollbar { height: 10px; }
.table-responsive::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 8px; }
.table-responsive::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 8px; }
.table-responsive::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.gp-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; white-space: nowrap; }
.gp-table th { background: #F9FAFB; font-weight: 700; color: var(--text3); text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; padding: 16px; border-bottom: 2px solid var(--border); text-align: left; }
.gp-table th:first-child { border-top-left-radius: 8px; }
.gp-table th:last-child { border-top-right-radius: 8px; }
.gp-table td { padding: 16px; border-bottom: 1px solid var(--border); color: var(--text); vertical-align: middle; transition: background 0.15s; }
.gp-table tr:hover td { background: #F9FAFB; }
.row-disabled td { opacity: 0.5; text-decoration: line-through; }
.td-actions { display: flex; gap: 8px; }

.vida-badge { background: var(--s2); font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; color: var(--text2); }

/* Inline Select */
.inline-select { padding: 6px 12px; border: 1px solid var(--border); border-radius: 8px; background: #f8fafc; font-size: 13px; font-weight: 500; color: var(--text); outline: none; transition: all 0.2s; width: 100%; max-width: 180px; cursor: pointer; }
.inline-select:hover { border-color: #cbd5e1; background: #fff; box-shadow: var(--shadow-sm); }
.inline-select:focus { border-color: var(--brand); background: #fff; box-shadow: 0 0 0 3px rgba(196,18,48,0.1); }

/* Badges */
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-green { background: var(--green2); color: #065f46; }
.badge-blue { background: var(--blue2); color: #1e40af; }
.badge-red { background: var(--red2); color: #991b1b; }
.badge-yellow { background: var(--yellow2); color: #92400e; }
.badge-purple { background: #ede9fe; color: #5b21b6; }

/* Buttons */
.btn-primary { padding: 10px 20px; background: linear-gradient(180deg, var(--brand) 0%, var(--brand-dark) 100%); color: #fff; border: 1px solid var(--brand-dark); border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.1); text-shadow: 0 1px 1px rgba(0,0,0,0.2); }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 6px -1px rgba(196,18,48,0.2); }
.btn-primary:active { transform: translateY(0); box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-secondary { padding: 10px 20px; background: #fff; color: var(--text); border: 1px solid var(--s4); border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; box-shadow: var(--shadow-sm); }
.btn-secondary:hover { background: var(--s3); border-color: var(--text3); }
.btn-sm { padding: 6px 12px; border: 1px solid var(--s4); background: #fff; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; color: var(--text); transition: all 0.2s; white-space: nowrap; box-shadow: var(--shadow-sm); }
.btn-sm:hover { background: var(--s3); border-color: var(--text3); transform: translateY(-1px); }
.btn-accent { background: var(--brand-bg); color: var(--brand); border-color: var(--brand-mid); box-shadow: none; }
.btn-accent:hover { background: var(--brand-mid); color: var(--brand-dark); }
.btn-danger { color: var(--red); border-color: var(--red3); }
.btn-danger:hover { background: var(--red2); }
.filter-select { padding: 8px 12px; border: 1px solid var(--s4); border-radius: 8px; font-size: 13px; font-weight: 500; background: #fff; color: var(--text); min-width: 160px; box-shadow: var(--shadow-sm); outline: none; transition: 0.2s; }
.filter-select:focus { border-color: var(--brand); box-shadow: 0 0 0 3px rgba(196,18,48,0.1); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(4px); }
.modal-box { background: #fff; border-radius: 20px; padding: 32px; width: 480px; max-width: 95vw; max-height: 90vh; overflow-y: auto; box-shadow: var(--shadow-float); animation: modalIn 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes modalIn { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.modal-wide { width: 800px; }
.modal-box h3 { font-size: 20px; font-weight: 800; margin-bottom: 24px; color: var(--text); letter-spacing: -0.01em; }
.modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--border); }

/* Forms */
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; flex: 1; }
.form-group label { font-size: 12px; font-weight: 700; color: var(--text2); text-transform: uppercase; letter-spacing: 0.05em; }
.form-group input, .form-group select { padding: 10px 14px; border: 1px solid var(--s4); border-radius: 8px; font-size: 14px; color: var(--text); background: #fff; transition: all 0.2s; box-shadow: var(--shadow-sm); outline: none; }
.form-group input:focus, .form-group select:focus { border-color: var(--brand); box-shadow: 0 0 0 3px rgba(196,18,48,0.1); }
.form-row { display: flex; gap: 16px; }

/* Empty */
.empty-state { text-align: center; padding: 48px 20px; color: var(--text3); font-size: 14px; font-weight: 500; display: flex; flex-direction: column; align-items: center; border: 2px dashed var(--s2); border-radius: 12px; margin: 20px 0; background: #fafafa; }
.empty-state p { margin: 0; }

/* Eixos Diagram PREMIUM */
.modal-expanded { width: 1100px; max-width: 98vw; padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.modal-header-gp { padding: 20px 28px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #fafafa; }
.vd-config-badge { font-size: 11px; font-weight: 700; background: var(--s3); color: var(--text2); padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
.btn-close { background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text3); }

.gp-move-container { display: flex; height: 600px; }

/* Diagram Área */
.gp-vehicle-canvas { flex: 1; padding: 30px; background: #fafafa; overflow-y: auto; border-right: 1px solid var(--border); display: flex; justify-content: center; align-items: flex-start; }

.vehicle-diagram-area { position: relative; padding: 60px 40px; margin-top: 20px; }

.chassis-box { position: absolute; left: 50%; transform: translateX(-50%); width: 220px; top: 0; bottom: 0; border: 6px solid #d1d5db; border-radius: 20px; z-index: 1; background: #f8fafc; }
.placa-box { position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #fff; border: 1px solid #94a3b8; border-radius: 4px; border-top: 5px solid #0284c7; width: 90px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); z-index: 5; }
.placa-br { font-size: 8px; font-weight: 700; color: #fff; background: #0284c7; margin-top: -5px; padding-bottom: 1px; }
.placa-num { font-size: 14px; font-weight: 700; color: #1e293b; padding: 2px 0; font-family: monospace; }
.chassis-vertical-line { position: absolute; left: 50%; transform: translateX(-50%); width: 10px; background: #8892b0; top: 10%; bottom: 10%; z-index: 1; border-radius: 4px; }

.axles-container { display: flex; flex-direction: column; gap: 30px; z-index: 2; position: relative; }

.axle-row { display: flex; align-items: center; justify-content: center; position: relative; width: 100%; z-index: 2; }
.axle-visual { display: flex; align-items: center; justify-content: center; position: relative; width: 350px; height: 100px; }

.axle-bar { position: absolute; left: 16px; right: 16px; height: 10px; background: #8892b0; z-index: 1; border-radius: 4px; }

.center-shape { position: absolute; z-index: 3; background: #f8fafc; border: 6px solid #8892b0; }
.shape-diamond { width: 40px; height: 40px; transform: rotate(45deg); }
.shape-circle { width: 40px; height: 40px; border-radius: 50%; }

.wheels-side { display: flex; gap: 4px; z-index: 5; position: absolute; }
.side-esq { left: 0; }
.side-dir { right: 0; }

.tire-drop-zone { 
  width: 32px; height: 90px; border: 2px dashed #cbd5e1; border-radius: 8px; 
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  transition: all 0.2s; background: #fff; cursor: pointer;
}
.tire-drop-zone.drag-over { border-color: var(--brand); background: var(--brand-bg); }
.tire-drop-zone.occupied { border: none; background: transparent; }

.tire-placeholder { display: flex; flex-direction: column; align-items: center; color: #94a3b8; }
.tire-placeholder span { font-size: 24px; font-weight: 300; }

.tire-item { 
  width: 32px; height: 90px; background: linear-gradient(to right, #1a1a1a 0%, #3a3a3a 50%, #1a1a1a 100%);
  border-radius: 6px; display: flex; align-items: center; justify-content: center;
  color: #fff; cursor: grab; box-shadow: inset 0 0 4px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.3);
  position: relative; border: 1px solid #000;
}
.tire-item::before { content: ''; position: absolute; top: 0; left: 6px; right: 6px; bottom: 0; border-left: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); }

.tire-id { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 13px; font-weight: 700; letter-spacing: 1px; color: #e2e8f0; z-index: 2; }

/* Estepes */
.spare-container { position: absolute; right: -80px; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; align-items: center; gap: 10px; z-index: 5; }
.spare-title { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }


/* Stock Panel */
.gp-stock-panel { width: 320px; background: #f1f5f9; border-left: 1px solid var(--border); display: flex; flex-direction: column; }
.stock-header { padding: 20px; display: flex; justify-content: space-between; align-items: center; }
.stock-header h4 { font-size: 14px; font-weight: 700; }
.stock-count { font-size: 11px; font-weight: 700; color: var(--brand); background: var(--brand-bg); padding: 2px 8px; border-radius: 10px; }
.search-stock { padding: 0 20px 15px; }
.stock-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; }

.stock-list { flex: 1; overflow-y: auto; padding: 0 15px; display: flex; flex-direction: column; gap: 10px; }
.tire-card-stock { 
  background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 12px;
  display: flex; gap: 12px; cursor: grab; transition: all 0.2s;
}
.tire-card-stock:hover { border-color: var(--brand); transform: translateX(4px); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.tire-card-stock.tire-pending { border: 2px solid #ef4444; background: #fff1f2; position: relative; }
.tire-card-stock.tire-pending::after { content: 'PENDENTE'; position: absolute; bottom: 4px; right: 8px; font-size: 8px; font-weight: 800; color: #ef4444; }
.tire-card-stock.tire-new { border: 2px solid #22c55e; background: #f0fdf4; position: relative; }
.tire-card-stock.tire-new::after { content: 'NOVO'; position: absolute; bottom: 4px; right: 8px; font-size: 8px; font-weight: 800; color: #22c55e; }
.tire-mini-visual { 
  width: 24px; height: 56px; 
  background: linear-gradient(to right, #1a1a1a 0%, #4a4a4a 50%, #1a1a1a 100%);
  border-radius: 4px; position: relative; border: 1px solid #000;
  box-shadow: inset 0 0 3px rgba(0,0,0,0.8), var(--shadow-sm);
  flex-shrink: 0;
}
.tire-mini-visual::before {
  content: ''; position: absolute; top: 0; left: 4px; right: 4px; bottom: 0;
  border-left: 1px solid rgba(255,255,255,0.08); border-right: 1px solid rgba(255,255,255,0.08);
}
.tire-card-info { display: flex; flex-direction: column; }
.t-fogo { font-size: 13px; font-weight: 700; color: var(--text); }
.t-desc { font-size: 11px; color: var(--text2); }
.t-status { font-size: 10px; font-weight: 600; color: var(--text3); margin-top: 2px; }

.removal-zone { 
  margin: 15px; padding: 20px; border: 2px dashed #94a3b8; border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: #64748b; transition: all 0.2s;
}
.removal-zone.drag-over { border-color: var(--red); background: #fef2f2; color: var(--red); transform: scale(1.02); }
.removal-zone .icon { font-size: 24px; }
.removal-zone .label { font-size: 11px; font-weight: 700; text-align: center; text-transform: uppercase; }

.empty-stock { text-align: center; padding: 40px 20px; font-size: 13px; color: var(--text3); }

@media (max-width: 768px) {
  .gp-move-container { flex-direction: column; height: auto; }
  .gp-stock-panel { width: 100%; height: 400px; border-left: none; border-top: 1px solid var(--border); }
}

/* Config Preview Box */
.config-preview-box { background: var(--brand-bg); border: 2px solid var(--brand-mid); border-radius: 12px; padding: 16px; margin-top: 10px; }

/* Sucata Tab Styles */
.sucata-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 20px; }
.sucata-column { background: #f8fafc; border: 1px solid var(--border); border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.col-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }
.col-header h3 { font-size: 15px; font-weight: 700; color: #1e293b; }
.sucata-cards { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; max-height: 600px; padding: 4px; }
.sucata-card { 
  background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 16px;
  display: flex; align-items: center; gap: 16px; transition: all 0.2s;
}
.sucata-card.pending { border-left: 4px solid #f59e0b; }
.sucata-card.done { border-left: 4px solid #10b981; }
.sucata-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.s-card-id { font-size: 14px; font-weight: 800; color: var(--text); background: #f1f5f9; padding: 4px 8px; border-radius: 6px; }
.s-card-info { flex: 1; display: flex; flex-direction: column; }
.s-card-info span { font-size: 13px; font-weight: 600; }
.s-card-info small { font-size: 11px; color: var(--text3); }
.btn-confirm-arrival { 
  background: var(--brand); color: #fff; border: none; padding: 8px 16px; border-radius: 8px;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.2s;
}
.btn-confirm-arrival:hover { background: var(--brand-dark); transform: scale(1.05); }
.empty-sucata { text-align: center; padding: 40px 20px; color: #94a3b8; font-size: 13px; font-style: italic; }
.s-card-actions { display: flex; align-items: center; gap: 10px; }
.btn-icon { background: none; border: none; cursor: pointer; font-size: 16px; opacity: 0.6; transition: opacity 0.2s; }
.btn-icon:hover { opacity: 1; }


.preview-info { display: flex; gap: 24px; margin-bottom: 4px; }
.p-item { display: flex; align-items: center; gap: 10px; }
.p-icon { font-size: 24px; }
.p-text { font-size: 14px; color: var(--text); }
.p-text strong { font-size: 18px; color: var(--brand); }
.preview-desc { font-size: 11px; color: var(--text3); font-weight: 500; margin: 0; }

.select-premium { border-color: var(--brand-mid) !important; font-weight: 600; color: var(--brand); }

/* Toast */
.toast { position: fixed; bottom: 24px; right: 24px; padding: 12px 24px; border-radius: 10px; font-size: 14px; font-weight: 500; color: #fff; z-index: 2000; animation: slideIn .3s ease; box-shadow: 0 8px 24px rgba(0,0,0,.15); }
.toast.success { background: var(--green); }
.toast.error { background: var(--red); }
@keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

@media (max-width: 768px) {
  .gp-page { padding: 16px; }
  .form-row { flex-direction: column; }
  .modal-wide { width: 95vw; }
}

/* Novo Layout de Alocação */
.alocacao-layout { display: flex; gap: 0; padding: 0 !important; height: calc(100vh - 160px); min-height: 600px; overflow: hidden; margin: -10px -20px; }
.aloc-sidebar { width: 300px; border-right: 1px solid var(--border); background: #fff; display: flex; flex-direction: column; }
.aloc-sidebar .search-box { padding: 20px; border-bottom: 1px solid var(--border); }
.aloc-veiculo-list { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 6px; }
.aloc-v-card { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 12px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.aloc-v-card:hover { background: #f8fafc; border-color: var(--border); }
.aloc-v-card.active { background: var(--brand-bg); border-color: var(--brand-mid); }
.v-card-icon { font-size: 20px; }
.v-card-info { flex: 1; display: flex; flex-direction: column; }
.v-placa { font-weight: 800; color: var(--text); font-size: 14px; }
.v-modelo { font-size: 11px; color: var(--text3); }

.aloc-workbench { flex: 1; background: #fff; display: flex; flex-direction: column; position: relative; }
.workbench-content { height: 100%; display: flex; flex-direction: column; }
.workbench-header { padding: 15px 30px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #fff; }
.wb-info { display: flex; align-items: center; gap: 16px; }
.wb-info h2 { font-size: 22px; font-weight: 900; color: var(--text); margin: 0; }
.workbench-inner { flex: 1; height: auto !important; }

.empty-mini { text-align: center; padding: 20px; font-size: 12px; color: var(--text3); }
.select-v-prompt { text-align: center; margin-top: 100px; }
.prompt-icon { font-size: 64px; display: block; margin-bottom: 20px; opacity: 0.5; }

@media (max-width: 1024px) {
  .aloc-sidebar { width: 220px; }
}

/* Histórico Timeline */
.sec-subtitle { font-size: 13px; color: var(--text3); margin: -4px 0 0; }
.search-box-pill { display: flex; align-items: center; gap: 8px; background: #f1f5f9; padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); width: 280px; }
.search-box-pill input { background: transparent; border: none; outline: none; font-size: 13px; width: 100%; color: var(--text); }
.search-box-pill svg { color: var(--text3); }

.timeline-container { display: flex; flex-direction: column; gap: 2px; padding: 20px 0; max-width: 900px; margin: 0 auto; }
.timeline-item { display: flex; gap: 24px; padding: 16px; border-radius: 12px; transition: all 0.2s; position: relative; }
.timeline-item:hover { background: #f8fafc; }
.timeline-item::before { content: ''; position: absolute; left: 95px; top: 0; bottom: 0; width: 2px; background: #e2e8f0; z-index: 1; }
.timeline-item:first-child::before { top: 20px; }
.timeline-item:last-child::before { bottom: 20px; }

.tl-date { width: 60px; display: flex; flex-direction: column; align-items: flex-end; justify-content: center; flex-shrink: 0; }
.tl-day { font-size: 14px; font-weight: 800; color: var(--text); }
.tl-time { font-size: 11px; color: var(--text3); font-weight: 600; }

.tl-icon-box { 
  width: 42px; height: 42px; border-radius: 50%; background: #fff; border: 2px solid #e2e8f0;
  display: flex; align-items: center; justify-content: center; font-size: 20px;
  z-index: 2; position: relative; flex-shrink: 0; box-shadow: var(--shadow-sm);
}

.tl-content { flex: 1; background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 16px; box-shadow: var(--shadow-sm); }
.tl-header { display: flex; justify-content: space-between; margin-bottom: 12px; align-items: center; }
.tl-type { font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text); }
.tl-pneu { font-size: 13px; color: var(--text2); }

.tl-details { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 12px; }
.tl-detail-item { display: flex; flex-direction: column; gap: 2px; }
.tl-label { font-size: 10px; font-weight: 700; color: var(--text3); text-transform: uppercase; }
.tl-val { font-size: 13px; font-weight: 600; color: var(--text); }

.tl-obs { background: #f8fafc; padding: 10px 14px; border-radius: 8px; font-size: 12px; color: var(--text2); display: flex; align-items: center; gap: 8px; font-style: italic; }
.obs-icon { font-style: normal; }

/* Sucata Origin Badges */
.s-origin-badge { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.s-origin-badge .lbl { font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--text3); }
.s-origin-badge .val { font-size: 11px; font-weight: 700; color: #0284c7; background: #f0f9ff; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd; }
.s-tire-name { font-weight: 800; color: #1e293b; font-size: 14px; }

.badge-new-tiny { background: #dcfce7; color: #166534; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 4px; border: 1px solid #bbf7d0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

.row-new td { background-color: #f0fdf4 !important; border-top: 1px solid #bbf7d0; border-bottom: 1px solid #bbf7d0; }
.row-new:hover td { background-color: #dcfce7 !important; }

/* Reciclagem e Financeiro Styles */
.btn-recicladora { background: #e0f2f1; color: #00897b; border: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-recicladora:hover { background: #00897b; color: white; }

.lotes-container { display: flex; flex-direction: column; gap: 24px; }
.lote-card { background: white; border-radius: 12px; border: 1px solid var(--border); overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.lote-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; background: #f8fafc; border-bottom: 1px solid var(--border); }
.lote-title { display: flex; gap: 16px; align-items: center; }
.lote-icon { font-size: 24px; }
.lote-names h3 { margin: 0; font-size: 18px; color: var(--text); }
.lote-date { font-size: 13px; color: #94a3b8; }
.lote-finance { display: flex; gap: 24px; align-items: center; }
.finance-item { display: flex; flex-direction: column; text-align: right; }
.finance-item .lbl { font-size: 11px; color: #94a3b8; text-transform: uppercase; }
.finance-item .val { font-size: 16px; font-weight: 700; color: #10b981; }
.btn-lote-valor { background: white; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; transition: all 0.2s; }
.btn-lote-valor:hover { border-color: #3b82f6; color: #3b82f6; }
.lote-pneus { padding: 0; }
.gp-table.mini { margin: 0; font-size: 13px; border: none; }
.gp-table.mini th { background: transparent; padding: 12px 24px; }
.gp-table.mini td { padding: 12px 24px; }

.financeiro-dashboard { display: flex; flex-direction: column; gap: 24px; }
.fin-card-main { display: flex; gap: 48px; background: white; padding: 32px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid var(--border); }
.fin-stat { display: flex; flex-direction: column; gap: 8px; }
.fin-stat .lbl { font-size: 14px; font-weight: 600; color: #64748b; }
.fin-stat .val { font-size: 28px; font-weight: 800; color: var(--text); }
.fin-stat .val.big { color: #10b981; }
.fin-grid { display: grid; grid-template-columns: 1fr; gap: 24px; }
.fin-table-box { background: white; padding: 24px; border-radius: 16px; border: 1px solid var(--border); }
.fin-table-box h3 { margin-bottom: 20px; font-size: 18px; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.text-green { color: #10b981; }
.opacity-50 { opacity: 0.5; }

/* PRINT STYLES */
.print-only { display: none; }

@media print {
  /* Esconde especificamente os elementos do layout global e da página */
  nav.sidebar, 
  .sec-toolbar, 
  .gp-section, 
  .modal-overlay, 
  .sidebar-spacer, 
  .nav-group,
  button, 
  .toast { 
    display: none !important; 
  }

  /* Remove margens e estruturas que empurram o conteúdo */
  .shell { display: block !important; }
  .main-content { 
    margin: 0 !important; 
    padding: 0 !important; 
    display: block !important; 
    width: 100% !important;
  }

  /* Garante que o relatório seja o único soberano na página */
  #printable-lote {
    display: block !important;
    visibility: visible !important;
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: white !important;
    z-index: 9999;
  }
  
  #printable-lote * {
    visibility: visible !important;
  }

  @page {
    margin: 0;
  }
}

#printable-lote { font-family: 'Inter', sans-serif; color: #1a1a1a; padding: 40px !important; }
.print-header { display: flex; border: 2px solid #000; margin-bottom: 20px; }
.print-logo-box { width: 180px; padding: 10px; border-right: 2px solid #000; display: flex; align-items: center; justify-content: center; }
.print-logo-img { width: 100%; height: auto; display: block; }

.print-header-info { flex: 1; padding: 10px; font-size: 11px; line-height: 1.4; border-right: 2px solid #000; }
.print-doc-type { width: 180px; padding: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; background: #f0f0f0; }

.print-summary { display: flex; gap: 30px; margin-bottom: 20px; padding: 10px; background: #f8fafc; border: 1px solid #eee; }
.print-summary p { margin: 0; font-size: 13px; }

.print-table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
.print-table th { background: #f0f0f0; border: 1px solid #000; padding: 10px; text-align: left; font-size: 12px; }
.print-table td { border: 1px solid #000; padding: 8px 10px; font-size: 12px; }

.print-footer { display: flex; justify-content: space-around; margin-top: 60px; }
.print-signature { width: 250px; text-align: center; }
.sig-line { border-top: 1px solid #000; margin-bottom: 8px; }
.print-signature p { margin: 0; font-size: 12px; }

.print-date-footer { margin-top: 40px; font-size: 10px; text-align: center; color: #999; border-top: 1px dotted #ccc; padding-top: 10px; }

</style>
