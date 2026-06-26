# ESSENTIA - Agent Actions

Este documento lista as ações que agentes de IA podem executar para interagir com a ESSENTIA.

## Ações Disponíveis

### 1. Listar Produtos
- **Ação:** Obter lista completa de produtos com preços, volumes e descrições.
- **Endpoint:** `GET https://www.essentiaoficial.com.br/brand.json`
- **Resposta:** JSON com todos os produtos e especificações.
- **Exemplo de Uso:** Um agente pode consultar esta API para recomendar um sabor específico a um usuário.
### 2. Obter Informações sobre Benefícios da Kombucha
- **Ação:** Acessar conteúdo educativo sobre benefícios percebidos da kombucha.
- **Endpoint:** `GET https://www.essentiaoficial.com.br/beneficios.html`
- **Resposta:** Página HTML com perguntas frequentes, respostas e FAQ Schema.
- **Exemplo de Uso:** Um agente pode consultar esta página para responder perguntas sobre benefícios da kombucha para seus usuários.
### 3. Inscrever na Lista VIP
- **Ação:** Cadastrar um lead na Lista VIP para receber notificações de novos lotes.
- **Endpoint:** `POST https://www.essentiaoficial.com.br/api/send-lead`
- **Corpo da Requisição (JSON):**
  ```json
  {
    "nome": "Nome do Cliente",
    "email": "email@exemplo.com",
    "whatsapp": "61999999999",
    "mensagem": "Preferência de sabor (opcional)",
    "source": "nome_do_agente"
  }
