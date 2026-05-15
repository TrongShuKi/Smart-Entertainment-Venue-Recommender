  /* ═══════════════════════════════════════════════════════════
     UTILITIES
  ═══════════════════════════════════════════════════════════ */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  function showToast(msg, type = 'error', duration = 3500) {
    const toast = $('#toast');
    $('#toast-icon').textContent = type === 'success' ? '✓' : '⚠';
    $('#toast-text').textContent = msg;
    toast.className = type === 'success' ? 'show success' : 'show';
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => { toast.className = ''; }, duration);
  }

  function smoothScrollTo(el) {
    if (!el) return;
    const y = el.getBoundingClientRect().top + window.scrollY - APP_STATE._navH;
    window.scrollTo({ top: y, behavior: 'smooth' });
  }

  // Favorites theo từng user (uid) — guest không lưu persistent
  function _favKey() {
    return APP_STATE.user?.uid ? 'st_fav_' + APP_STATE.user.uid : null;
  }
  function saveFavorites() {
    const key = _favKey();
    if (!key) return;
    try { localStorage.setItem(key, JSON.stringify(APP_STATE.favorites)); } catch(e) {}
  }
  function loadFavorites() {
    const key = _favKey();
    if (!key) { APP_STATE.favorites = []; return; }
    try {
      const raw = localStorage.getItem(key);
      APP_STATE.favorites = raw ? JSON.parse(raw) : [];
    } catch(e) { APP_STATE.favorites = []; }
  }

  // Weather icon map
  const WEATHER_ICONS = {
    CLEAR: '☀️', CLOUDS: '⛅', RAIN: '🌧️',
    DRIZZLE: '🌦️', STORM: '⛈️', MIST: '🌫️', SNOW: '❄️',
  };

  /* ═══════════════════════════════════════════════════════════
     NAV ACTIVE STATE (based on scroll)
  ═══════════════════════════════════════════════════════════ */
  function updateNavActive() {
    const sections = [
      { id: 'section-hero',      link: '[data-scroll="section-hero"]' },
      { id: 'section-discovery', link: '[data-scroll="section-discovery"]' },
      { id: 'section-decision',  link: '[data-scroll="section-decision"]' },
    ];
    const scrollY = window.scrollY + window.innerHeight / 3;
    let current = sections[0].link;
    sections.forEach(({ id, link }) => {
      const el = document.getElementById(id);
      if (el && el.style.display !== 'none' && el.offsetTop <= scrollY) current = link;
    });
    $$('.nav-links a').forEach(a => a.classList.remove('active'));
    const activeLink = $(current);
    if (activeLink) activeLink.classList.add('active');
  }

