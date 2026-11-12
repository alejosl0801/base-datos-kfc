/**
 * Cloudflare Worker - Observaciones de la app "Base de Datos KFC".
 * Necesita un KV namespace enlazado con el nombre de variable: OBS
 * El PIN de administrador no se guarda aqui: solo su huella SHA-256.
 */
const APP_KEY = 'pNU717Phq0XT2xYZiA_Dy2b7';
const ORIGENES = ['https://alejosl0801.github.io', 'http://127.0.0.1:8765', 'http://localhost:8765'];
const PIN_SHA256 = '2d674a12c9e2eeb3fc357c1338a0762d20b50dab8cd089cb4185a48dcb769fab';
const MAX_TEXTO = 1500, MAX_ITEMS = 600, MAX_POR_MIN = 60;
const ID_OK = /^(ACC_)?([A-Z]{1,3}\d{1,3}|PENDIENTE - [A-Z0-9 ]{1,60})$/;
const golpes = new Map();
function limitado(ip) {
  const k = ip + ':' + Math.floor(Date.now() / 60000);
  const n = (golpes.get(k) || 0) + 1;
  golpes.set(k, n);
  if (golpes.size > 5000) golpes.clear();
  return n > MAX_POR_MIN;
}

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
    if (!ORIGENES.includes(origin)) return json({ error: 'origen no permitido' }, 403);
    if (limitado(req.headers.get('CF-Connecting-IP') || 'x')) return json({ error: 'demasiadas solicitudes' }, 429);
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
      if (!ID_OK.test(id)) return json({ error: 'id' }, 400);

      if (b.action === 'put') {
        const texto = String(b.text || '').slice(0, MAX_TEXTO);
        if (!texto.trim()) { await env.OBS.delete('o:' + id); return json({ ok: true, borrada: true }); }
        const cur = await env.OBS.get('o:' + id, 'json');
        if (cur && cur.t !== texto && b.base !== cur.d) return json({ error: 'conflicto', cur }, 409);
        if (!cur) {
          const lista = await env.OBS.list({ prefix: 'o:' });
          if (lista.keys.length >= MAX_ITEMS) return json({ error: 'lleno' }, 429);
        }
        const d = new Date().toISOString();
        await env.OBS.put('o:' + id, JSON.stringify({ t: texto, d }));
        return json({ ok: true, d });
      }
      if (b.action === 'del') {
        const dig = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(String(b.pin || '')));
        const hex = [...new Uint8Array(dig)].map((x) => x.toString(16).padStart(2, '0')).join('');
        if (hex !== PIN_SHA256) return json({ error: 'pin' }, 403);
        await env.OBS.delete('o:' + id);
        return json({ ok: true });
      }
      return json({ error: 'accion' }, 400);
    }
    return json({ error: 'metodo' }, 405);
  },
};
