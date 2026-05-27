import os
from supabase import create_client
from groq import Groq
import requests

# Configurações de ambiente
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# 1. Buscar dados (igual ao atual)
try:
    response = supabase.table("leads_24h").select("*").execute()
    leads = response.data
except:
    leads = []

try:
    total_response = supabase.table("leads_essentia").select("*", count="exact").execute()
    total_leads = total_response.count
except:
    total_leads = "?"

dados_brutos = str(leads) if leads else "Nenhum lead novo."

# 2. Carregar prompts especializados (pasta prompts/)
def load_prompt(filename):
    with open(f"scripts/prompts/{filename}", "r") as f:
        return f.read()

prompt_estrategista = load_prompt("estrategista.txt")
prompt_redator = load_prompt("redator.txt")
prompt_designer = load_prompt("designer.txt")

# 3. Chamada ao Estrategista
user_estrategista = f"Dados dos leads:\n{dados_brutos}\nTotal na base: {total_leads}"
resp_estrategista = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"system","content":prompt_estrategista},
              {"role":"user","content":user_estrategista}],
    temperature=0.7, max_tokens=800
)
relatorio_estrategista = resp_estrategista.choices[0].message.content

# 4. Chamada ao Redator (usa saída do Estrategista como contexto)
user_redator = f"Relatório estratégico:\n{relatorio_estrategista}\n\nGere 3 legendas baseadas nesse insight."
resp_redator = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"system","content":prompt_redator},
              {"role":"user","content":user_redator}],
    temperature=0.8, max_tokens=1000
)
legendas = resp_redator.choices[0].message.content

# 5. Chamada ao Designer (usa saída do Redator como contexto)
user_designer = f"Legendas criadas:\n{legendas}\n\nGere um prompt de imagem ou storyboard visual para a primeira legenda."
resp_designer = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"system","content":prompt_designer},
              {"role":"user","content":user_designer}],
    temperature=0.7, max_tokens=500
)
visual = resp_designer.choices[0].message.content

# 6. Montar pack final
pack_final = f"""🧠 PACK CEREBRAL ESSENTIA

{relatorio_estrategista}

━━━━━━━━━━━━━━━
📝 VARIAÇÕES DE LEGENDA
{legendas}

━━━━━━━━━━━━━━━
🎨 DIREÇÃO VISUAL
{visual}
"""

# 7. Enviar para o Telegram
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {"chat_id": TELEGRAM_CHAT_ID, "text": pack_final}
response = requests.post(url, json=payload)
print("Pack multiagente enviado!")
print("Resposta do Telegram:", response.json())