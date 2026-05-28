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
    temperature=0.8, max_tokens=1200
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
    temperature=0.7, max_tokens=900
)
visual = resp_designer.choices[0].message.content

# ------------------------------------------------------------------
# 6. Gerador de Imagem (Stable Horde)
# ------------------------------------------------------------------
# 1. Tenta o formato obrigatório: IMAGEM: texto
    match = re.search(r'IMAGEM:\s*(.+)', texto_visual, re.IGNORECASE)
    if match:
        prompt = match.group(1).strip()
        # Remove asteriscos que possam ter vindo do markdown
        prompt = prompt.strip('*').strip()
        if prompt:
            print(f"Prompt extraído via IMAGEM: {prompt}")
            return prompt
    # 2. Fallback: bloco ```prompt (caso o Designer ignore a instrução)
    match = re.search(r'```prompt\s*\n(.*?)\n```', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        prompt = match.group(1).strip()
        print(f"Prompt extraído via bloco: {prompt}")
        return prompt
    # 3. Último fallback: qualquer frase em inglês com palavra-chave visual
    match = re.search(r'(?:a|an|the)\s[\w\s,.\-()]{30,}(?:photorealistic|rustic|wooden|bottle|natural|lighting|kombucha)[\w\s,.\-()]*', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        prompt = match.group(0).strip()
        print(f"Prompt extraído via fallback: {prompt}")
        return prompt
    print("Nenhum prompt em inglês encontrado.")
    return None

# 6. Gerador de Imagem (Pollinations.ai)
def gerar_imagem_pollinations(prompt, width=1024, height=1024, model="flux"):
    """
    Gera uma imagem usando a API gratuita da Pollinations.ai.
    Não requer chave de API, cadastro ou polling.
    Retorna os bytes da imagem ou None em caso de erro.
    """
    from urllib.parse import quote
    encoded_prompt = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={model}&width={width}&height={height}&nologo=true"
    
    print(f"Gerando imagem com Pollinations.ai: {prompt[:100]}...")
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            print("Imagem gerada com sucesso!")
            return response.content
        else:
            print(f"Erro na Pollinations.ai (status {response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Erro na geração de imagem: {e}")
        return None

# --- Fluxo de geração da imagem ---
prompt_imagem = extrair_prompt_imagem(visual)

if prompt_imagem:
    img_data = gerar_imagem_pollinations(prompt_imagem)
    
    if img_data:
        primeira_legenda = legendas.split("**Opção")[1].split("**Opção")[0] if "**Opção" in legendas else legendas
        caption = f"🔥 IMAGEM DO POST\n\n{primeira_legenda[:500]}"
        
        telegram_photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files = {"photo": ("post_essentia.png", img_data)}
        photo_response = requests.post(
            telegram_photo_url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files=files
        )
        print("Imagem enviada para o Telegram:", photo_response.json())
    else:
        print("A geração da imagem falhou. O pack de texto será enviado normalmente.")
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
