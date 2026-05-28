import os
from supabase import create_client
from groq import Groq
import requests
import time

# ------------------------------------------------------------------
# Variáveis de ambiente
# ------------------------------------------------------------------
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
STABLE_HORDE_KEY = os.environ.get("STABLE_HORDE_KEY", "0000000000")  # anon key gratuita

# Inicializa clientes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# ------------------------------------------------------------------
# 1. Busca dados dos leads
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# 2. Carrega prompts especializados
# ------------------------------------------------------------------
def load_prompt(filename):
    with open(f"scripts/prompts/{filename}", "r") as f:
        return f.read()

prompt_estrategista = load_prompt("estrategista.txt")
prompt_redator = load_prompt("redator.txt")
prompt_designer = load_prompt("designer.txt")

# ------------------------------------------------------------------
# 3. Estrategista
# ------------------------------------------------------------------
user_estrategista = f"Dados dos leads:\n{dados_brutos}\nTotal na base: {total_leads}"
resp_estrategista = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"system","content":prompt_estrategista},
              {"role":"user","content":user_estrategista}],
    temperature=0.7, max_tokens=800
)
relatorio_estrategista = resp_estrategista.choices[0].message.content

# ------------------------------------------------------------------
# 4. Redator
# ------------------------------------------------------------------
user_redator = f"Relatório estratégico:\n{relatorio_estrategista}\n\nGere 3 legendas baseadas nesse insight."
resp_redator = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"system","content":prompt_redator},
              {"role":"user","content":user_redator}],
    temperature=0.8, max_tokens=1000
)
legendas = resp_redator.choices[0].message.content

# ------------------------------------------------------------------
# 5. Designer (prompt visual)
# ------------------------------------------------------------------
user_designer = f"Legendas criadas:\n{legendas}\n\nGere um prompt de imagem ou storyboard visual para a primeira legenda."
resp_designer = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role":"system","content":prompt_designer},
              {"role":"user","content":user_designer}],
    temperature=0.7, max_tokens=800
)
visual = resp_designer.choices[0].message.content

# ------------------------------------------------------------------
# 6. Gerador de Imagem (Stable Horde)
# ------------------------------------------------------------------
def extrair_prompt_imagem(texto_visual):
    """Extrai o prompt de imagem em inglês do bloco do Designer."""
    import re
    # Primeiro, tenta encontrar o bloco do DALL-E (geralmente em inglês)
    match = re.search(r'"(?:a|an|the)\s[\w\s,.\-()]+(?:photorealistic|lighting|rustic|ambient|atmosphere|wooden|bottle|natural)[\w\s,.\-()]*"', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        prompt = match.group(0).strip('"')
        print(f"Prompt extraído: {prompt}")
        return prompt
    print("Nenhum prompt em inglês encontrado.")
    return None

prompt_imagem = extrair_prompt_imagem(visual)

if prompt_imagem:
    print(f"Gerando imagem com prompt: {prompt_imagem[:100]}...")
    
    horde_payload = {
        "prompt": prompt_imagem + ", natural lighting, earthy tones, photorealistic, high quality",
        "params": {"width": 512, "height": 512, "steps": 20, "n": 1}
    }
    headers = {"apikey": STABLE_HORDE_KEY}
    
    try:
        horde_response = requests.post(
            "https://stablehorde.net/api/v2/generate/text2img",
            json=horde_payload,
            headers=headers,
            timeout=30
        )
        print(f"Status code: {horde_response.status_code}")
        print(f"Resposta bruta: {horde_response.text[:200]}")
        
        if horde_response.status_code == 202:
            task_id = horde_response.json()["id"]
            print(f"Task ID: {task_id}. Aguardando geração...")
            
            image_url = None
            tentativas = 0
            while not image_url and tentativas < 36:
                time.sleep(5)
                status_resp = requests.get(f"https://stablehorde.net/api/v2/generate/status/{task_id}")
                data = status_resp.json()
                if data.get("done"):
                    image_url = data["generations"][0]["img"]
                    break
                tentativas += 1
            
            if image_url:
                print("Imagem gerada com sucesso!")
                img_data = requests.get(image_url).content
                
                primeira_legenda = legendas.split("**Opção")[1].split("**Opção")[0] if "**Opção" in legendas else legendas
                caption = f"🔥 IMAGEM DO POST\n\n{primeira_legenda[:500]}"
                
                telegram_photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                files = {"photo": ("post_essentia.png", img_data)}
                photo_response = requests.post(
                    telegram_photo_url,
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                    files=files
                )
                print("Imagem enviada:", photo_response.json())
            else:
                print("Timeout na geração da imagem. O pack de texto será enviado normalmente.")
        else:
            print(f"Erro na Stable Horde (status {horde_response.status_code}): {horde_response.text}")
    except Exception as e:
        print(f"Erro na geração de imagem: {e}. O pack de texto será enviado normalmente.")
else:
    print("Nenhum prompt de imagem encontrado. Seguindo com o pack de texto.")
# ------------------------------------------------------------------
# 7. Monta e envia o pack de texto
# ------------------------------------------------------------------
pack_final = f"""🧠 PACK CEREBRAL ESSENTIA

{relatorio_estrategista}

━━━━━━━━━━━━━━━
📝 VARIAÇÕES DE LEGENDA
{legendas}

━━━━━━━━━━━━━━━
🎨 DIREÇÃO VISUAL
{visual}
"""

def enviar_mensagem_longa(chat_id, texto, bot_token):
    max_chars = 4000
    partes = []
    while len(texto) > max_chars:
        split_point = texto.rfind('\n', 0, max_chars)
        if split_point == -1:
            split_point = max_chars
        partes.append(texto[:split_point])
        texto = texto[split_point:].lstrip('\n')
    partes.append(texto)
    
    for i, parte in enumerate(partes):
        prefixo = f"[Parte {i+1}/{len(partes)}]\n\n" if len(partes) > 1 else ""
        payload = {"chat_id": chat_id, "text": prefixo + parte}
        resp = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json=payload)
        print(f"Parte {i+1} enviada:", resp.json())

enviar_mensagem_longa(TELEGRAM_CHAT_ID, pack_final, TELEGRAM_BOT_TOKEN)
print("Pack v3.0 enviado com sucesso!")
