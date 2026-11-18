// Progress sync for the revision site. Stores one JSON blob per 16-character code in Workers KV.
// GET /p/<CODE>  -> the saved blob (404 if none)    PUT /p/<CODE>  -> save it (max 200 KB)
const ORIGINS = ['https://haffi-khalid.github.io', 'http://localhost:8765'];
const CODE = /^[A-HJ-NP-Z2-9]{16}$/;
const count = (j) => { try { const r = JSON.parse(j).r; return r ? String(r).split(',').length : 0; } catch (e) { return 0; } };
export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin');
    const cors = {
      'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Vary': 'Origin',
    };
    const res = (body, status = 200) => new Response(body, { status, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const m = new URL(req.url).pathname.match(/^\/p\/([A-Z0-9]+)$/);
    if (!m || !CODE.test(m[1])) return res('{"error":"bad code"}', 400);
    if (req.method === 'GET') {
      // Return the fullest saved snapshot, so a Reset never loses what was saved before it.
      const [a, b] = await Promise.all([env.PROGRESS.get(m[1]), env.PROGRESS.get(m[1] + ':bak')]);
      const v = b !== null && (a === null || count(b) > count(a)) ? b : a;
      return v === null ? res('{"error":"not found"}', 404) : res(v);
    }
    if (req.method === 'PUT') {
      const body = await req.text();
      if (body.length > 200000) return res('{"error":"too big"}', 413);
      try { JSON.parse(body); } catch (e) { return res('{"error":"bad json"}', 400); }
      const old = await env.PROGRESS.get(m[1]);
      if (old !== null && count(old) > count(body)) {
        const bak = await env.PROGRESS.get(m[1] + ':bak');
        if (bak === null || count(bak) < count(old)) await env.PROGRESS.put(m[1] + ':bak', old);
      }
      await env.PROGRESS.put(m[1], body);
      return res('{"ok":true}');
    }
    return res('{"error":"method"}', 405);
  },
};
