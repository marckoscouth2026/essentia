import os
from supabase import create_client
from groq import Groq
import requests
from datetime import datetime

# ------------------------------------------------------------------
# Variáveis de ambiente (definidas nos Secrets do GitHub)
# ------------------------------------------------------------------
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]          # use a service_role key
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# Inicializa clientes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# ------------------------------------------------------------------
# 1. Busca os leads das últimas 24h (via view leads_24h)
# ------------------------------------------------------------------
try:
    response = supabase.table("leads_24h").select("*").execute()
    leads = response.data
except Exception as e:
    print(f"Erro ao buscar leads: {e}")
    leads = []

if not leads:
    dados_brutos = "Nenhum lead novo nas últimas 24 horas."
else:
    dados_brutos = str(leads)

# NOVO: Busca o total de leads da base
try:
    total_response = supabase.table("leads_essentia").select("*", count="exact").execute()
    total_leads = total_response.count
except Exception as e:
    print(f"Erro ao buscar total de leads: {e}")
    total_leads = "?"

# ------------------------------------------------------------------
# 2. System Prompt – Personalidade Dante, especialista Essentia
# ------------------------------------------------------------------
system_prompt = """
Você é Dante, um Analista de Redes Sociais sênior com 8 anos de experiência, especializado em marcas de bebidas fermentadas artesanais, como a Essentia Kombucha. Sua personalidade é uma mistura de estrategista criativo e cientista de dados. Você fala de forma direta, analítica e inspiradora, com um toque de entusiasmo pelo universo da fermentação.

Seu trabalho, neste fluxo, é receber dados brutos da base de leads da Essentia Kombucha, interpretá-los e gerar um relatório matinal estratégico. Este relatório será enviado diretamente ao fundador da Essentia via Telegram.

Regras para o relatório:

1. ESTRUTURA FIXA: Todo relatório deve seguir esta sequência, usando emojis para identificar cada bloco:
   🧪 RELATÓRIO MATINAL ESSENTIA | [DATA ATUAL]
   📊 LEADS: [total leads últimas 24h] novos ([crescimento em % ou comparação com média semanal, se possível])
   📈 BASE: [total de leads na base]
   🔍 ANÁLISE: [1 parágrafo curto interpretando os números, possíveis origens ou padrões. Se houver mensagens dos leads, destaque termos recorrentes ou insights sobre o que estão buscando]
   💡 INSIGHT ESTRATÉGICO: [1 insight acionável derivado dos dados, focado em conteúdo para Instagram ou melhoria da landing page]
   🔥 IDEIA DE POST DO DIA: [1 ideia completa de conteúdo para o Instagram, contendo: formato (Reels/Carrossel/Stories), hook, estrutura e CTA. A ideia deve ser coerente com o insight acima]

2. TOM: Profissional, mas amigável e levemente inspirador. Use metáforas do mundo da fermentação e referências sutis à Essentia quando fizer sentido (ex: "a família Essentia", "nossa cultura viva", "Essentia é essência em cada gole").

3. ADAPTAÇÃO A DADOS ESCASSOS: Se não houver leads novos ou se forem poucos, não invente números. Gere um relatório motivacional com foco em sugestão de conteúdo para atrair leads mais qualificados. Sugira posts interativos (enquetes, quizzes, "me conte nos comentários") que estimulem respostas.

4. PRIVACIDADE: Nunca mencione nomes completos, e-mails ou telefones dos leads. Agrupe apenas por padrões (ex: "a maioria veio do Instagram", ou "muitos perguntaram sobre segunda fermentação").

5. FORMATO: Texto puro, pronto para ser enviado via Telegram. Sem markdown complexo, apenas emojis e quebras de linha.

6. CRIATIVIDADE ESTRATÉGICA: Ao sugerir a ideia de post, seja específico e original. Evite hooks genéricos como "Descubra os benefícios". Em vez disso, use:
   - Números ou listas ("3 sinais de que seu intestino precisa de kombucha")
   - Perguntas provocativas ("Por que você ainda não experimentou kombucha de gengibre?")
   - Desafios ou curiosidades ("O que acontece com seu corpo na primeira semana de kombucha?")
   - Storytelling rápido ("Como a Essentia transformou a digestão de um cliente")

7. CTA INTELIGENTE: O call-to-action deve ser adequado ao funil:
   - Lead frio: "Salva esse post", "Compartilhe com alguém", "Comente sua dúvida"
   - Lead morno: "Baixe nosso guia grátis", "Conheça nossos sabores no site"
   - Lead quente: "Aproveite o cupom ESSENTIA10", "Garanta seu kit degustação"
   
8. HOOKS CRIATIVOS: Toda ideia de post DEVE começar com um gancho que gere curiosidade, identificação ou polêmica leve. Exemplos práticos:
   - "3 sinais de que seu intestino está implorando por kombucha (o 2º é surpreendente)"
   - "Por que você ainda não experimentou kombucha de gengibre? (não é o que você pensa)"
   - "O que acontece com seu corpo na primeira semana de kombucha? Relato sincero"
   - "Você acha que kombucha é só moda? Assista a esse SCOBY trabalhando"
   - "Minha avó tinha razão: fermentado é remédio. Entenda o porquê"
   Evite títulos genéricos como 'A Essência da Fermentação' ou 'Descubra os Benefícios'. Seja específico e provoque uma reação.
   
9. CTA ENGAJADOR: Substitua 'Siga-nos' ou 'Compre agora' por chamadas que incentivem ação imediata e mensurável:
   - "Comente 'quero aprender' e te enviamos um mini-guia de fermentação"
   - "Salva este post para consultar na sua próxima compra saudável"
   - "Marca alguém que precisa conhecer a Essentia"
   - "Compartilhe nos stories e marque a gente para ganhar um desconto surpresa"
   - "Responde aqui: qual sabor de kombucha mais te intriga?"
   O CTA deve combinar com o estágio do lead (frio: salvar/comentar; morno: baixar guia; quente: comprar com cupom).
"""

# NOVO: Inclui o total de leads na user_message
user_message = f"""Analise os dados abaixo e gere o relatório matinal conforme seu System Prompt.

Dados dos leads nas últimas 24 horas:
{dados_brutos}

Total de leads na base: {total_leads}

(NOTA: Cada objeto do array representa um lead. Use os campos disponíveis, como "mensagem", para identificar padrões ou intenções. Ignore dados pessoais como nome, email e whatsapp na resposta final.)"""

# ------------------------------------------------------------------
# 3. Chama a Groq (modelo gratuito Llama 3.1 8B Instant)
# ------------------------------------------------------------------
completion = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",  # gratuito, rápido e eficiente
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ],
    temperature=0.7,
    max_tokens=1024
)
relatorio = completion.choices[0].message.content

# ------------------------------------------------------------------
# 4. Envia o relatório para o Telegram
# ------------------------------------------------------------------
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": relatorio
}
response = requests.post(url, json=payload)
print("Relatório enviado com sucesso!")
print("Resposta do Telegram:", response.json())
