const SUPABASE_URL = "https://mimwktbuhkqxrvbqgjgq.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1pbXdrdGJ1aGtxeHJ2YnFnamdxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwODE0MzMsImV4cCI6MjA5NDY1NzQzM30.uk91bi71OMqkTZAlfO-DC-wlnT64JU2P71Czqhi5Eow";

document.getElementById('leadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btnSubmit = document.getElementById('btnSubmit');
    const responseMessage = document.getElementById('responseMessage');
    
    const nome = document.getElementById('nome').value;
    const email = document.getElementById('email').value;
    const whatsapp = document.getElementById('whatsapp').value;
    
    btnSubmit.innerText = "Enviando...";
    btnSubmit.disabled = true;

    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/leads_essentia`, {
            method: 'POST',
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`,
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            },
            body: JSON.stringify({ nome, email, whatsapp })
        });

        if (response.ok) {
            responseMessage.style.color = "#4CAF50";
            responseMessage.innerText = "🎉 Sucesso! Você está na lista VIP.";
            responseMessage.style.display = "block";
            document.getElementById('leadForm').reset();
        } else {
            throw new Error('Falha ao salvar no banco');
        }
    } catch (error) {
        responseMessage.style.color = "#ef4444";
        responseMessage.innerText = "❌ Erro ao enviar. Tente novamente mais tarde.";
        responseMessage.style.display = "block";
    } finally {
        btnSubmit.innerText = "Garantir Minha Vaga";
        btnSubmit.disabled = false;
    }
});