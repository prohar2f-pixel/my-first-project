export default async function handler(req, res) {
  const { code } = req.query;

  const r = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({
      client_id: process.env.GITHUB_CLIENT_ID,
      client_secret: process.env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });

  const { access_token } = await r.json();

  res.setHeader('Content-Type', 'text/html');
  res.end(`<!DOCTYPE html><html><body><script>
(function() {
  var token = ${JSON.stringify(access_token)};
  var msg = 'authorization:github:success:' + JSON.stringify({ token: token, provider: 'github' });
  function receiveMessage(e) { window.opener.postMessage(msg, e.origin); }
  window.addEventListener('message', receiveMessage, false);
  window.opener.postMessage('authorizing:github', '*');
})();
<\/script></body></html>`);
}
