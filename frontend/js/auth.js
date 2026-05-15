  /* ═══════════════════════════════════════════════════════════
     AUTH MANAGER
  ═══════════════════════════════════════════════════════════ */
  const Auth = {
    login(userData) {
      APP_STATE.user = userData;
      APP_STATE.isGuest = false;
      loadFavorites();            // load favorites của user này từ localStorage
      this._updateUI();
      this._persistSession(userData);
      showToast(`Chào mừng, ${userData.email}!`, 'success');
    },

    logout() {
      APP_STATE.user = null;
      APP_STATE.isGuest = true;
      APP_STATE.favorites = [];   // xóa favorites khỏi state khi logout
      this._updateUI();
      localStorage.removeItem('st_session');
      showToast('Đã đăng xuất', 'success', 2000);
    },

    _persistSession(data) {
      try { localStorage.setItem('st_session', JSON.stringify(data)); } catch(e) {}
    },

    restoreSession() {
      try {
        const raw = localStorage.getItem('st_session');
        if (raw) {
          const data = JSON.parse(raw);
          if (data?.idToken) {
            APP_STATE.user = data;
            APP_STATE.isGuest = false;
            loadFavorites();      // load favorites của user này
            this._updateUI();
            return true;
          }
        }
      } catch(e) {}
      return false;
    },

    _updateUI() {
      const loggedIn = !APP_STATE.isGuest;

      // Guest elements — chỉ hiện khi chưa đăng nhập
      const guestEls = ['nav-guest-tag', 'nav-login-btn'];
      guestEls.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = loggedIn ? 'none' : '';
      });

      // Logged-in elements — chỉ hiện khi đã đăng nhập
      const userWrap = document.getElementById('nav-user-wrap');
      if (userWrap) userWrap.style.display = loggedIn ? 'block' : 'none';

      if (loggedIn && APP_STATE.user) {
        const emailEl = document.getElementById('dropdown-email');
        const nameEl  = document.getElementById('dropdown-name');
        if (emailEl) emailEl.textContent = APP_STATE.user.email || '';
        if (nameEl)  nameEl.textContent  = (APP_STATE.user.email || '').split('@')[0];
      }

      // Update side panel
      SidePanel.render();
    },
  };

  /* ═══════════════════════════════════════════════════════════
     AUTH MODAL
  ═══════════════════════════════════════════════════════════ */
  const AuthModal = {
    _tab: 'login',

    open(tab = 'login') {
      this.switchTab(tab);
      $('#auth-modal').classList.add('open');
      setTimeout(() => document.addEventListener('keydown', this._onKey), 50);
    },
    close() {
      $('#auth-modal').classList.remove('open');
      document.removeEventListener('keydown', this._onKey);
      ['login-error', 'signup-error'].forEach(id => { const el = $(`#${id}`); if(el) el.textContent = ''; });
    },
    _onKey(e) { if (e.key === 'Escape') AuthModal.close(); },

    switchTab(tab) {
      this._tab = tab;
      $$('.auth-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
      });
      $('#auth-form-login').style.display  = tab === 'login'  ? 'block' : 'none';
      $('#auth-form-signup').style.display = tab === 'signup' ? 'block' : 'none';
    },

    async submitLogin() {
      const email = $('#login-email').value.trim();
      const pwd   = $('#login-password').value;
      const errEl = $('#login-error');

      if (!email || !pwd) {
        errEl.textContent = '⚠ Vui lòng nhập đầy đủ thông tin';
        return;
      }

      const btn = $('#login-submit');
      const origText = btn.textContent;
      btn.textContent = 'Đang đăng nhập...';
      btn.disabled = true;
      btn.style.opacity = '0.7';
      errEl.textContent = '';

      try {
        const data = await API.login(email, pwd);
        Auth.login({ uid: data.uid, email: data.email, idToken: data.idToken });
        this.close();
      } catch(err) {
        errEl.textContent = '✕ Sai email hoặc mật khẩu. Thử lại nhé!';
        // Shake animation
        const box = btn.closest('.modal-box');
        if (box) { box.style.animation = 'shake 0.3s ease'; setTimeout(() => box.style.animation = '', 300); }
      } finally {
        btn.textContent = origText;
        btn.disabled = false;
        btn.style.opacity = '';
      }
    },

    async submitSignup() {
      const email = $('#signup-email').value.trim();
      const pwd   = $('#signup-password').value;
      const errEl = $('#signup-error');

      if (!email || !pwd) {
        errEl.textContent = '⚠ Vui lòng nhập đầy đủ thông tin';
        return;
      }
      if (pwd.length < 6) {
        errEl.textContent = '⚠ Mật khẩu phải có ít nhất 6 ký tự';
        return;
      }
      if (!email.includes('@')) {
        errEl.textContent = '⚠ Email không hợp lệ';
        return;
      }

      const btn = $('#signup-submit');
      const origText = btn.textContent;
      btn.textContent = 'Đang tạo tài khoản...';
      btn.disabled = true;
      btn.style.opacity = '0.7';
      errEl.textContent = '';

      try {
        await API.signup(email, pwd);
        showToast('Tạo tài khoản thành công! Đang đăng nhập...', 'success');
        const data = await API.login(email, pwd);
        Auth.login({ uid: data.uid, email: data.email, idToken: data.idToken });
        this.close();
      } catch(err) {
        errEl.textContent = '✕ ' + (err.message || 'Tạo tài khoản thất bại. Email có thể đã tồn tại.');
      } finally {
        btn.textContent = origText;
        btn.disabled = false;
        btn.style.opacity = '';
      }
    },
  };

