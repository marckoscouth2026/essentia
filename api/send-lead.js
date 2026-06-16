// api/send-lead.js
export default async function handler(req, res) {
  // Aceita apenas POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método não permitido' });
  }

  try {
    const { nome, email, whatsapp, mensagem, source } = req.body;

    // Token do Bot (agora seguro, vindo do ambiente da Vercel)
    const tokenBot = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = '@essentia_alertas'; // ou use o ID numérico do canal

    if (!tokenBot) {
      throw new Error('Token do Telegram não configurado no ambiente');
    }

    const whatsappLimpo = whatsapp.replace(/\D/g, '');
    
    const textoAlerta = `🍇 *NOVO LEAD!* \n\n` +
      `👤 *Nome:* ${nome}\n` +
      `✉️ *E-mail:* ${email}\n` +
      `📱 *WhatsApp:* ${whatsapp}\n` +
      `💬 *Mensagem:* ${mensagem || '—'}\n` +
      `📍 *Origem:* ${source}\n` +
      `👉 *WhatsApp:* https://wa.me/55${whatsappLimpo}`;

    // Envia para o Telegram
    const response = await fetch(`https://api.telegram.org/bot${tokenBot}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: textoAlerta,
        parse_mode: 'Markdown'
      })
    });

    const data = await response.json();

    if (!data.ok) {
      throw new Error('Falha ao enviar mensagem para o Telegram');
    }

    // Retorna sucesso
    res.status(200).json({ success: true });

  } catch (error) {
    console.error('Erro no webhook:', error);
    res.status(500).json({ error: 'Erro ao processar lead' });
  }
}
