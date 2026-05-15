  /* ═══════════════════════════════════════════════════════════
     API CLIENT — mirrors api_client.py
  ═══════════════════════════════════════════════════════════ */
  const API = {
    base: APP_STATE.API_BASE,

    headers(withAuth = false) {
      const h = { 'Content-Type': 'application/json' };
      if (withAuth && APP_STATE.user?.idToken) {
        h['Authorization'] = `Bearer ${APP_STATE.user.idToken}`;
      }
      return h;
    },

    async post(path, body, auth = false) {
      const res = await fetch(this.base + path, {
        method: 'POST',
        headers: this.headers(auth),
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return res.json();
    },

    async get(path, params = {}, auth = false) {
      const url = new URL(this.base + path);
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
      const res = await fetch(url, { headers: this.headers(auth) });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return res.json();
    },

    async login(email, password) {
      return this.post('/auth/login', { email, password });
    },

    async signup(email, password) {
      return this.post('/auth/signup', { email, password });
    },

    async suggest(query, location) {
      return this.post('/suggest', { query, location }, !!APP_STATE.user);
    },

    async history(limit = 5) {
      return this.get('/suggest/history', { limit }, true);
    },

    async health() {
      return this.get('/health');
    },
  };

