/* ═══════════════════════════════════════════════════════════
     SIDE PANEL — Yêu thích
     - Chỉ hiển thị danh sách khi đã đăng nhập
     - Click item → mở DetailModal (chấp nhận place object)
     - Badge luôn đồng bộ, kể cả khi logout
  ═══════════════════════════════════════════════════════════ */
  const SidePanel = {
    open() {
      $('#side-panel').classList.add('open');
      this.render();
    },
    close() {
      $('#side-panel').classList.remove('open');
    },
    toggle() {
      if ($('#side-panel').classList.contains('open')) this.close();
      else this.open();
    },

    render() {
      const body = $('#side-panel-body');
      if (!body) return;

      // ── Badge: luôn update trước, kể cả khi list rỗng ──
      this._updateBadge();

      // ── Empty / Guest states ──
      if (APP_STATE.isGuest) {
        body.innerHTML = `
          <div class="side-panel-empty">
            <div class="side-panel-empty-icon">🔒</div>
            <div class="side-panel-empty-text">Đăng nhập để lưu địa điểm yêu thích</div>
            <span class="side-panel-login-cta" id="sp-login-cta">Đăng nhập ngay →</span>
          </div>`;
        document.getElementById('sp-login-cta')
          ?.addEventListener('click', () => { this.close(); AuthModal.open('login'); });
        return;
      }

      if (APP_STATE.favorites.length === 0) {
        body.innerHTML = `
          <div class="side-panel-empty">
            <div class="side-panel-empty-icon">♡</div>
            <div class="side-panel-empty-text">Chưa có địa điểm yêu thích</div>
            <span style="font-size:12px;color:var(--text-dim);font-family:var(--font-mono);">
              Bấm ❤ trên địa điểm để lưu
            </span>
          </div>`;
        return;
      }

      // ── Render danh sách ──
      body.innerHTML = APP_STATE.favorites.map((place, i) => `
        <div class="fav-item" data-id="${place.id}">
          <img class="fav-thumb"
               src="${place.image_url && place.image_url.startsWith('http') ? place.image_url : ''}"
               alt="${place.name}"
               onerror="this.style.background='#1a1d22';this.removeAttribute('src')" />
          <div class="fav-info">
            <div class="fav-name">${place.name}</div>
            <div class="fav-cat">
              ${place.category || ''}
              ${place.distance != null ? ' · ' + Number(place.distance).toFixed(1) + ' km' : ''}
            </div>
          </div>
          <button class="fav-remove" data-id="${place.id}" title="Xóa khỏi yêu thích">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>`).join('');

      // ── Events ──
      body.querySelectorAll('.fav-item').forEach(el => {
        el.addEventListener('click', (e) => {
          // Nút xóa
          if (e.target.closest('.fav-remove')) {
            e.stopPropagation();
            const id = el.dataset.id;
            Favorites.remove(id);
            return;
          }

          // Click vào item → mở Detail Modal
          const rawId = String(el.dataset.id);
          const place = APP_STATE.favorites.find(f => String(f.id) === rawId);
          if (!place) return;

          this.close();

          if (typeof DetailModal !== 'undefined') {
            // Truyền place object trực tiếp (DetailModal.open đã được fix để nhận cả 2 dạng)
            DetailModal.open(place);
          }
        });
      });
    },

    _updateBadge() {
      const badge = $('#fav-badge');
      if (!badge) return;
      const count = APP_STATE.isGuest ? 0 : APP_STATE.favorites.length;
      badge.textContent = count;
      badge.classList.toggle('visible', count > 0);
    },
  };