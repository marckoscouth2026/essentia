#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime, timezone
from supabase import create_client, Client
from groq import Groq
import requests

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S UTC"
)
logger = logging.getLogger(__name__)

def load_env_vars():
    """Carrega e valida variáveis de ambiente."""
    required = ["SUPABASE_URL", "SUPABASE_KEY", "GROQ_API_KEY", 
                "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    for var in required:
        if not os.getenv(var):
            logger.error(f"Variável de ambiente ausente: {var}")
            sys.exit(1)

def fetch_data(supabase: Client):
    """Exemplo: Busca dados do Supabase."""
    try:
        response = supabase.table("leads_24h").select("*").limit(50).execute()
        logger.info(f"Dados coletados: {len(response.data)} registros")
        return response.data
    except Exception as e:
        logger.error(f"Falha ao buscar dados: {e}")
        raise

def generate_report_with_groq(data, groq_client: Groq) -> str:
    """Gera relatório usando a IA."""
    prompt = f"Resuma os seguintes dados em formato de relatório matinal:\n{str(data)}"
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Falha na geração com Groq: {e}")
        raise

def send_to_telegram(message: str):
    """Envia o relatório para o Telegram."""
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "parse_mode": "HTML",
        "text": f"📊 <b>Relatório Matinal - {datetime.now(timezone.utc).strftime('%d/%m/%Y')}</b>\n\n{message}"
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    logger.info("Relatório enviado com sucesso para o Telegram.")

def main():
    load_env_vars()
    logger.info("Iniciando pipeline do Dante...")
    
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    data = fetch_data(supabase)
    report = generate_report_with_groq(data, groq_client)
    send_to_telegram(report)
    
    logger.info("Pipeline finalizado com sucesso.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Erro fatal no script: {e}")
        sys.exit(1)  # Retorna código 1 → dispara o step `if: failure()` do GitHub Actions
