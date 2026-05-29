# 🌿 Essentia — Histórico de Versões

**Projeto:** Essentia Kombucha  
**Objetivo:** Construir a primeira marca de bebidas fermentadas data-driven do Brasil.  
**Mantenedor:** Marckos  
**Arquiteto da IA:** Dante (agente estratégico)

---

## v3.0 — Integração Visual (29/05/2026)
**Destaques:**
- 🧠 Sistema multiagente completo: Estrategista, Redator, Designer e Gerador de Imagens.
- 🎨 Geração automática de imagens via Pollinations.ai (API gratuita, sem chave).
- ⏰ Agendamento externo consolidado com cron‑job.org (webhook `dante-cron`).
- ✅ Notificações de sucesso e falha no Telegram ao final de cada execução.
- 🔍 Extrator de prompt visual com fallbacks (IMAGEM:, bloco ```prompt, regex em inglês).
- 🔒 Privacidade reforçada e prompts visuais em inglês para melhor qualidade.

**Limitações conhecidas:**
- A qualidade da imagem ainda pode variar; o prompt às vezes carrega ruídos de formatação.
- Dependência de modelos gratuitos da Groq (sujeitos a descontinuação) exige monitoramento.

---

## v2.1 — Pergunte à Essentia (27/05/2026)
**Destaques:**
- 🧪 Nova série semanal: "Pergunte à Essentia", respondendo dúvidas reais dos leads.
- 🎥 Dante Estrategista agora sugere roteiros de Reels baseados nas perguntas dos clientes.
- 📝 Formulário da landing page atualizado para capturar a maior dúvida sobre kombucha.
- 🔁 Ciclo completo: Lead pergunta → Dante analisa → Conteúdo é criado → Mais leads perguntam.

---

## v2.0 — Cérebro Multiagente (26/05/2026)
**Destaques:**
- 🧠 Dante dividido em três especialistas: Estrategista, Redator e Designer.
- 📦 Entrega do "Pack Cerebral" completo via Telegram: análise, 3 legendas e direção visual.
- 🤖 Orquestração automática com GitHub Actions + Groq (modelo gratuito).
- 🔒 Privacidade reforçada: dados pessoais nunca são expostos nos relatórios.

---

## v1.0 — Dante Solo (25/05/2026)
**Destaques:**
- 📊 Primeiro relatório matinal automático com análise de leads.
- 🔥 Ideia de post diário baseada em dados reais do Supabase.
- 🕘 Agendamento diário via GitHub Actions.
- 💬 Envio do relatório diretamente no Telegram pessoal.

---

## v0.1 — Cultura Mãe (24/05/2026)
**Destaques:**
- 🌐 Landing page no ar: www.essentiaoficial.com.br.
- 🗄️ Integração com Supabase: formulário de leads armazenando nome, e-mail, WhatsApp e mensagem.
- 🤖 Bot do Telegram notificando cada novo lead no canal "ESSENTIA - Alertas".

---

## 📅 Roadmap (futuro)

| Versão | Nome           | Descrição breve                                              |
|--------|----------------|--------------------------------------------------------------|
| v3.1   | Refinamento Visual | Ajuste fino do prompt de imagem e testes com novos modelos |
| v4.0   | Clube do SCOBY | Assinatura mensal curada pelo Dante + grupo VIP               |
| v5.0   | Essentia IA    | Atendimento automático no Telegram respondendo dúvidas sobre kombucha |

---

> *"A Essentia não é apenas uma bebida. É um organismo vivo que escuta, aprende e fermenta estratégias."*