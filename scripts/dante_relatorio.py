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
#    A view foi criada com:
#    CREATE OR REPLACE VIEW leads_24h AS
#    SELECT * FROM leads_essentia WHERE created_at > NOW() - INTERVAL '1 day';
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

3. ADAPTAÇÃO A DADOS ESCASSOS: Se não houver leads novos, não invente números. Gere um relatório motivacional com foco em sugestão de conteúdo para atrair leads e análise de sazonalidade.

4. PRIVACIDADE: Nunca mencione nomes completos, e-mails ou telefones dos leads. Agrupe apenas por padrões (ex: "a maioria veio do Instagram", ou "muitos perguntaram sobre segunda fermentação").

5. FORMATO: Texto puro, pronto para ser enviado via Telegram. Sem markdown complexo, apenas emojis e quebras de linha.
"""

user_message = f"""Analise os dados abaixo e gere o relatório matinal conforme seu System Prompt.

Dados dos leads nas últimas 24 horas:
{dados_brutos}

(NOTA: Cada objeto do array representa um lead. Use os campos disponíveis, como "mensagem", para identificar padrões ou intenções. Ignore dados pessoais como nome, email e whatsapp na resposta final.)"""

# ------------------------------------------------------------------
# 3. Chama a Groq (modelo gratuito Llama 3 8B)
# ------------------------------------------------------------------
completion = groq_client.chat.completions.create(
    model="llama3-8b-8192",  # gratuito, rápido e eficiente
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
