  /* ═══════════════════════════════════════════════════════════
     SEARCH HANDLER
  ═══════════════════════════════════════════════════════════ */
  const Search = {
    async run(query) {
      if (!query.trim()) return;

      const btn = $('#search-btn');
      const input = $('#main-search-input');

      // Loading state
      btn.classList.add('loading');
      input.disabled = true;
      APP_STATE.lastQuery = query;

      try {
        // Get user location (with fallback to HCMC)
        const loc = await this._getLocation();
        APP_STATE.lastLocation = loc;

        const data = await API.suggest(query, loc);

        this.handleSuccess(data);

      } catch (err) {
        console.error('[Search]', err);
        showToast(err.message || 'Không kết nối được server. Kiểm tra backend đang chạy chưa?');
      } finally {
        btn.classList.remove('loading');
        input.disabled = false;
      }
    },

    handleSuccess(data) {
      // Cập nhật State
      APP_STATE.results       = data;
      APP_STATE.places        = data.top_places || [];
      APP_STATE.weather       = data.weather_info || null;
      APP_STATE.contextSummary = data.user_context_summary || '';
      APP_STATE.activePlaceIndex = 0;

      if (APP_STATE.places.length === 0) {
        showToast('Không tìm thấy địa điểm phù hợp. Thử mô tả khác nhé!');
        return;
      }

      // Update weather badge & UI
      this._updateWeatherBadge(data.weather_info);
      this._revealResults();
    },

    async _getLocation() {
      return new Promise((resolve) => {
        if (!navigator.geolocation) { resolve(APP_STATE.lastLocation); return; }
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
          ()    => resolve(APP_STATE.lastLocation),
          { timeout: 4000 }
        );
      });
    },

    _updateWeatherBadge(w) {
      if (!w) return;
      const badge = $('#hero-weather-badge');
      $('#hero-weather-icon').textContent = WEATHER_ICONS[w.condition] || '🌡️';
      $('#hero-weather-temp').textContent = `${Math.round(w.temperature)}°C`;
      $('#hero-weather-desc').textContent = w.condition_vi || w.condition;
      badge.classList.add('visible');
    },

    _revealResults() {
      const disc = $('#section-discovery');
      const dec  = $('#section-decision');

      disc.classList.add('revealed');
      dec.classList.add('revealed');
      APP_STATE.resultsRevealed = true;

      // Hide scroll cue
      $('#hero-scroll-cue').style.opacity = '0';

      // Trigger Part 2 render (will be defined in Part 2)
      if (typeof Discovery !== 'undefined') Discovery.render(APP_STATE.places, APP_STATE.weather);
      if (typeof DecisionHub !== 'undefined') DecisionHub.render(APP_STATE.places, APP_STATE.weather, APP_STATE.lastLocation);

      // Smooth scroll to Tầng 2
      setTimeout(() => smoothScrollTo(disc), 100);
    },
  };

  // ── Lắng nghe sự kiện khôi phục từ lịch sử (history.js) ──
  document.addEventListener('restoreHistory', (e) => {
    if (e.detail && typeof Search !== 'undefined') {
      Search.handleSuccess(e.detail);
    }
  });

  
