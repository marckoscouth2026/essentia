import os
from supabase import create_client
from groq import Groq
import requests
import time
import re

# ------------------------------------------------------------------
# Variáveis de ambiente
# ------------------------------------------------------------------
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
HF_API_KEY = os.environ.get("HF_API_KEY")

# Inicializa clientes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# ------------------------------------------------------------------
# 1. Busca dados dos leads
# ------------------------------------------------------------------
def buscar_leads():
    try:
        response = supabase.table("leads_24h").select("*").execute()
        return response.data
    except Exception:
        return []


def buscar_total_leads():
    try:
        response = supabase.table("leads_essentia").select("*", count="exact").execute()
        return response.count
    except Exception:
        return "?"


leads = buscar_leads()
total_leads = buscar_total_leads()
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
    messages=[
        {"role": "system", "content": prompt_estrategista},
        {"role": "user", "content": user_estrategista}
    ],
    temperature=0.7,
    max_tokens=800
)
relatorio_estrategista = resp_estrategista.choices[0].message.content


# ------------------------------------------------------------------
# 4. Redator
# ------------------------------------------------------------------
user_redator = f"Relatório estratégico:\n{relatorio_estrategista}\n\nGere 3 legendas baseadas nesse insight."
resp_redator = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": prompt_redator},
        {"role": "user", "content": user_redator}
    ],
    temperature=0.8,
    max_tokens=1200
)
legendas = resp_redator.choices[0].message.content


# ------------------------------------------------------------------
# 5. Designer (prompt visual)
# ------------------------------------------------------------------
user_designer = f"Legendas criadas:\n{legendas}\n\nGere um prompt de imagem ou storyboard visual para a primeira legenda."
resp_designer = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": prompt_designer},
        {"role": "user", "content": user_designer}
    ],
    temperature=0.7,
    max_tokens=900
)
visual = resp_designer.choices[0].message.content


# ------------------------------------------------------------------
# 6. Gerador de Imagem (Hugging Face)
# ------------------------------------------------------------------
def extrair_prompt_imagem(texto_visual):
    """Extrai o prompt de imagem do bloco do Designer."""
    # 1. IMAGEM: texto
    match = re.search(r'IMAGEM:\s*(.+)', texto_visual, re.IGNORECASE)
    if match:
        prompt = match.group(1).strip().strip('*').strip()
        if prompt:
            print(f"Prompt extraído via IMAGEM: {prompt}")
            return prompt
    # 2. Bloco ```prompt
    match = re.search(r'```prompt\s*\n(.*?)\n```', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        prompt = match.group(1).strip()
        print(f"Prompt extraído via bloco: {prompt}")
        return prompt
    # 3. Fallback em inglês
    match = re.search(
        r'(?:a|an|the)\s[\w\s,.\-()]{30,}(?:photorealistic|rustic|wooden|bottle|natural|lighting|kombucha)[\w\s,.\-()]*',
        texto_visual,
        re.DOTALL | re.IGNORECASE
    )
    if match:
        prompt = match.group(0).strip()
        print(f"Prompt extraído via fallback: {prompt}")
        return prompt
    print("Nenhum prompt em inglês encontrado.")
    return None


def gerar_imagem_huggingface(prompt, width=1024, height=1024):
    """Gera imagem via Hugging Face (Stable Diffusion) — gratuito e estável."""
    if not HF_API_KEY:
        print("HF_API_KEY não configurada. Pulando geração de imagem.")
        return None

    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt, "parameters": {"width": width, "height": height}}

    print(f"Gerando imagem com Hugging Face: {prompt[:80]}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            print("Imagem gerada com sucesso!")
            return response.content
        else:
            print(f"Erro no Hugging Face (status {response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Erro na geração com Hugging Face: {e}")
        return None


# --- Fluxo de geração da imagem ---
prompt_imagem = extrair_prompt_imagem(visual)

if prompt_imagem:
    img_data = gerar_imagem_huggingface(prompt_imagem)
    if img_data:
        # Extrai primeira legenda
        if "**Opção" in legendas:
            primeira_legenda = legendas.split("**Opção")[1].split("**Opção")[0]
        else:
            primeira_legenda = legendas
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
        print("Falha ao gerar imagem. Seguindo com o pack de texto.")
else:
    print("Nenhum prompt de imagem encontrado. Seguindo com o pack de texto.")


# ------------------------------------------------------------------
# 7. Envia o pack de texto
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