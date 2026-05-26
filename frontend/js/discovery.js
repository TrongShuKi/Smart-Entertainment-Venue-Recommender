  /* ═══════════════════════════════════════════════════════════
     PART 2 — DISCOVERY SECTION
     Full Swiper slider + focus panel + animated transitions
  ═══════════════════════════════════════════════════════════ */
  var Discovery = {
    _swiper: null,
    _places: [],
    _bgA: null,
    _bgB: null,
    _bgActive: 'a',   // which bg div is currently visible

    /* ── Main entry: called by Search._revealResults() ── */
    render(places, weather) {
      if (!places || places.length === 0) return;
      this._places = places;

      const sec = document.getElementById('section-discovery');
      sec.innerHTML = this._buildHTML(places);

      // Cache bg refs
      this._bgA = document.getElementById('disc-bg-a');
      this._bgB = document.getElementById('disc-bg-b');

      // Init Swiper
      this._initSwiper(places);

      // Bind buttons
      this._bindEvents();

      // Initial focus
      setTimeout(() => this._setFocus(0, false), 120);
    },

    /* ── HTML builder ── */
    _buildHTML(places) {
      const MEDALS = ['🥇', '🥈', '🥉'];

      const cards = places.map((p, i) => `
        <div class="swiper-slide disc-slide" data-index="${i}">
          <img
            src="${p.image_url && p.image_url.startsWith('http') ? p.image_url : `https://picsum.photos/seed/${p.id || i}/600/900`}"
            alt="${p.name}"
            loading="lazy"
            onerror="this.src='https://picsum.photos/seed/${(p.id||i)+'x'}/600/900'"
          />
          <div class="disc-card-overlay">
            <div class="disc-card-category">${p.category || ''}</div>
            <div class="disc-card-name">${p.name}</div>
          </div>
          <div class="disc-rank-medal">${MEDALS[i] || ''}</div>
        </div>`).join('');

      const ctxHtml = APP_STATE.contextSummary ? `
        <div class="disc-context-bar">
          <div class="disc-context-dot"></div>
          Kết quả cho: <strong>${APP_STATE.contextSummary}</strong>
        </div>` : '';

      return `
        <!-- Crossfade backgrounds -->
        <div class="disc-bg" id="disc-bg-a" style="opacity:1;"></div>
        <div class="disc-bg" id="disc-bg-b" style="opacity:0;"></div>
        <div class="disc-overlay"></div>

        ${ctxHtml}

        <div class="disc-layout">

          <!-- ── LEFT: Focus panel ── -->
          <div class="disc-left">

            <div class="disc-anim disc-distance-badge" id="disc-distance">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <circle cx="12" cy="10" r="3"/>
                <path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"/>
              </svg>
              <span id="disc-dist-val">--</span>
            </div>

            <div class="disc-anim disc-region-text" id="disc-region" style="transition-delay:.04s">--</div>

            <h2 class="disc-anim disc-place-title" id="disc-title" style="transition-delay:.08s">--</h2>

            <div class="disc-anim disc-meta-row" id="disc-meta" style="transition-delay:.11s">
              <span class="disc-stars" id="disc-stars">★★★★★</span>
              <span class="disc-rating-num" id="disc-rating">0.0</span>
              <span class="disc-price-tag" id="disc-price">--</span>
            </div>

            <p class="disc-anim disc-place-desc" id="disc-desc" style="transition-delay:.15s">--</p>

            <div class="disc-anim disc-actions" id="disc-actions" style="transition-delay:.19s">
              <button class="disc-bookmark-btn" id="disc-bookmark-btn" title="Lưu yêu thích">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </button>
              <button class="disc-select-btn" id="disc-select-btn">
                Chọn địa điểm
                <span class="disc-select-arrow">
                  <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                    <line x1="5" y1="12" x2="19" y2="12"/>
                    <polyline points="12 5 19 12 12 19"/>
                  </svg>
                </span>
              </button>
            </div>
          </div>

          <!-- ── RIGHT: Swiper ── -->
          <div class="disc-right">
            <div class="disc-swiper-outer">
              <div class="swiper disc-swiper" id="disc-swiper">
                <div class="swiper-wrapper">${cards}</div>
              </div>
            </div>

            <!-- Nav bar -->
            <div class="disc-nav-bar">
              <button class="disc-nav-btn" id="disc-prev" aria-label="Địa điểm trước">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
              </button>
              <button class="disc-nav-btn" id="disc-next" aria-label="Địa điểm tiếp theo">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
              <div class="disc-progress-track">
                <div class="disc-progress-fill" id="disc-progress-fill" style="width:0%"></div>
              </div>
              <div class="disc-counter" id="disc-counter">
                01<sub>/${String(places.length).padStart(2,'0')}</sub>
              </div>
            </div>
          </div>

        </div>`;
    },

    /* ── Swiper init ── */
    _initSwiper(places) {
      this._swiper = new Swiper('#disc-swiper', {
        slidesPerView: 'auto',
        spaceBetween: 22,
        centeredSlides: true,      // FIX: center card active, nav mới hoạt động
        grabCursor: true,
        loop: false,
        resistance: true,
        resistanceRatio: 0.7,
        watchSlidesProgress: true, // FIX: track slide active chính xác hơn
        on: {
          slideChange: (swiper) => {
            this._setFocus(swiper.realIndex, true);
          },
        },
      });

      // Click any card to focus it
      document.querySelectorAll('.disc-slide').forEach(slide => {
        slide.addEventListener('click', () => {
          const idx = parseInt(slide.dataset.index);
          if (!isNaN(idx) && this._swiper) {
            this._swiper.slideTo(idx);
          }
        });
      });
    },

    /* ── Event bindings ── */
    _bindEvents() {
      document.getElementById('disc-prev')?.addEventListener('click', () => {
        this._swiper?.slidePrev();
      });
      document.getElementById('disc-next')?.addEventListener('click', () => {
        this._swiper?.slideNext();
      });

      document.getElementById('disc-bookmark-btn')?.addEventListener('click', () => {
        const place = this._places[APP_STATE.activePlaceIndex];
        if (!place) return;
        if (APP_STATE.isGuest) {
          showToast('Đăng nhập để lưu yêu thích ❤️');
          AuthModal.open('login');
          return;
        }
        Favorites.add(place);
        this._updateBookmarkState(place.id);
      });

      document.getElementById('disc-select-btn')?.addEventListener('click', () => {
        if (typeof DetailModal !== 'undefined') {
          DetailModal.open(APP_STATE.activePlaceIndex);
        } else {
          // Stub — Part 3 will replace this
          const place = this._places[APP_STATE.activePlaceIndex];
          showToast(`"${place?.name}" — Chi tiết sẽ có ở Phần 3`, 'success', 2500);
        }
      });
    },

    /* ── Set focus to a place index ── */
    _setFocus(index, animated) {
      APP_STATE.activePlaceIndex = index;
      const place = this._places[index];
      if (!place) return;

      const ANIM_ELS = ['disc-distance','disc-region','disc-title','disc-meta','disc-desc','disc-actions'];

      if (animated) {
        // Step 1: fade out animated elements
        ANIM_ELS.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.classList.remove('in');
        });
        // Step 2: after short pause, update + fade in
        setTimeout(() => this._applyFocus(place, ANIM_ELS, index), 80);
      } else {
        this._applyFocus(place, ANIM_ELS, index);
      }
    },

    _applyFocus(place, animEls, index) {
      // ── Background crossfade ──
      const imgUrl = place.image_url && place.image_url.startsWith('http')
        ? place.image_url
        : `https://picsum.photos/seed/${place.id || index}/1920/1080`;

      const incoming = this._bgActive === 'a' ? this._bgB : this._bgA;
      const outgoing = this._bgActive === 'a' ? this._bgA : this._bgB;

      if (incoming) {
        incoming.style.backgroundImage = `url('${imgUrl}')`;
        incoming.style.opacity = '1';
      }
      if (outgoing) {
        outgoing.style.opacity = '0';
      }
      this._bgActive = this._bgActive === 'a' ? 'b' : 'a';

      // ── Left panel content ──
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };

      set('disc-dist-val', place.distance != null ? `${Number(place.distance).toFixed(1)} km từ bạn` : '-- km');
      set('disc-region', place.category || 'Địa điểm');
      set('disc-title', place.name || '');

      // Rating stars
      const r = place.rating || 0;
      const fullS = Math.round(r);
      const starsEl = document.getElementById('disc-stars');
      if (starsEl) starsEl.textContent = '★'.repeat(fullS) + '☆'.repeat(Math.max(0, 5 - fullS));
      set('disc-rating', `${Number(r).toFixed(1)}/5`);

      // Price
      const priceEl = document.getElementById('disc-price');
      if (priceEl) {
        priceEl.textContent = place.price === 0 ? 'Miễn phí' : `${Number(place.price).toLocaleString('vi-VN')}đ`;
      }

      // Description — prefer AI description, fall back to tag
      set('disc-desc', place.description || place.tag || `Địa điểm ${place.category || ''} tại TP.HCM`);

      // Bookmark state
      this._updateBookmarkState(place.id);

      // Counter
      const counterEl = document.getElementById('disc-counter');
      if (counterEl) {
        counterEl.innerHTML = `${String(index + 1).padStart(2, '0')}<sub>/${String(this._places.length).padStart(2, '0')}</sub>`;
      }

      // Progress bar
      const prog = document.getElementById('disc-progress-fill');
      if (prog) {
        const pct = this._places.length > 1
          ? (index / (this._places.length - 1)) * 100
          : 100;
        prog.style.width = `${pct}%`;
      }

      // Nav button disabled state
      const prev = document.getElementById('disc-prev');
      const next = document.getElementById('disc-next');
      if (prev) prev.disabled = index === 0;
      if (next) next.disabled = index === this._places.length - 1;

      // ── Staggered fade-in ──
      requestAnimationFrame(() => {
        animEls.forEach((id, i) => {
          const el = document.getElementById(id);
          if (el) setTimeout(() => el.classList.add('in'), i * 45);
        });
      });
    },

    _updateBookmarkState(placeId) {
      const btn = document.getElementById('disc-bookmark-btn');
      if (!btn) return;
      const faved = Favorites.has(placeId);
      btn.classList.toggle('active', faved);
    },

    // Public: gọi từ DecisionHub khi click pin trên map
    focusPlace(index) {
      if (index >= 0 && index < this._places.length) {
        this._setFocus(index, true);
        // Nếu Swiper đang chạy thì sync slide
        if (this._swiper) this._swiper.slideTo(index);
      }
    },
  };

