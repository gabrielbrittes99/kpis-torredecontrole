# KPIs Torre de Controle - Modo TV (Dashboard)

Este guia explica como colocar o painel em funcionamento em uma TV ou monitor de monitoramento.

## 🚀 Como Rodar (O jeito mais fácil)

Se você já tem o projeto na máquina:

1. **Configure o `.env`**: Certifique-se de que o arquivo `backend\.env` existe e tem as credenciais corretas.
2. **Execute o `INICIAR.bat`**: Basta dar um duplo clique neste arquivo.
    - Ele vai verificar/instalar o Python e Node.js automaticamente.
    - Vai configurar o ambiente e baixar as dependências.
    - Vai buildar o frontend se necessário.
    - Vai abrir o navegador automaticamente em modo **Fullscreen (Kiosk)**.

## 🛑 Como Parar

1. Execute o arquivo **`PARAR.bat`**.
    - Ele vai encerrar o servidor e liberar os processos.

## 🛠️ Requisitos Mínimos (O script tenta instalar sozinho)

- **Windows 10 ou 11** (com suporte a `winget` preferencialmente).
- Conexão com a internet para a primeira execução (instalação de dependências).
- Arquivo `backend\.env` configurado.

## 📝 Observações

- O servidor roda localmente na porta `8000`.
- Os logs do servidor ficam salvos em `server_log.txt` para diagnóstico.
- Se o navegador não abrir em tela cheia, verifique se você tem o **Microsoft Edge** ou **Google Chrome** instalado.
