  /* ═══════════════════════════════════════════════════════════
     EVENT BINDINGS — Part 1
  ═══════════════════════════════════════════════════════════ */
  document.addEventListener('DOMContentLoaded', () => {
    // Compute nav height for offset calculations
    APP_STATE._navH = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) || 64;

    // Restore session (loadFavorites được gọi bên trong restoreSession/login)
    Auth.restoreSession();
    DetailModal.init();
    SidePanel.render();

    // ── Search
    const searchInput = $('#main-search-input');
    const searchBtn   = $('#search-btn');

    searchBtn.addEventListener('click', () => Search.run(searchInput.value));
    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') Search.run(searchInput.value);
    });

    // Quick chips
    $$('.hero-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        searchInput.value = chip.dataset.query;
        Search.run(chip.dataset.query);
      });
    });

    // ── Navbar: brand click → scroll to top
    $('#nav-brand').addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ── Navbar: search icon → scroll to hero & focus input
    $('#nav-search-btn').addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(() => searchInput.focus(), 500);
    });

    // ── Navbar: smooth scroll links
    $$('[data-scroll]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById(link.dataset.scroll);
        if (target && target.classList.contains('revealed') || link.dataset.scroll === 'section-hero') {
          smoothScrollTo(target || document.getElementById('section-hero'));
        }
      });
    });

    // ── Navbar: favorites
    $('#nav-fav-btn').addEventListener('click', () => SidePanel.toggle());
    $('#close-side-panel').addEventListener('click', () => SidePanel.close());

    // ── Navbar: login button (guest)
    $('#nav-login-btn').addEventListener('click', () => AuthModal.open('login'));

    // ── Navbar: user dropdown
    const navUserBtn = document.getElementById('nav-user-btn');
    if (navUserBtn) {
      navUserBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        document.getElementById('user-dropdown')?.classList.toggle('open');
      });
    }
    document.addEventListener('click', (e) => {
      const wrap = $('#nav-user-wrap');
      if (wrap && !wrap.contains(e.target)) {
        $('#user-dropdown')?.classList.remove('open');
      }
    });

    // ── Dropdown items
    $('#dd-logout')?.addEventListener('click', () => Auth.logout());
    $('#dd-favorites')?.addEventListener('click', () => {
      $('#user-dropdown').classList.remove('open');
      SidePanel.open();
    });
    $('#dd-history')?.addEventListener('click', () => {
      $('#user-dropdown').classList.remove('open');
      if (!APP_STATE.user) { AuthModal.open('login'); return; }
      HistoryModal.open();
    });

    // ── History Modal
    document.getElementById('history-modal-close')?.addEventListener('click', () => HistoryModal.close());
    document.getElementById('history-backdrop')?.addEventListener('click', () => HistoryModal.close());

    // ── Auth Modal
    $('#nav-guest-tag').addEventListener('click', () => AuthModal.open('login'));
    $('#auth-modal-close').addEventListener('click', () => AuthModal.close());
    $('#auth-backdrop').addEventListener('click', () => AuthModal.close());
    $('#continue-as-guest').addEventListener('click', () => AuthModal.close());

    $$('.auth-tab').forEach(tab => {
      tab.addEventListener('click', () => AuthModal.switchTab(tab.dataset.tab));
    });

    $('#login-submit').addEventListener('click',  () => AuthModal.submitLogin());
    $('#signup-submit').addEventListener('click', () => AuthModal.submitSignup());

    // Enter key in forms
    ['login-email', 'login-password'].forEach(id => {
      $(`#${id}`)?.addEventListener('keydown', e => { if(e.key === 'Enter') AuthModal.submitLogin(); });
    });
    ['signup-email', 'signup-password'].forEach(id => {
      $(`#${id}`)?.addEventListener('keydown', e => { if(e.key === 'Enter') AuthModal.submitSignup(); });
    });

    // ── Google OAuth — Popup flow ──────────────────────────────────────────
    // Trang cha lắng nghe postMessage từ popup
    window.addEventListener('message', (e) => {
      if (e.data?.type !== 'GOOGLE_AUTH_SUCCESS') return;
      const token = e.data.idToken;
      if (!token) return;
      // Verify với backend rồi login
      API.post('/auth/google', { id_token: token })
        .then(data => {
          Auth.login({ uid: data.uid, email: data.email, idToken: data.idToken });
          AuthModal.close();
        })
        .catch(() => showToast('Đăng nhập Google thất bại. Thử lại nhé!'));
    });

    ['#google-login-btn', '#google-signup-btn'].forEach(sel => {
      $(sel)?.addEventListener('click', () => {
        const url = `${APP_STATE.API_BASE}/auth/google/start`;
        const w = 500, h = 640;
        const left = Math.round((screen.width  - w) / 2);
        const top  = Math.round((screen.height - h) / 2);
        window.open(
          url, 'google_oauth',
          `width=${w},height=${h},left=${left},top=${top},` +
          `toolbar=no,menubar=no,location=no,status=no,scrollbars=yes`
        );
      });
    });

    // ── Nếu trang này CHÍNH LÀ popup (frontend_url trỏ vào đây) ──────────
    // Khi backend redirect về: http://localhost:8080/?id_token=xxx
    // Popup nhận URL → gửi token về trang cha → tự đóng
    (function handlePopupCallback() {
      const params = new URLSearchParams(window.location.search);
      const token  = params.get('id_token');
      if (!token) return; // Không phải callback, bỏ qua

      // Xóa token khỏi URL để tránh lộ khi refresh
      window.history.replaceState({}, '', window.location.pathname);

      if (window.opener && !window.opener.closed) {
        // Gửi token về trang cha
        window.opener.postMessage({ type: 'GOOGLE_AUTH_SUCCESS', idToken: token }, '*');
        // Đóng popup sau 300ms (chờ postMessage gửi xong)
        setTimeout(() => window.close(), 300);
      } else {
        // Fallback: popup bị mở thành tab mới, tự xử lý login luôn
        API.post('/auth/google', { id_token: token })
          .then(data => {
            Auth.login({ uid: data.uid, email: data.email, idToken: data.idToken });
            AuthModal.close();
          })
          .catch(() => showToast('Đăng nhập Google thất bại'));
      }
    })();

    // ── Scroll events
    window.addEventListener('scroll', updateNavActive, { passive: true });
    updateNavActive();

    // ── Fetch weather on load (background, no block)
    fetch(`${APP_STATE.API_BASE}/weather/current?lat=10.7769&lon=106.7009`)
      .then(r => r.json())
      .then(w => {
        $('#hero-weather-icon').textContent = WEATHER_ICONS[w.condition] || '🌡️';
        $('#hero-weather-temp').textContent = `${Math.round(w.temperature)}°C`;
        $('#hero-weather-desc').textContent = w.condition_vi || w.condition;
        $('#hero-weather-badge').classList.add('visible');
      })
      .catch(() => {
        // Silent fail — weather badge stays hidden
      });
  });

