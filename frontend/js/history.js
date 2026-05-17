  /* ═══════════════════════════════════════════════════════════
     PLACEHOLDER STUBS — Sẽ được ghi đè bởi các Part sau
  ═══════════════════════════════════════════════════════════ */
  /* ═══════════════════════════════════════════════════════════
     HISTORY MODAL MANAGER
  ═══════════════════════════════════════════════════════════ */
  const HistoryModal = {
    open() {
      const modal = document.getElementById('history-modal');
      if (!modal) return;
      modal.classList.add('open');
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', this._onKey);
      this._load();
    },
    close() {
      const modal = document.getElementById('history-modal');
      if (modal) modal.classList.remove('open');
      document.body.style.overflow = '';
      document.removeEventListener('keydown', this._onKey);
    },
    _onKey(e) { if (e.key === 'Escape') HistoryModal.close(); },

    async _load() {
      const list = document.getElementById('history-list');
      const sub  = document.getElementById('history-modal-sub');
      if (!list) return;

      // Fix overflow: Giới hạn chiều cao danh sách, cho phép cuộn, giữ tiêu đề cố định
      list.style.maxHeight = '55vh';
      list.style.overflowY = 'auto';

      // Loading state
      list.innerHTML = '<div class="hist-loading"><div class="hist-spinner"></div>Đang tải lịch sử...</div>';

      if (!APP_STATE.user) {
        list.innerHTML = '<div class="hist-empty"><div class="hist-empty-icon">🔒</div>Vui lòng đăng nhập để xem lịch sử</div>';
        return;
      }

      try {
        const data = await API.history(10);
        const items = data.history || [];
        
        // Lưu lại data vào bộ nhớ để khi click thì lấy ra dùng
        this._historyItems = items;
        
        if (sub) sub.textContent = items.length > 0
          ? `${items.length} lượt tìm kiếm gần đây của ${APP_STATE.user.email}`
          : 'Chưa có lịch sử tìm kiếm';

        if (items.length === 0) {
          list.innerHTML = '<div class="hist-empty"><div class="hist-empty-icon">🔍</div>Bạn chưa tìm kiếm địa điểm nào</div>';
          return;
        }

        list.innerHTML = items.map((item, i) => {
          const results = item.results || [];
          const time = item.timestamp ? this._formatTime(item.timestamp) : '';
          const chips = results.slice(0, 3).map(r =>
            `<span class="hist-result-chip">${r.name || 'Địa điểm'}</span>`
          ).join('');

          return `<div class="hist-item" data-query="${(item.query||'').replace(/"/g,'&quot;')}">
            <div class="hist-item-top">
              <div class="hist-query">${item.query || '(không có nội dung)'}</div>
              <span class="hist-time">${time}</span>
            </div>
            ${results.length > 0 ? `<div class="hist-results">${chips}</div>` : ''}
            <div class="hist-replay-btn">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
              Tìm lại
            </div>
          </div>`;
        }).join('');

        // Click để tìm lại
        list.querySelectorAll('.hist-item').forEach((el, index) => {
          el.addEventListener('click', () => {
            const selectedItem = this._historyItems[index];
            if (!selectedItem || !selectedItem.results || selectedItem.results.length === 0) return;
            
            this.close();
            const input = document.getElementById('main-search-input');
            if (input) input.value = selectedItem.query || '';
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            // Tái tạo lại cấu trúc Response giả lập từ lịch sử
            const mockResponse = {
                status: 'success',
                message: 'Khôi phục từ lịch sử',
                top_places: selectedItem.results,
                weather_info: selectedItem.weather_info || null,
                user_context_summary: selectedItem.user_context_summary || ''
            };
            
            // Phát sự kiện (hoặc gọi hàm) để render UI KHÔNG qua API
            document.dispatchEvent(new CustomEvent('restoreHistory', { detail: mockResponse }));
          });
        });

      } catch(err) {
        list.innerHTML = '<div class="hist-empty"><div class="hist-empty-icon">⚠️</div>Không lấy được lịch sử. Thử lại sau.</div>';
      }
    },

    _formatTime(isoStr) {
      try {
        const d = new Date(isoStr + 'Z'); // UTC từ backend
        const now = new Date();
        const diff = Math.floor((now - d) / 1000);
        if (diff < 60)    return 'Vừa xong';
        if (diff < 3600)  return `${Math.floor(diff/60)} phút trước`;
        if (diff < 86400) return `${Math.floor(diff/3600)} giờ trước`;
        if (diff < 604800)return `${Math.floor(diff/86400)} ngày trước`;
        return d.toLocaleDateString('vi-VN');
      } catch(e) { return ''; }
    },
  };
