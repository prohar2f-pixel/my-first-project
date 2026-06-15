export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json',
    };

    let data;
    try {
      data = await request.json();
    } catch {
      return new Response(JSON.stringify({ ok: false, error: 'bad json' }), { status: 400, headers: cors });
    }

    const { name, phone, email, service, comment } = data;
    const text = [
      '🛒 <b>Новая заявка с сайта!</b>',
      `👤 <b>Имя:</b> ${name}`,
      `📞 <b>Контакт:</b> ${phone}`,
      email ? `📧 <b>Email:</b> ${email}` : null,
      `💼 <b>Услуга:</b> ${service}`,
      comment ? `💬 <b>Комментарий:</b> ${comment}` : null,
    ].filter(Boolean).join('\n\n');

    try {
      await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, parse_mode: 'HTML' }),
      });
      return new Response(JSON.stringify({ ok: true }), { headers: cors });
    } catch (err) {
      return new Response(JSON.stringify({ ok: false }), { status: 500, headers: cors });
    }
  },
};
