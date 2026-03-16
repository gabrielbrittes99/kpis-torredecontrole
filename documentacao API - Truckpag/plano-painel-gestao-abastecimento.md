# Plano de Desenvolvimento — Painel de Gestão de Abastecimento em Tempo Real
**TruckPag Meios de Pagamento**
Versão 1.0 · Março 2026

---

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [API TruckPag — Referência Técnica Completa](#2-api-truckpag--referência-técnica-completa)
3. [Funcionalidades do Painel](#3-funcionalidades-do-painel)
4. [Dados e Lógica de Negócio](#4-dados-e-lógica-de-negócio)
5. [Arquitetura e Stack Tecnológica](#5-arquitetura-e-stack-tecnológica)
6. [Layout e UX do Painel](#6-layout-e-ux-do-painel)
7. [Segurança e Boas Práticas](#7-segurança-e-boas-práticas)
8. [Roadmap de Desenvolvimento](#8-roadmap-de-desenvolvimento)
9. [Checklist de Pré-requisitos](#9-checklist-de-pré-requisitos)
10. [Glossário](#10-glossário)

---

## 1. Visão Geral do Projeto

### 1.1 Objetivo

Desenvolver um painel web de monitoramento em tempo real que consuma a API da TruckPag Meios de Pagamento e exiba todas as transações de abastecimento com status **RECUSADO**. O objetivo é permitir que a equipe operacional identifique e resolva rapidamente os problemas enfrentados pelos motoristas na pista, antes mesmo que eles precisem ligar para o suporte.

### 1.2 Problema que o painel resolve

Hoje, quando um motorista tenta abastecer e a transação é recusada, os motivos variam (valor divergente, KM inválido, placa incorreta, duplicidade, etc.) e a equipe de suporte **não tem visibilidade imediata**. O motorista fica parado na pista aguardando atendimento manual e reativo.

O painel elimina esse gap, dando à equipe um **feed ao vivo de todas as recusas** para atuação proativa.

### 1.3 Resultados esperados

- Redução do tempo médio de resolução de transações recusadas
- Visibilidade centralizada de todos os erros de abastecimento em tempo real
- Identificação do motivo de recusa antes mesmo do motorista entrar em contato
- Histórico e tendências dos motivos para ações preventivas na frota
- KPIs de aprovação/rejeição disponíveis para a gestão

---

## 2. API TruckPag — Referência Técnica Completa

### 2.1 Ambientes

| Ambiente | Base URL | Uso |
|----------|----------|-----|
| **Homologação (HML)** | `https://api.hml.truckpag.com.br` | Desenvolvimento e testes |
| **Produção (PRD)** | `https://api.prd.truckpag.com.br` | Go-live e operação real |

> ⚠️ **ATENÇÃO:** Sempre desenvolver e testar no ambiente HML antes de migrar para PRD. Solicitar tokens separados para cada ambiente pelo e-mail: **ti@truckpag.com.br**

### 2.2 Autenticação

Toda requisição autenticada deve incluir o seguinte header HTTP:

```
Authorization: Bearer {SEU_TOKEN}
Content-Type: application/json
Accept: application/json
```

- O token deve ser solicitado via e-mail para `ti@truckpag.com.br`
- Solicitar tokens **separados** para HML e PRD
- Guardar o token em variável de ambiente (`.env`), **NUNCA** hardcoded no código
- Todos os endpoints do módulo **Integração Clientes** exigem autenticação

---

### 2.3 Endpoint Principal do Painel

O painel se baseia inteiramente neste endpoint para buscar as transações recusadas:

```
POST /api/integracao-clientes/relatorios/analitico-transacao
```

#### 2.3.1 Parâmetros do Body

| Campo | Tipo | Obrig. | Descrição / Valor para o painel |
|-------|------|--------|----------------------------------|
| `data_inicial` | string (Y-m-d) | Condicional* | Data de início. Para o painel: **data de hoje**. Obrigatório quando `transacoes_id` não está presente. |
| `data_final` | string (Y-m-d) | Condicional* | Data de fim. Para o painel: **data de hoje**. Obrigatório quando `transacoes_id` não está presente. |
| `transacao_status` | integer[] | Não | **Enviar `[2]` para buscar apenas RECUSADAS.** Se omitido, retorna todos os status. |
| `clientes_id` | integer[] | Não | Lista de IDs de clientes. Se omitido, retorna todos vinculados ao token. |
| `estabelecimentos_id` | integer[] | Não | Filtrar por postos específicos. |
| `veiculo_placas` | string[] | Não | Filtrar por placas (sem formatação: `AAA1234` ou `AAA0A00`, max 100 chars). |
| `transacoes_id` | integer[] | Condicional* | Buscar transações específicas por ID. Dispensa datas. |
| `bomba` | string | Não | `T` = Todas, `I` = Interna, `E` = Externa |
| `com_nfe` | string | Não | `S` = Sim, `N` = Não, `T` = Todas |
| `transacao_tipo` | integer[] | Não | `1` = Manual, `2` = Compra, `3` = Estorno |
| `motivos_estorno_transacao_id` | integer[] | Não | Filtrar por motivo de recusa específico (ver seção 2.5). |
| `veiculo_numeros_frota` | string[] | Não | Filtrar por número de frota (max 20 chars). |
| `servicos_id` | integer[] | Não | Filtrar por tipo de serviço. |

> *Obrigatório quando `transacoes_id` não está presente.

#### 2.3.2 Exemplo de Request para o Painel

```json
POST https://api.hml.truckpag.com.br/api/integracao-clientes/relatorios/analitico-transacao
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "data_inicial": "2026-03-12",
  "data_final": "2026-03-12",
  "transacao_status": [2]
}
```

#### 2.3.3 Campos Relevantes da Resposta

Cada objeto do array retornado contém:

| Campo | Tipo | Importância | Descrição |
|-------|------|-------------|-----------|
| `transacao_id` | integer | 🔴 CRÍTICA | ID único da transação. Usar para identificar novas entradas. |
| `transacao_data` | string (ISO 8601) | 🔴 CRÍTICA | Data e hora da tentativa de abastecimento. |
| `transacao_valor` | decimal | 🔴 CRÍTICA | Valor total da transação tentada. |
| `transacao_status` | string | 🔴 CRÍTICA | `APROVADA`, `RECUSADA`, `MANUAL`, etc. |
| `motorista_nome` | string | 🔴 CRÍTICA | Nome completo do motorista. |
| `veiculo_placa` | string | 🔴 CRÍTICA | Placa do veículo. |
| `estabelecimento_nome` | string | 🔴 CRÍTICA | Nome do posto de combustível. |
| `motivo_estorno_id` | integer | 🔴 CRÍTICA | ID do motivo de recusa (ver seção 2.5). |
| `motivo_estorno_descricao` | string | 🔴 CRÍTICA | Descrição do motivo de recusa. |
| `mensagem` | string | 🔴 CRÍTICA | Mensagem descritiva do resultado. |
| `quilometragem` | integer | 🟠 ALTA | KM/hodômetro informado pelo motorista. |
| `litragem` | decimal | 🟠 ALTA | Volume em litros da tentativa. |
| `valor_litro` | decimal | 🟠 ALTA | Preço por litro informado pelo posto. |
| `cartao_numero` | string | 🟠 ALTA | Número do cartão utilizado. |
| `hodometro_anterior` | integer | 🟠 ALTA | Último KM registrado para o veículo (para detectar KM retroativo). |
| `cliente_nome` | string | 🟡 MÉDIA | Nome da empresa/cliente. |
| `cliente_id` | integer | 🟡 MÉDIA | ID da empresa/cliente. |
| `estabelecimento_id` | integer | 🟡 MÉDIA | ID do posto. |
| `combustivel_nome` | string | 🟡 MÉDIA | Nome do combustível (Diesel S10, etc.). |
| `operador_nome` | string | 🟡 MÉDIA | Nome do operador do posto. |
| `registro_data` | string | 🟡 MÉDIA | Data de registro da transação no sistema. |
| `transacao_tipo` | string | 🟡 MÉDIA | `MANUAL`, `COMPRA`, `ESTORNO`. |
| `servico_nome` | string | 🟢 BAIXA | Nome do serviço (ex: "Abastecimento"). |
| `tipo_medidor_nome` | string | 🟢 BAIXA | `Hodômetro`, `Horímetro`, etc. |
| `cliente_cnpj` | string | 🟢 BAIXA | CNPJ da empresa. |
| `estabelecimento_cnpj` | string | 🟢 BAIXA | CNPJ do posto. |

---

### 2.4 Outros Endpoints Úteis

| Endpoint | Método | Para que serve no painel |
|----------|--------|--------------------------|
| `POST /api/integracao-clientes/relatorios/analitico-abastecimentos` | POST | Buscar histórico de aprovadas para comparação de padrões e cálculo de taxa de rejeição. |
| `GET /api/integracao-clientes/motorista` (ou similar) | GET | Listar motoristas para filtros. |
| `PUT /api/integracao-clientes/motorista/{id}` | PUT | Atualizar dados do motorista se necessário via painel (ex: corrigir KM limite). |

---

### 2.5 Tabela Completa de Motivos de Recusa

O campo `motivo_estorno_id` indica por que a transação foi recusada. O painel **deve exibir a descrição amigável**, não apenas o ID.

| ID | Motivo | Causa comum / O que verificar |
|----|--------|-------------------------------|
| **1** | **Valor / Preço Divergente** | Valor da transação ou preço/litro diferente do negociado ou do limite autorizado. **Erro mais frequente.** |
| **2** | Estabelecimento Incorreto | Posto não autorizado para o cartão ou cliente. |
| **3** | Dois Combustíveis | Dois tipos de combustível selecionados no mesmo abastecimento. |
| **4** | Dois Serviços | Dois serviços selecionados na mesma transação. |
| **5** | Lançamento Incorreto (Bomba Interna) | Erro no lançamento manual de bomba interna. |
| **6** | Duplicidade de Transação | Transação idêntica já registrada em curto intervalo de tempo. |
| **7** | Serviço Incorreto | Serviço não liberado para o cartão deste veículo. |
| **8** | Placa Incorreta | Placa informada não encontrada ou diferente do cadastro da frota. |
| **9** | Transação de Teste | Transação gerada em ambiente de testes. |
| **10** | NFe/NFSe Cancelada | Nota fiscal da transação foi cancelada pelo estabelecimento. |

> 💡 **DICA:** Os motivos **1 (Valor)**, **6 (Duplicidade)** e **8 (Placa)** são tipicamente os mais frequentes. O painel deve ter filtros rápidos para esses três.

---

### 2.6 Campos de Status de Transação (transacao_status)

| Valor | Significado |
|-------|-------------|
| `APROVADA` | Transação autorizada e concluída |
| `RECUSADA` | Transação negada (foco do painel) |
| `MANUAL` | Transação em processo de aprovação manual |

> Para buscar apenas recusadas no endpoint, enviar `"transacao_status": [2]` no body.

---

## 3. Funcionalidades do Painel

### 3.1 Mapa de Funcionalidades por Prioridade

| Funcionalidade | Prioridade | Complexidade | Sprint |
|----------------|------------|-------------|--------|
| Polling automático do endpoint de transações recusadas | 🔴 CRÍTICA | Alta | 1 |
| Feed ao vivo com cards de transações recusadas | 🔴 CRÍTICA | Alta | 1 |
| Exibição do motivo de recusa com descrição amigável | 🔴 CRÍTICA | Baixa | 1 |
| Detecção de novas transações sem duplicação | 🔴 CRÍTICA | Média | 1 |
| KPIs no topo: total recusadas, por hora, taxa de aprovação | 🟠 ALTA | Média | 1 |
| Toast/alerta visual para novas transações recusadas | 🟠 ALTA | Média | 1 |
| Filtros rápidos por tipo de erro (Valor, KM, Placa, Outros) | 🟠 ALTA | Baixa | 1 |
| Configuração de Bearer Token na interface | 🟠 ALTA | Baixa | 1 |
| Modal de detalhe completo da transação | 🟠 ALTA | Média | 2 |
| Sidebar com ranking de motivos de recusa | 🟡 MÉDIA | Média | 2 |
| Ação "Marcar como Resolvido" com log da sessão | 🟡 MÉDIA | Alta | 2 |
| Filtro avançado: empresa, posto, motorista, placa | 🟡 MÉDIA | Média | 2 |
| Configuração do intervalo de polling (15s, 30s, 1min, 2min) | 🟡 MÉDIA | Baixa | 2 |
| Tratamento completo de erros HTTP da API | 🟡 MÉDIA | Média | 2 |
| Histórico das últimas 24h / 7 dias | 🟢 BAIXA | Alta | 3 |
| Exportação CSV / Excel das transações recusadas | 🟢 BAIXA | Média | 3 |
| Gráfico de recusas por hora do dia | 🟢 BAIXA | Alta | 3 |
| Notificação por e-mail/webhook Slack em pico de recusas | 🟢 BAIXA | Alta | 3 |

---

### 3.2 Detalhamento das Funcionalidades Críticas

#### 3.2.1 Polling Automático

- Chamar o endpoint a cada N segundos (configurável: 15s, 30s, 1min, 2min)
- Comparar os `transacao_id` retornados com o Set de IDs já conhecidos
- Somente transações com IDs novos são tratadas como novas recusas
- Nunca duplicar uma transação no feed, mesmo que a API retorne o mesmo registro
- Exibir contador regressivo até a próxima consulta
- Pausar automaticamente se a API retornar erro HTTP 3x consecutivas
- Ajustar `data_inicial` e `data_final` automaticamente à virada do dia (meia-noite)

#### 3.2.2 Feed de Transações Recusadas

- Exibir cada transação como um **card** com as informações prioritárias
- Novas transações entram **no topo do feed** com animação visual (slide-in)
- Campos em conflito com o erro ficam destacados em vermelho/laranja (ex: valor em erro de valor, KM em erro de hodômetro)
- O feed exibe até 80–100 cards; transações mais antigas são descartadas progressivamente
- Suporte a filtros rápidos sem recarregar a página

#### 3.2.3 KPIs do Topo (5 cards)

1. **Recusadas hoje** — total acumulado desde abertura do painel
2. **Última hora** — recusadas nos últimos 60 minutos
3. **Motivo mais frequente** — motivo com maior contagem + número de ocorrências
4. **Última atualização** — horário da última consulta + countdown para a próxima
5. **Aprovadas / Taxa** — total de aprovadas e percentual de rejeição do dia

#### 3.2.4 Toast de Alerta

- Aparece no canto superior direito a cada nova recusa detectada
- Exibe: nome do motorista, placa e motivo da recusa
- Desaparece automaticamente após ~4 segundos
- Máximo de 3–5 toasts simultâneos para não poluir a tela

#### 3.2.5 Marcar como Resolvido

- Remove a transação do feed ativo visualmente
- Registra localmente na sessão: quem resolveu + horário
- **Não chama nenhum endpoint da API TruckPag** — é controle interno do painel
- Transações resolvidas podem ir para uma aba "Resolvidos" (ao invés de serem excluídas)
- Se o próximo polling retornar a mesma transação já resolvida, não re-exibi-la

---

## 4. Dados e Lógica de Negócio

### 4.1 Regras de Negócio

#### 4.1.1 Fluxo do Polling (passo a passo)

```
1. Timer dispara (ex: a cada 30s)
         ↓
2. POST /relatorios/analitico-transacao
   body: { data_inicial: hoje, data_final: hoje, transacao_status: [2] }
         ↓
3. API retorna array de transacoes[]
         ↓
4. Filtrar: novas = retorno.filter(tx => !idsConhecidos.has(tx.transacao_id))
            + excluir idsResolvidos
         ↓
5. Adicionar novas no topo do feed + disparar toast de alerta
         ↓
6. Atualizar idsConhecidos + KPIs + Sidebar + Log de atividade
         ↓
7. Reiniciar o countdown para o próximo ciclo
```

#### 4.1.2 Classificação Automática para Filtros

O painel classifica cada transação recusada em uma categoria para os filtros rápidos:

| Categoria | Como classificar | Campos em destaque no card |
|-----------|------------------|---------------------------|
| **Valor / Preço** | `motivo_estorno_id === 1` | `transacao_valor` e `valor_litro` em vermelho |
| **KM / Hodômetro** | `motivo_estorno_id === 1` + `mensagem` contém 'km' ou 'hodômetro' | `quilometragem` em laranja, exibir `hodometro_anterior` |
| **Placa** | `motivo_estorno_id === 8` | `veiculo_placa` em vermelho |
| **Duplicidade** | `motivo_estorno_id === 6` | `transacao_id` + `transacao_data` |
| **Estabelecimento** | `motivo_estorno_id === 2` | `estabelecimento_nome` em destaque |
| **Outros** | IDs 3, 4, 5, 7, 9, 10 | `mensagem` completa |

#### 4.1.3 Cálculo de "Última Hora"

```
transacoesUltimaHora = allTx.filter(tx => 
  (Date.now() - new Date(tx.transacao_data).getTime()) < 3_600_000
)
```

#### 4.1.4 Tempo Relativo (campo `transacao_data`)

Converter para exibição amigável, atualizado a cada 30 segundos:

| Diferença | Exibir |
|-----------|--------|
| < 60s | "X seg atrás" |
| < 3600s | "X min atrás" |
| < 86400s | "Xh atrás" |
| ≥ 86400s | "DD/MM HH:mm" |

---

### 4.2 Modelo de Estado do Frontend

```javascript
// Estado global do painel
{
  // DADOS
  transacoesRecusadas: Transacao[],      // feed principal (ordenado do mais novo)
  idsConhecidos: Set<number>,            // para detectar novas a cada polling
  idsResolvidos: Set<number>,            // transações marcadas como resolvidas
  
  // CONTROLE
  pollingAtivo: boolean,
  intervaloPolling: number,              // ms: 15000 | 30000 | 60000 | 120000
  timerHandle: number | null,
  
  // FILTROS
  filtroAtivo: 'todos' | 'valor' | 'km' | 'placa' | 'outros',
  
  // MÉTRICAS
  totalAprovadas: number,
  ultimaAtualizacao: Date | null,
  contadorRegressivo: number,            // segundos até próxima consulta
  
  // SESSÃO
  log: LogEntry[],                       // atividade da sessão (max 30 entradas)
  totalRequisicoes: number,
  ultimoStatusHTTP: number | null,
  ultimaLatencia: number | null,         // ms
  errosConsecutivos: number,             // pausar após 3
}
```

### 4.3 Estrutura do Objeto Transação (enriquecido pelo painel)

```typescript
interface Transacao {
  // Campos vindos da API TruckPag
  transacao_id: number;
  transacao_data: string;         // ISO 8601
  transacao_valor: number;
  transacao_status: string;
  transacao_tipo: string;
  motorista_nome: string;
  veiculo_placa: string;
  cartao_numero: string;
  estabelecimento_nome: string;
  estabelecimento_id: number;
  cliente_nome: string;
  cliente_id: number;
  combustivel_nome: string;
  litragem: number;
  valor_litro: number;
  quilometragem: number;
  hodometro_anterior: number;
  mensagem: string;
  motivo_estorno_id: number;
  motivo_estorno_descricao: string;
  operador_nome: string;
  registro_data: string;

  // Campos adicionados pelo painel (prefixo _)
  _isNew: boolean;               // true apenas no ciclo em que foi detectada
  _categoria: string;            // classificação para filtros rápidos
  _valorConflito: boolean;       // destacar campo valor em vermelho
  _kmConflito: boolean;          // destacar campo km em laranja
  _resolvidoPor?: string;        // nome do operador que marcou como resolvido
  _resolvidoEm?: Date;           // quando foi marcado como resolvido
}
```

---

## 5. Arquitetura e Stack Tecnológica

### 5.1 Opções de Stack

| Opção | Frontend | Backend/BFF | Indicado quando |
|-------|----------|-------------|-----------------|
| **A — MVP Simples** ✅ | React ou HTML + Vanilla JS | Nenhum — chama a API diretamente | Painel interno, CORS liberado, time pequeno. |
| **B — Com BFF** | React / Next.js | Node.js + Express | Token deve ficar seguro no servidor; múltiplos usuários. |
| **C — Full Stack** | React / Vue | Node.js + banco de dados | Histórico persistente, auditoria, múltiplos operadores. |

> 💡 **RECOMENDAÇÃO:** Para o MVP, usar a **Opção A** (React + chamada direta). É suficiente para uso interno e mais rápido de entregar. O token é configurado via interface a cada sessão.

---

### 5.2 Problema de CORS — O que Verificar

A API TruckPag pode **não permitir chamadas diretas do browser** por política de CORS. É o primeiro ponto a validar antes de começar o desenvolvimento.

| Cenário | Solução |
|---------|---------|
| **CORS liberado** | Chamar a API diretamente do browser. Mais simples — funciona para o MVP. |
| **CORS bloqueado** | Criar um endpoint proxy simples em Node.js/Express que recebe a requisição do frontend e repassa para a API com o token no header. O token fica no servidor. |
| **Ambiente corporativo com proxy HTTP** | Configurar o proxy para permitir saída para `api.hml.truckpag.com.br` e `api.prd.truckpag.com.br`. |

**Como testar CORS:**
```javascript
// Testar no console do browser (F12)
fetch('https://api.hml.truckpag.com.br/api/integracao-clientes/relatorios/analitico-transacao', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer SEU_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ data_inicial: '2026-03-12', data_final: '2026-03-12', transacao_status: [2] })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

---

### 5.3 Estrutura de Arquivos Sugerida (Opção A — React)

```
painel-abastecimento/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.jsx               # Logo + indicador LIVE + relógio
│   │   ├── ConfigBar.jsx            # Input de token + seletor de intervalo
│   │   ├── KpiStrip.jsx             # 5 cards de métricas
│   │   ├── TransacaoCard.jsx        # Card individual do feed
│   │   ├── TransacaoModal.jsx       # Modal de detalhe
│   │   ├── FeedHeader.jsx           # Título + filtros rápidos
│   │   ├── Sidebar.jsx              # Ranking de motivos + log
│   │   └── Toast.jsx                # Notificações temporárias
│   ├── hooks/
│   │   └── usePolling.js            # Lógica de polling + detecção de novas
│   ├── utils/
│   │   ├── api.js                   # Função fetchTransacoes()
│   │   ├── classificar.js           # Classificar transação por categoria
│   │   ├── formatters.js            # Formatar valor, data, tempo relativo
│   │   └── motivos.js               # Mapa ID → descrição dos motivos
│   ├── constants/
│   │   └── motivos.js               # Tabela de motivos de recusa (seção 2.5)
│   ├── App.jsx                      # Componente raiz + estado global
│   └── main.jsx
├── .env                             # BEARER_TOKEN=... (não commitar)
├── .gitignore                       # incluir .env
└── package.json
```

---

## 6. Layout e UX do Painel

### 6.1 Zonas da Tela

| Zona | Conteúdo |
|------|----------|
| **Header** | Logo TruckPag + nome do painel + indicador LIVE pulsante + relógio em tempo real |
| **Barra de Configuração** | Input do Bearer Token (campo password) + seletor de intervalo de polling + botão Iniciar/Parar |
| **Strip de KPIs** | 5 cards horizontais: Recusadas hoje · Última hora · Motivo top · Última atualização · Aprovadas/Taxa |
| **Feed principal (70% da largura)** | Lista de cards ordenados do mais novo ao mais antigo. Filtros rápidos no topo. |
| **Sidebar direita (30%)** | Ranking de motivos com barras de progresso + log de atividade + status da conexão |
| **Barra de status (rodapé)** | Status online/offline + ambiente (HML/PRD) + endpoint consumido |

### 6.2 Campos Obrigatórios no Card de Transação

| Campo no card | Dado da API | Observação UX |
|---------------|-------------|----------------|
| Nome do motorista | `motorista_nome` | Elemento principal, fonte maior |
| Placa do veículo | `veiculo_placa` | Badge colorido (azul) |
| Nome do posto | `estabelecimento_nome` | Badge secundário |
| ID da transação | `transacao_id` | Para o operador copiar/consultar |
| **Motivo de recusa** | `motivo_estorno_id` + descrição | Box em vermelho com ícone de erro. Texto amigável da seção 2.5 |
| Mensagem da API | `mensagem` | Detalhe técnico, truncado em 90 chars |
| Valor tentado | `transacao_valor` | Em vermelho se for erro de valor |
| Litros | `litragem` | "X,X L" com 1 casa decimal |
| KM / Hodômetro | `quilometragem` | Em laranja se for erro de KM |
| Preço por litro | `valor_litro` | "R$ X,XX" |
| Tempo relativo | calculado de `transacao_data` | "X min atrás", atualizado a cada 30s |
| Botões de ação | — | Copiar ID · Copiar dados · ✓ Resolvido |

### 6.3 Modal de Detalhe (ao clicar no card)

O modal deve exibir **todos os campos do card** mais os seguintes adicionais:

- Número do cartão (`cartao_numero`)
- CNPJ do posto (`estabelecimento_cnpj`)
- Nome do operador do posto (`operador_nome`)
- Tipo de bomba (`bomba`)
- Hodômetro anterior × hodômetro informado (para detectar KM retroativo)
- Tipo de combustível + serviço
- Botões: Fechar · Copiar dados JSON · Marcar como Resolvido

### 6.4 Sidebar — Ranking de Motivos

```
Motivos de Recusa (hoje)
─────────────────────────────
Valor/Preço Divergente  ████████  23
Duplicidade             ████      11
Placa Incorreta         ███        8
Estab. Incorreto        ██         5
Outros                  █          2
```

---

## 7. Segurança e Boas Práticas

### 7.1 Proteção do Bearer Token

> 🔴 **CRÍTICO:** O Bearer Token dá acesso a dados sensíveis de toda a frota. Trate-o como uma senha.

- **NUNCA** commitar o token em repositório Git (nem em `.env` sem `.gitignore`)
- **Frontend puro (MVP):** pedir o token via input (campo `type="password"`) a cada sessão. Não persistir no `localStorage`.
- **Com BFF:** guardar o token em variável de ambiente do servidor (`process.env.TRUCKPAG_TOKEN`), nunca enviar ao browser
- Rotacionar o token periodicamente junto com o time da TruckPag
- Considerar tokens individuais por operador/ambiente quando possível

### 7.2 Configurações de Rede

- Liberar saída HTTPS (porta 443) para `api.hml.truckpag.com.br` e `api.prd.truckpag.com.br` no firewall corporativo
- Verificar com a TruckPag se o IP de saída do ambiente precisa de whitelist
- Solicitar à TruckPag a liberação do CORS para a origem do painel (ex: `https://painel.suaempresa.com.br`)

### 7.3 Tratamento de Erros HTTP da API

| HTTP Status | Significado | Ação no painel |
|-------------|-------------|----------------|
| `200` | Sucesso | Processar normalmente |
| `401` | Token inválido ou expirado | Parar polling. Exibir alerta "Token inválido — reconfigure". |
| `403` | Sem permissão | Verificar se o token tem acesso ao módulo Integração Clientes. |
| `422` | Dados inválidos no request | Verificar os parâmetros enviados (datas, formato). |
| `429` | Rate limit atingido | Aumentar o intervalo de polling. Implementar back-off exponencial. |
| `500` | Erro interno da API | Registrar no log. Tentar novamente no próximo ciclo. |
| Timeout / Network error | Falha de conexão | Registrar no log. Após 3 falhas consecutivas: parar e alertar o operador. |

### 7.4 Intervalo de Polling x Rate Limit

A API pode ter limites de requisições por minuto. Recomendações:

| Intervalo | Req/hora | Uso recomendado |
|-----------|----------|-----------------|
| 15s | 240/h | Operações críticas, pico de movimento |
| 30s | 120/h | **Padrão recomendado** |
| 1min | 60/h | Horários de menor movimento |
| 2min | 30/h | Modo econômico / madrugada |

---

## 8. Roadmap de Desenvolvimento

### Sprint 1 — MVP Operacional (1–2 semanas)

| # | Tarefa | Estimativa |
|---|--------|------------|
| 1 | Solicitar token Bearer HML para ti@truckpag.com.br | 1 dia |
| 2 | Validar CORS: testar chamada direta do browser à API HML | 0,5 dia |
| 3 | Se CORS bloqueado: criar proxy BFF simples em Node.js | 1 dia |
| 4 | Setup do projeto (React) com estrutura de pastas e estado global | 1 dia |
| 5 | Implementar `usePolling`: timer + chamada à API + detecção de novas por ID | 1 dia |
| 6 | Renderizar feed de cards com todos os campos obrigatórios (seção 6.2) | 2 dias |
| 7 | KPIs no topo (5 cards) com cálculo em tempo real | 1 dia |
| 8 | Toast de alerta para novas transações | 0,5 dia |
| 9 | Filtros rápidos: Todos / Valor / KM / Placa / Outros | 1 dia |
| 10 | Testes com dados reais no HML + ajustes de campos e formatação | 1 dia |

### Sprint 2 — Qualidade e UX (1–2 semanas)

| # | Tarefa | Estimativa |
|---|--------|------------|
| 11 | Modal de detalhe completo ao clicar no card | 1 dia |
| 12 | Sidebar com ranking de motivos e log de atividade | 1 dia |
| 13 | Funcionalidade "Marcar como Resolvido" com controle de sessão | 1 dia |
| 14 | Filtros avançados: empresa, posto, motorista, data range | 2 dias |
| 15 | Tratamento de todos os erros HTTP (seção 7.3) + back-off | 1 dia |
| 16 | Refinamentos de UX, responsividade e acessibilidade | 1 dia |
| 17 | Deploy no ambiente interno de homologação | 1 dia |

### Sprint 3 — Evolução Futura

| # | Tarefa |
|---|--------|
| 18 | Migrar para ambiente PRD após validação completa |
| 19 | Persistência de histórico em banco de dados |
| 20 | Gráfico de recusas por hora do dia e por dia da semana |
| 21 | Exportação de relatório CSV/Excel |
| 22 | Notificação por webhook Slack / e-mail em pico de recusas |
| 23 | Dashboard gerencial com métricas semanais/mensais |
| 24 | Autenticação de operadores com log de quem resolveu o quê |

---

## 9. Checklist de Pré-requisitos

Confirmar cada item antes de iniciar o desenvolvimento:

### 9.1 Acesso e Credenciais

- [ ] Token Bearer HML solicitado para `ti@truckpag.com.br`
- [ ] Token Bearer HML recebido e testado com curl ou Postman
- [ ] Token Bearer PRD planejado (solicitar separadamente)
- [ ] IDs de exemplo válidos para o HML obtidos: `empresa_id`, `cliente_id`
- [ ] Documentação da API baixada / URL do Swagger anotada

### 9.2 Infraestrutura

- [ ] CORS validado: testar chamada direta do browser à API HML
- [ ] Se CORS bloqueado: servidor/BFF Node.js provisionado
- [ ] Saída HTTPS para `api.hml.truckpag.com.br` liberada no firewall
- [ ] Repositório Git criado com `.gitignore` incluindo `.env`
- [ ] Ambiente de deploy definido (Vercel, servidor próprio, etc.)

### 9.3 Definições de Negócio

- [ ] Intervalo de polling definido pela equipe (recomendado: **30s**)
- [ ] Quais motivos de recusa são prioritários para o time de suporte
- [ ] Quem terá acesso ao painel e como será feito o controle de acesso
- [ ] Se a ação "Resolvido" precisa ser rastreada por operador (implica autenticação)
- [ ] Horário de operação do painel: 24/7 ou apenas horário comercial
- [ ] Definir se o histórico precisa ser persistido além da sessão atual

---

## 10. Glossário

| Termo | Definição |
|-------|-----------|
| **Bearer Token** | Chave de autenticação gerada pela TruckPag, enviada no header `Authorization` de cada requisição à API. |
| **Polling** | Técnica de consultar repetidamente um endpoint em intervalos regulares para detectar novos dados, simulando tempo real. |
| **HML** | Ambiente de Homologação — para testes sem impacto em dados reais da operação. |
| **PRD** | Ambiente de Produção — dados reais da operação de frota. |
| **CORS** | Cross-Origin Resource Sharing — política do browser que pode bloquear chamadas a APIs de outro domínio. |
| **BFF** | Backend for Frontend — servidor intermediário que chama a API no lado do servidor, sem expor o token ao browser. |
| **transacao_status** | Campo da API que indica o resultado: `APROVADA`, `RECUSADA`, `MANUAL`. |
| **motivo_estorno_id** | Código numérico do motivo pelo qual a transação foi recusada (ver seção 2.5). |
| **Feed** | Lista contínua de itens atualizada em tempo real, ordenada do mais novo ao mais antigo. |
| **KPI** | Key Performance Indicator — indicador numérico exibido nos cards do topo do painel. |
| **Toast** | Notificação temporária que aparece automaticamente na tela e desaparece após alguns segundos. |
| **Integração Clientes** | Módulo da API TruckPag que gerencia motoristas, relatórios analíticos e importação de abastecimentos. |
| **Back-off exponencial** | Estratégia de aumentar progressivamente o intervalo entre tentativas após erros consecutivos. |

---

*Documento gerado em Março de 2026 · TruckPag Meios de Pagamento · v1.0*
