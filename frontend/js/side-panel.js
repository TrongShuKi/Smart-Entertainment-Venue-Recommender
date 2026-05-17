  /* ═══════════════════════════════════════════════════════════
     SIDE PANEL
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

      if (APP_STATE.favorites.length === 0) {
        body.innerHTML = `
          <div class="side-panel-empty">
            <div class="side-panel-empty-icon">♡</div>
            <div class="side-panel-empty-text">Chưa có địa điểm yêu thích</div>
            ${APP_STATE.isGuest ? `<span class="side-panel-login-cta" id="sp-login-cta">Đăng nhập để lưu →</span>` : ''}
          </div>`;
        const cta = $('#sp-login-cta');
        if (cta) cta.addEventListener('click', () => { this.close(); AuthModal.open(); });
        return;
      }

      body.innerHTML = APP_STATE.favorites.map((place, i) => `
        <div class="fav-item" data-index="${i}" data-id="${place.id}">
          <img class="fav-thumb" src="${place.image_url || ''}" alt="${place.name}"
               onerror="this.style.background='#1a1d22';this.removeAttribute('src')" />
          <div class="fav-info">
            <div class="fav-name">${place.name}</div>
            <div class="fav-cat">${place.category || ''} · ${place.distance?.toFixed(1) || '?'} km</div>
          </div>
          <button class="fav-remove" data-id="${place.id}" title="Xóa">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>`).join('');

          // Events
          body.querySelectorAll('.fav-item').forEach(el => {
              el.addEventListener('click', (e) => {
                  if (e.target.closest('.fav-remove')) {
                      e.stopPropagation();
                      Favorites.remove(el.dataset.id);
                  } else {
                      const rawId = String(el.dataset.id);
                      const place = APP_STATE.favorites.find(f => String(f.id) === rawId);

                      this.close();

                      if (place && typeof DetailModal !== 'undefined') {
                          DetailModal.open(place);
                      } else {
                          console.error("Không tìm thấy địa điểm hoặc DetailModal chưa load.");
                      }
                  }
              });
          });

          // Update badge
          const badge = $('#fav-badge');
          if (badge) {
              badge.textContent = APP_STATE.favorites.length;
              badge.classList.toggle('visible', APP_STATE.favorites.length > 0);
          }
      },
  };