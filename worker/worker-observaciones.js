/**
 * Cloudflare Worker - Observaciones de la app "Base de Datos KFC".
 * Guarda las observaciones que escribe Fabiola para que Alejandro las vea y las borre.
 *
 * Necesita (se configura una sola vez en Cloudflare):
 *   - KV namespace enlazado con el nombre de variable:  OBS
 *   - Secret:  ADMIN_PIN   (el PIN que solo conoce Alejandro; sirve para borrar)
 */
const APP_KEY = 'pNU717Phq0XT2xYZiA_Dy2b7';
const ORIGENES = ['https://alejosl0801.github.io', 'http://127.0.0.1:8765', 'http://localhost:8765'];
const MAX_TEXTO = 1500, MAX_ITEMS = 600;

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ORIGENES.includes(origin) ? origin : ORIGENES[0],
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Vary': 'Origin',
    };
    const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    const url = new URL(req.url);

    if (req.method === 'GET') {
      if (url.searchParams.get('k') !== APP_KEY) return json({ error: 'no autorizado' }, 403);
      const lista = await env.OBS.list({ prefix: 'o:' });
      const items = {};
      await Promise.all(lista.keys.map(async (k) => {
        const v = await env.OBS.get(k.name, 'json');
        if (v) items[k.name.slice(2)] = v;
      }));
      return json({ items });
    }

    if (req.method === 'POST') {
      let b;
      try { b = await req.json(); } catch (e) { return json({ error: 'json' }, 400); }
      if (b.k !== APP_KEY) return json({ error: 'no autorizado' }, 403);
      const id = String(b.id || '');
      if (!/^[A-Za-z0-9 _.\-]{1,90}$/.test(id)) return json({ error: 'id' }, 400);

      if (b.action === 'put') {
        const texto = String(b.text || '').slice(0, MAX_TEXTO);
        if (!texto.trim()) { await env.OBS.delete('o:' + id); return json({ ok: true, borrada: true }); }
        const lista = await env.OBS.list({ prefix: 'o:' });
        if (lista.keys.length >= MAX_ITEMS && !lista.keys.some((k) => k.name === 'o:' + id)) return json({ error: 'lleno' }, 429);
        await env.OBS.put('o:' + id, JSON.stringify({ t: texto, d: new Date().toISOString() }));
        return json({ ok: true });
      }
      if (b.action === 'del') {
        if (!env.ADMIN_PIN || b.pin !== env.ADMIN_PIN) return json({ error: 'pin' }, 403);
        await env.OBS.delete('o:' + id);
        return json({ ok: true });
      }
      return json({ error: 'accion' }, 400);
    }
    return json({ error: 'metodo' }, 405);
  },
};
