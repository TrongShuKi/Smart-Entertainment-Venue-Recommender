  /* ═══════════════════════════════════════════════════════════
     PART 4 — DECISION HUB
     Bản đồ Leaflet toàn cảnh + Weather widget + Chart + Directions
  ═══════════════════════════════════════════════════════════ */
  var DecisionHub = {
    _map: null,
    _markers: [],
    _weatherChart: null,
    _MEDALS: ['🥇', '🥈', '🥉'],
    _COLORS: ['#c8a96e', '#4a9eff', '#52b788'],

    /* ── Weather helpers ── */
    _ICONS: { CLEAR:'☀️', CLOUDS:'⛅', RAIN:'🌧️', DRIZZLE:'🌦️', STORM:'⛈️', MIST:'🌫️', SNOW:'❄️' },
    _comment(w) {
      if (!w) return 'Thời tiết ổn định, thích hợp để khám phá.';
      const c = w.condition;
      if (c === 'CLEAR')   return `🌞 Nắng đẹp ${Math.round(w.temperature)}°C — lý tưởng để xuất phát ngay!`;
      if (c === 'RAIN')    return `🌧️ Trời đang mưa — ưu tiên chọn địa điểm trong nhà nhé.`;
      if (c === 'STORM')   return `⛈️ Có dông bão — nên hoãn lại hoặc chọn nơi an toàn trong nhà.`;
      if (c === 'CLOUDS')  return `⛅ Nhiều mây, nhiệt độ dễ chịu — rất phù hợp để đi dạo ngoài trời.`;
      if (c === 'DRIZZLE') return `🌦️ Mưa nhỏ lất phất — nhớ mang theo ô cho chắc!`;
      if (c === 'MIST')    return `🌫️ Sương mù nhẹ, tầm nhìn hạn chế — lái xe cẩn thận.`;
      return `Thời tiết hiện tại ${w.condition_vi || c}.`;
    },

    /* ── Build HTML ── */
    _buildHTML(places, weather) {
      const w = weather || {};
      const icon = this._ICONS[w.condition] || '🌡️';
      const temp = w.temperature ? Math.round(w.temperature) : '--';
      const rainPct = w.rain_probability != null ? Math.round(w.rain_probability * 100) : 0;
      const tempPct = w.temperature ? Math.min(100, Math.round(((w.temperature - 15) / 25) * 100)) : 50;

      const dirBtns = places.map((p, i) => `
        <a class="dec-dir-btn" id="dec-dir-${i}"
           href="https://www.google.com/maps/dir/?api=1&destination=${p.latitude},${p.longitude}"
           target="_blank" rel="noopener">
          <span class="dec-dir-medal">${this._MEDALS[i] || (i+1)}</span>
          <span class="dec-dir-info">
            <span class="dec-dir-name">${p.name}</span>
            <span class="dec-dir-dist">${p.distance != null ? p.distance.toFixed(1) + ' km từ bạn' : '--'}</span>
          </span>
          <svg class="dec-dir-arrow" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
          </svg>
        </a>`).join('');

      return `
        <div id="decision-inner">
          <!-- Header -->
          <div class="dec-header">
            <div class="dec-eyebrow">✦ Bước cuối cùng</div>
            <h2 class="dec-title">Ra quyết định</h2>
            <p class="dec-subtitle">Xem bản đồ, thời tiết thực tế và chỉ đường đến địa điểm bạn chọn</p>
          </div>

          <div class="dec-layout">
            <!-- Cột trái: Bản đồ -->
            <div>
              <div class="dec-map-wrap">
                <div id="decision-map"></div>
                <!-- Map legend overlay -->
                <div id="dec-map-legend" style="
                  position:absolute; bottom:16px; left:16px; z-index:500;
                  background:rgba(10,12,15,0.8); backdrop-filter:blur(12px);
                  border:1px solid rgba(255,255,255,0.08); border-radius:12px;
                  padding:10px 14px; display:flex; flex-direction:column; gap:7px;">
                  <div style="display:flex;align-items:center;gap:8px;font-size:11px;font-family:var(--font-mono);color:rgba(240,237,232,0.5);">
                    <div style="width:10px;height:10px;border-radius:50%;background:#4a9eff;border:2px solid #fff;flex-shrink:0;"></div>
                    Vị trí của bạn
                  </div>
                  ${places.map((p,i) => `
                  <div style="display:flex;align-items:center;gap:8px;font-size:11px;font-family:var(--font-mono);color:rgba(240,237,232,0.5);">
                    <div style="width:10px;height:10px;border-radius:50%;background:${this._COLORS[i]};border:2px solid #fff;flex-shrink:0;"></div>
                    ${p.name}
                  </div>`).join('')}
                </div>
              </div>
            </div>

            <!-- Cột phải: Weather + Directions -->
            <div class="dec-right-col">

              <!-- Weather Card -->
              <div class="dec-weather-card">
                <div class="dec-weather-top">
                  <div>
                    <div class="dec-weather-icon">${icon}</div>
                    <div style="font-size:12px;color:var(--text-dim);font-family:var(--font-mono);margin-top:6px;">
                      ${w.location_name || 'TP. Hồ Chí Minh'}
                    </div>
                  </div>
                  <div class="dec-weather-main">
                    <div class="dec-weather-temp">${temp}<sup>°C</sup></div>
                    <div class="dec-weather-cond">${w.condition_vi || w.condition || 'N/A'}</div>
                  </div>
                </div>

                <!-- Comment -->
                <div class="dec-weather-comment">${this._comment(w)}</div>

                <!-- Metrics -->
                <div class="dec-metric-row">
                  <span class="dec-metric-label">Xác suất mưa</span>
                  <span class="dec-metric-value">${rainPct}%</span>
                </div>
                <div class="dec-bar-track">
                  <div class="dec-bar-fill rain" id="dec-rain-bar" style="width:0%"></div>
                </div>

                <div class="dec-metric-row">
                  <span class="dec-metric-label">Nhiệt độ</span>
                  <span class="dec-metric-value">${temp}°C</span>
                </div>
                <div class="dec-bar-track">
                  <div class="dec-bar-fill temp" id="dec-temp-bar" style="width:0%"></div>
                </div>

                <!-- Mini chart: Nhiệt độ theo giờ (giả lập từ temp thực) -->
                <div style="margin-top:14px;">
                  <div style="font-family:var(--font-mono);font-size:10px;letter-spacing:0.15em;text-transform:uppercase;color:var(--text-dim);margin-bottom:8px;">
                    Xu hướng nhiệt độ hôm nay
                  </div>
                  <div class="dec-chart-wrap">
                    <canvas id="weather-chart"></canvas>
                  </div>
                </div>
              </div>

              <!-- Directions Card -->
              <div class="dec-directions-card">
                <div class="dec-directions-label">🗺 Chỉ đường Google Maps</div>
                ${dirBtns}
              </div>

            </div><!-- /dec-right-col -->
          </div><!-- /dec-layout -->
        </div><!-- /decision-inner -->
      `;
    },

    /* ── Init Leaflet map ── */
    _initMap(places, userCoords) {
      const [uLat, uLon] = userCoords;

      // Nếu map đã tồn tại thì destroy trước
      if (this._map) {
        this._map.remove();
        this._map = null;
        this._markers = [];
      }

      this._map = L.map('decision-map', {
        center: [uLat, uLon],
        zoom: 13,
        zoomControl: true,
        attributionControl: false,
      });

      // Lưu vào APP_STATE để SidePanel dùng
      APP_STATE.mapInstance = this._map;

      // Dark tile layer
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
      }).addTo(this._map);

      // ── User marker ──
      const userIcon = L.divIcon({
        html: `<div style="
          width:16px;height:16px;border-radius:50%;
          background:#4a9eff;border:3px solid #fff;
          box-shadow:0 0 0 4px rgba(74,158,255,0.25), 0 4px 12px rgba(0,0,0,0.4);
        "></div>`,
        iconSize: [16, 16], iconAnchor: [8, 8], className: '',
      });
      L.marker([uLat, uLon], { icon: userIcon })
        .addTo(this._map)
        .bindTooltip('<b>📍 Bạn đang ở đây</b>', { permanent: false, direction: 'top' });

      // ── Place markers ──
      places.forEach((place, i) => {
        const lat = place.latitude, lon = place.longitude;
        if (!lat || !lon) return;

        const color = this._COLORS[i] || '#c8a96e';
        const medal = this._MEDALS[i] || (i + 1);

        const placeIcon = L.divIcon({
          html: `<div style="
            width:40px;height:40px;border-radius:50%;
            background:${color};border:3px solid #fff;
            box-shadow:0 4px 16px rgba(0,0,0,0.5);
            display:flex;align-items:center;justify-content:center;
            font-size:17px;cursor:pointer;
            transition:transform 0.2s;
          " onmouseenter="this.style.transform='scale(1.2)'"
             onmouseleave="this.style.transform='scale(1)'"
          >${medal}</div>`,
          iconSize: [40, 40], iconAnchor: [20, 20], className: '',
        });

        const imgSrc = place.image_url && place.image_url.startsWith('http')
          ? place.image_url
          : `https://picsum.photos/seed/${place.id || i}/120/80`;

        const tooltipHtml = `
          <div style="
            font-family:'DM Sans',sans-serif;
            width:200px;
          ">
            <img src="${imgSrc}" alt="${place.name}"
              style="width:100%;height:80px;object-fit:cover;border-radius:8px;margin-bottom:8px;display:block;"
              onerror="this.style.display='none'" />
            <div style="font-weight:600;font-size:13px;color:#111;margin-bottom:2px;">${place.name}</div>
            <div style="font-size:11px;color:#666;">${place.category || ''} · ${place.distance != null ? place.distance.toFixed(1) + ' km' : ''}</div>
            <div style="font-size:11px;color:#c8a96e;margin-top:2px;">★ ${Number(place.rating || 0).toFixed(1)} · ${medal}</div>
          </div>`;

        const marker = L.marker([lat, lon], { icon: placeIcon })
          .addTo(this._map)
          .bindTooltip(tooltipHtml, {
            direction: 'top',
            offset: [0, -24],
            className: 'dec-leaflet-tooltip',
            sticky: false,
          });

        // Click marker → scroll lên Tầng 2 + mở Detail Modal
        marker.on('click', () => {
          const disc = document.getElementById('section-discovery');
          if (disc) {
            const y = disc.getBoundingClientRect().top + window.scrollY - 64;
            window.scrollTo({ top: y, behavior: 'smooth' });
          }
          setTimeout(() => {
            if (typeof Discovery !== 'undefined') Discovery.focusPlace(i);
            if (typeof DetailModal !== 'undefined') DetailModal.open(i);
          }, 500);
        });

        this._markers.push(marker);

        // Dashed line: user → place
        L.polyline([[uLat, uLon], [lat, lon]], {
          color, weight: 2, opacity: 0.4, dashArray: '6 8',
        }).addTo(this._map);
      });

      // Fit map to show all markers
      const allCoords = [
        [uLat, uLon],
        ...places.filter(p => p.latitude && p.longitude).map(p => [p.latitude, p.longitude]),
      ];
      if (allCoords.length > 1) {
        this._map.fitBounds(allCoords, { padding: [48, 48] });
      }
    },

    /* ── Animate bars ── */
    _animateBars(rainPct, tempPct) {
      // Delay để CSS transition chạy sau khi DOM mount
      setTimeout(() => {
        const rainBar = document.getElementById('dec-rain-bar');
        const tempBar = document.getElementById('dec-temp-bar');
        if (rainBar) rainBar.style.width = `${rainPct}%`;
        if (tempBar) tempBar.style.width = `${Math.max(5, tempPct)}%`;
      }, 300);
    },

    /* ── Weather chart (Chart.js) ── */
    _initChart(baseTemp) {
      const canvas = document.getElementById('weather-chart');
      if (!canvas || typeof Chart === 'undefined') return;

      // Destroy old chart if exists
      if (this._weatherChart) {
        this._weatherChart.destroy();
        this._weatherChart = null;
      }

      // Simulate hourly temps from base: morning cool → afternoon peak → evening drop
      const now = new Date().getHours();
      const hours = Array.from({ length: 8 }, (_, i) => {
        const h = (now - 3 + i + 24) % 24;
        return `${h}:00`;
      });
      const base = baseTemp || 30;
      const temps = hours.map((_, i) => {
        const h = (now - 3 + i + 24) % 24;
        // Peak at 13-14h, cool at 5-6h
        const offset = Math.sin(((h - 6) / 24) * Math.PI * 2) * 4;
        return +(base + offset + (Math.random() - 0.5) * 0.8).toFixed(1);
      });

      const gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, 130);
      gradient.addColorStop(0, 'rgba(200,169,110,0.3)');
      gradient.addColorStop(1, 'rgba(200,169,110,0.0)');

      this._weatherChart = new Chart(canvas, {
        type: 'line',
        data: {
          labels: hours,
          datasets: [{
            data: temps,
            borderColor: '#c8a96e',
            borderWidth: 2,
            backgroundColor: gradient,
            fill: true,
            tension: 0.45,
            pointRadius: 3,
            pointBackgroundColor: '#c8a96e',
            pointBorderColor: '#0a0c0f',
            pointBorderWidth: 1.5,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#1a1d22',
              titleColor: '#c8a96e',
              bodyColor: '#f0ede8',
              borderColor: 'rgba(255,255,255,0.08)',
              borderWidth: 1,
              padding: 8,
              callbacks: {
                label: ctx => `${ctx.parsed.y}°C`,
              },
            },
          },
          scales: {
            x: {
              grid: { color: 'rgba(255,255,255,0.04)' },
              ticks: { color: 'rgba(240,237,232,0.35)', font: { family: 'Space Grotesk', size: 10 } },
            },
            y: {
              grid: { color: 'rgba(255,255,255,0.04)' },
              ticks: {
                color: 'rgba(240,237,232,0.35)',
                font: { family: 'Space Grotesk', size: 10 },
                callback: v => `${v}°`,
              },
            },
          },
        },
      });
    },

    /* ── Main render ── */
    render(places, weather, userLocation) {
      const sec = document.getElementById('section-decision');
      if (!sec) return;

      // Inject HTML (idempotent — chỉ inject 1 lần, update lại data nếu gọi lại)
      sec.innerHTML = this._buildHTML(places, weather);

      // Animate bars
      const rainPct = weather?.rain_probability != null ? Math.round(weather.rain_probability * 100) : 0;
      const tempPct = weather?.temperature ? Math.min(100, Math.round(((weather.temperature - 15) / 25) * 100)) : 50;
      this._animateBars(rainPct, tempPct);

      // Init chart
      this._initChart(weather?.temperature);

      // Init map (after DOM is ready)
      const coords = userLocation || APP_STATE.lastLocation || [10.7769, 106.7009];
      setTimeout(() => this._initMap(places, coords), 80);

      // Inject Leaflet tooltip CSS nếu chưa có
      this._injectTooltipCSS();
    },

    /* ── Leaflet custom tooltip CSS ── */
    _injectTooltipCSS() {
      if (document.getElementById('dec-tooltip-style')) return;
      const style = document.createElement('style');
      style.id = 'dec-tooltip-style';
      style.textContent = `
        .dec-leaflet-tooltip {
          background: #fff !important;
          border: none !important;
          border-radius: 12px !important;
          padding: 10px !important;
          box-shadow: 0 8px 32px rgba(0,0,0,0.25) !important;
          font-family: 'DM Sans', sans-serif !important;
        }
        .dec-leaflet-tooltip::before { display: none !important; }
        .leaflet-tooltip-top.dec-leaflet-tooltip::before {
          display: block !important;
          border-top-color: #fff !important;
        }
      `;
      document.head.appendChild(style);
    },
  };
