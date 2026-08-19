import os
from supabase import create_client
import requests
import time
import re
import json
from datetime import datetime

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def gerar_texto_gemini(system_prompt, user_message, temperature=0.7, max_tokens=800):
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY não configurada. Pulando geração de texto.")
        return ""

    model = "models/gemini-3.6-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_message}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
    }

    for tentativa in range(1, 4):
        print(f"Tentativa {tentativa}/3 - Gerando texto com Gemini...")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    print(f"Erro ao extrair texto: {e}")
                    return ""
            elif response.status_code in [503, 429]:
                print(f"Erro {response.status_code} (demanda). Aguardando 20s...")
                time.sleep(20)
            else:
                print(f"Erro no Gemini (status {response.status_code}): {response.text[:200]}")
                return ""
        except Exception as e:
            print(f"Erro de conexão: {e}. Aguardando 10s...")
            time.sleep(10)
    print("Todas as tentativas falharam. Retornando vazio.")
    return ""

try:
    leads = supabase.table("leads_24h").select("*").execute().data
except Exception:
    leads = []
try:
    total_leads = supabase.table("leads_essentia").select("*", count="exact").execute().count
except Exception:
    total_leads = "?"

dados_brutos = str(leads) if leads else "Nenhum lead novo."
dados_brutos = dados_brutos.replace("cerveja", "bebida similar").replace("Cerveja", "Bebida similar")

def load_prompt(filename):
    with open(f"scripts/prompts/{filename}", "r") as f:
        return f.read()

prompt_estrategista = load_prompt("estrategista.txt")
prompt_redator = load_prompt("redator.txt")
prompt_designer = load_prompt("designer.txt")

user_estrategista = f"Dados dos leads:\n{dados_brutos}\nTotal na base: {total_leads}"
relatorio_estrategista = gerar_texto_gemini(prompt_estrategista, user_estrategista, 0.7, 1500)

if not relatorio_estrategista:
    data_atual = datetime.now().strftime("%d/%m/%Y")
    relatorio_estrategista = f"""🧪 RELATÓRIO MATINAL ESSENTIA | {data_atual}
⚠️ O Google Gemini não retornou uma análise hoje. Possível bloqueio de segurança ou problema temporário.
📊 LEADS: {len(leads)} novo(s)
📈 BASE: {total_leads} leads na base
💡 INSIGHT ESTRATÉGICO (fallback): Vamos criar um post interativo perguntando aos seguidores: 'Qual sabor de kombucha mais representa a sua essência?'"""

user_redator = f"Relatório estratégico:\n{relatorio_estrategista}\n\nGere 3 legendas baseadas nesse insight."
legendas = gerar_texto_gemini(prompt_redator, user_redator, 0.8, 1500)

if not legendas:
    legendas = """**Opção 1**
Descubra os sabores únicos da Essentia e como eles podem transformar seu dia. #EssentiaKombucha

**Opção 2**
Feita com cultura viva e ingredientes naturais, a Essentia é mais que uma bebida: é um estilo de vida saudável. #KombuchaArtesanal

**Opção 3**
Qual sabor da Essentia mais combina com você? Comente abaixo e compartilhe sua experiência! #ComunidadeEssentia"""

user_designer = f"Legendas criadas:\n{legendas}\n\nGere um prompt de imagem ou storyboard visual para a primeira legenda."
visual = gerar_texto_gemini(prompt_designer, user_designer, 0.7, 1200)

if not visual or "IMAGEM:" not in visual:
    visual = "IMAGEM: A modern minimalist product shot of a sleek glass bottle of artisanal kombucha with a clean, contemporary label, placed on a smooth light grey surface, with fresh fruit slices and mint leaves arranged elegantly around the base, bright but soft studio lighting, subtle reflections, airy and high-end aesthetic, high resolution."

def extrair_prompt_imagem(texto_visual):
    match = re.search(r'IMAGEM:\s*(.+)', texto_visual, re.IGNORECASE)
    if match:
        return match.group(1).strip().strip('*').strip()
    match = re.search(r'```prompt\s*\n(.*?)\n```', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'(?:a|an|the)\s[\w\s,.\-()]{30,}(?:photorealistic|rustic|wooden|bottle|natural|lighting|kombucha)[\w\s,.\-()]*', texto_visual, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return None

prompt_imagem = extrair_prompt_imagem(visual)

if prompt_imagem and HF_API_KEY:
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt_imagem, "parameters": {"width": 1024, "height": 1024}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        if r.status_code == 200:
            img_data = r.content
            if "**Opção" in legendas:
                primeira_legenda = legendas.split("**Opção")[1].split("**Opção")[0]
            else:
                primeira_legenda = legendas
            caption = f"🔥 IMAGEM DO POST\n\n{primeira_legenda[:500]}"
            files = {"photo": ("post_essentia.png", img_data)}
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                files=files
            )
    except Exception as e:
        print(f"Erro ao gerar imagem: {e}")

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
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": prefixo + parte}
        )

enviar_mensagem_longa(TELEGRAM_CHAT_ID, pack_final, TELEGRAM_BOT_TOKEN)
print("Pack v3.0 enviado com sucesso!")
