/* ═══════════════════════════════════════════════════════════
   DETAIL MODAL — Phần 3
  ═══════════════════════════════════════════════════════════ */
  var DetailModal = {
    _miniMap: null,
    _currentPlace: null,
    _MEDALS: ['🥇', '🥈', '🥉'],

    open(indexOrPlace) {
      // Chấp nhận cả index (từ Discovery) lẫn place object (từ SidePanel/Favorites)
      let place, index;

      if (typeof indexOrPlace === 'number') {
        // Gọi từ Discovery/DecisionHub — dùng index vào APP_STATE.places
        index = indexOrPlace;
        place = APP_STATE.places[index];
      } else if (indexOrPlace && typeof indexOrPlace === 'object') {
        // Gọi từ SidePanel — place object truyền trực tiếp
        place = indexOrPlace;
        // Tìm index trong APP_STATE.places để lấy medal đúng (nếu có)
        index = APP_STATE.places.findIndex(p => String(p.id) === String(place.id));
        if (index === -1) index = 0; // fallback: dùng medal 🥇 nếu không tìm thấy
      }

      if (!place) return;
      this._currentPlace = place;

      this._populate(place, index);
      document.getElementById('detail-modal').classList.add('open');
      document.body.style.overflow = 'hidden';

      // Init mini-map after modal visible
      setTimeout(() => this._initMiniMap(place), 120);

      // Keyboard close
      document.addEventListener('keydown', this._onKey);
    },

    close() {
      document.getElementById('detail-modal').classList.remove('open');
      document.body.style.overflow = '';
      document.removeEventListener('keydown', this._onKey);

      // Destroy mini-map so it re-inits cleanly next time
      if (this._miniMap) {
        this._miniMap.remove();
        this._miniMap = null;
      }
    },

    _onKey(e) { if (e.key === 'Escape') DetailModal.close(); },

    _populate(place, index) {
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };

      // Image strip
      const img = document.getElementById('detail-img');
      if (img) {
        img.src = place.image_url && place.image_url.startsWith('http')
          ? place.image_url
          : `https://picsum.photos/seed/${place.id || index}/600/900`;
        img.alt = place.name;
      }
      set('detail-img-rank', this._MEDALS[index] || '');

      // Header
      set('detail-category-text', place.category || 'Địa điểm');
      set('detail-title', place.name || '');

      // Stars
      const r = place.rating || 0;
      const starsEl = document.getElementById('detail-stars');
      if (starsEl) {
        const full = Math.round(r);
        starsEl.textContent = '★'.repeat(full) + '☆'.repeat(Math.max(0, 5 - full));
      }
      set('detail-rating', `${Number(r).toFixed(1)}/5`);
      set('detail-distance', place.distance != null ? `${Number(place.distance).toFixed(1)} km từ bạn` : '--');

      // Description & Fact
      set('detail-desc', place.description || `Địa điểm ${place.category || ''} nổi bật tại TP.HCM.`);
      set('detail-fact', place.fact || 'Hãy đến tận nơi để cảm nhận không khí thực sự của địa điểm này.');

      // Info rows
      const priceEl = document.getElementById('detail-price-row');
      if (priceEl) {
        if (place.price === 0) {
          priceEl.textContent = 'Miễn phí';
          priceEl.className = 'detail-info-value free';
        } else {
          priceEl.textContent = `${Number(place.price).toLocaleString('vi-VN')}đ`;
          priceEl.className = 'detail-info-value';
        }
      }
      set('detail-tag-row', place.tag || place.category || '--');

      // Google Maps link
      const mapsBtn = document.getElementById('detail-btn-maps');
      if (mapsBtn && place.latitude && place.longitude) {
        mapsBtn.href = `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`;
      }

      // Save button state
      this._updateSaveBtn(place.id);
    },

    _initMiniMap(place) {
      // Clear old container content
      const container = document.getElementById('detail-mini-map');
      if (!container) return;

      // Re-create container to avoid Leaflet "already initialized" error
      container.innerHTML = '';
      container._leaflet_id = null;

      const lat = place.latitude || 10.7769;
      const lon = place.longitude || 106.7009;

      this._miniMap = L.map('detail-mini-map', {
        center: [lat, lon],
        zoom: 15,
        zoomControl: false,
        attributionControl: false,
        dragging: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        touchZoom: false,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
      }).addTo(this._miniMap);

      // Custom pin marker
      const icon = L.divIcon({
        html: `<div style="
          width:28px;height:28px;border-radius:50%;
          background:var(--accent);
          border:3px solid #fff;
          box-shadow:0 4px 12px rgba(0,0,0,0.4);
          display:flex;align-items:center;justify-content:center;
          font-size:13px;
        ">📍</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        className: '',
      });

      L.marker([lat, lon], { icon })
        .addTo(this._miniMap)
        .bindPopup(`<b>${place.name}</b>`, { closeButton: false })
        .openPopup();

      // User location marker (if available)
      const [uLat, uLon] = APP_STATE.lastLocation;
      if (uLat && uLon) {
        const userIcon = L.divIcon({
          html: `<div style="
            width:14px;height:14px;border-radius:50%;
            background:#4a9eff;border:2px solid #fff;
            box-shadow:0 2px 8px rgba(74,158,255,0.5);
          "></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7],
          className: '',
        });
        L.marker([uLat, uLon], { icon: userIcon }).addTo(this._miniMap);

        // Draw line user → place
        L.polyline([[uLat, uLon], [lat, lon]], {
          color: '#4a9eff',
          weight: 2,
          opacity: 0.5,
          dashArray: '5 6',
        }).addTo(this._miniMap);

        // Fit bounds to show both
        this._miniMap.fitBounds([[uLat, uLon], [lat, lon]], { padding: [24, 24] });
      }
    },

    _updateSaveBtn(placeId) {
      const btn = document.getElementById('detail-btn-save');
      if (!btn) return;
      const faved = Favorites.has(placeId);
      btn.classList.toggle('active', faved);
    },

    _bindEvents() {
      // Close button
      document.getElementById('detail-close')?.addEventListener('click', () => this.close());
      document.getElementById('detail-backdrop')?.addEventListener('click', () => this.close());

      // Save button
      document.getElementById('detail-btn-save')?.addEventListener('click', () => {
        if (!this._currentPlace) return;
        if (APP_STATE.isGuest) {
          this.close();
          AuthModal.open('login');
          showToast('Đăng nhập để lưu yêu thích ❤️');
          return;
        }
        Favorites.add(this._currentPlace);
        this._updateSaveBtn(this._currentPlace.id);
      });
    },

    init() {
      this._bindEvents();
    },
  };