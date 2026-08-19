import os
from supabase import create_client
import requests
import time
import re
import json

# ------------------------------------------------------------------
# Variáveis de ambiente
# ------------------------------------------------------------------
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

# Inicializa Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------------------------
# Função de geração de texto via Gemini (Google AI Studio)
# ------------------------------------------------------------------
def gerar_texto_gemini(system_prompt, user_message, temperature=0.7, max_tokens=800):
    """Gera texto usando o modelo Gemini 3.6 Flash (gratuito e estável)."""
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY não configurada. Pulando geração de texto.")
        return ""

    # Modelo atualizado conforme sugestão da API
    model = "models/gemini-3.6-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt + "\n\n" + user_message}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }

    print(f"Gerando texto com Gemini (temp={temperature}, max_tokens={max_tokens})...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
               if response.status_code == 200:
            data = response.json()
            try:
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        texto = parts[0].get("text", "")
                        if texto:
                            return texto
                # Se não encontrou texto, loga a resposta completa para diagnóstico
                print("Gemini retornou 200 mas sem texto. Resposta completa:")
                print(json.dumps(data, indent=2)[:500])
                return ""
            except Exception as e:
                print(f"Erro ao extrair texto do Gemini: {e}")
                return ""
        else:
            print(f"Erro no Gemini (status {response.status_code}): {response.text[:200]}")
            return ""


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

if not relatorio_estrategista:
    from datetime import datetime
    data_atual = datetime.now().strftime("%d/%m/%Y")
    relatorio_estrategista = f"""🧪 RELATÓRIO MATINAL ESSENTIA | {data_atual}

⚠️ O Google Gemini não retornou uma análise hoje. Possível bloqueio de segurança ou problema temporário.

📊 LEADS: {len(leads)} novo(s)
📈 BASE: {total_leads} leads na base

💡 INSIGHT ESTRATÉGICO (fallback):
Vamos criar um post interativo perguntando aos seguidores: 'Qual sabor de kombucha mais representa a sua essência?'
"""


# ------------------------------------------------------------------
# 4. Redator
# ------------------------------------------------------------------
user_redator = f"Relatório estratégico:\n{relatorio_estrategista}\n\nGere 3 legendas baseadas nesse insight."

legendas = gerar_texto_gemini(
    prompt_redator,
    user_redator,
    temperature=0.8,
    max_tokens=1200
)


# ------------------------------------------------------------------
# 5. Designer (prompt visual)
# ------------------------------------------------------------------
user_designer = f"Legendas criadas:\n{legendas}\n\nGere um prompt de imagem ou storyboard visual para a primeira legenda."

visual = gerar_texto_gemini(
    prompt_designer,
    user_designer,
    temperature=0.7,
    max_tokens=900
)


# ------------------------------------------------------------------
# 6. Gerador de Imagem (Hugging Face)
# ------------------------------------------------------------------
def extrair_prompt_imagem(texto_visual):
    """Extrai o prompt de imagem do bloco do Designer."""
    match = re.search(r'IMAGEM:\s*(.+)', texto_visual, re.IGNORECASE)
    if match:
        prompt = match.group(1).strip().strip('*').strip()
        if prompt:
            print(f"Prompt extraído via IMAGEM: {prompt}")
            return prompt
    match = re.search(r'```prompt\s*\n(.*?)\n```', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        prompt = match.group(1).strip()
        print(f"Prompt extraído via bloco: {prompt}")
        return prompt
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
    """Gera imagem via Hugging Face (Stable Diffusion)."""
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


prompt_imagem = extrair_prompt_imagem(visual)

if prompt_imagem:
    img_data = gerar_imagem_huggingface(prompt_imagem)
    if img_data:
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
