const ALLOWED_ORIGIN = 'https://prohar2f-pixel.github.io';

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const corsHeaders = {
      'Access-Control-Allow-Origin': origin === ALLOWED_ORIGIN ? ALLOWED_ORIGIN : '',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    let data;
    try {
      data = await request.json();
    } catch {
      return new Response(JSON.stringify({ ok: false, error: 'bad json' }), { status: 400, headers: corsHeaders });
    }

    const { name, phone, email, service, comment } = data;

    if (!name || !phone) {
      return new Response(JSON.stringify({ ok: false, error: 'missing fields' }), { status: 400, headers: corsHeaders });
    }

    const escape = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const text = [
      '🛒 <b>Новая заявка с сайта!</b>',
      `👤 <b>Имя:</b> ${escape(name)}`,
      `📞 <b>Контакт:</b> ${escape(phone)}`,
      email ? `📧 <b>Email:</b> ${escape(email)}` : null,
      `💼 <b>Услуга:</b> ${escape(service)}`,
      comment ? `💬 <b>Комментарий:</b> ${escape(comment)}` : null,
    ].filter(Boolean).join('\n\n');

    try {
      const tgRes = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, parse_mode: 'HTML' }),
      });
      if (!tgRes.ok) {
        return new Response(JSON.stringify({ ok: false, error: 'telegram_error' }), { status: 502, headers: corsHeaders });
      }
      return new Response(JSON.stringify({ ok: true }), { headers: corsHeaders });
    } catch (err) {
      return new Response(JSON.stringify({ ok: false, error: 'network_error' }), { status: 500, headers: corsHeaders });
    }
  },
};
