/* ═══════════════════════════════════════════════════════════
     FAVORITES MANAGER
     - Lưu/load từ Firestore (qua API /favorites)
     - localStorage chỉ làm cache tạm để UI phản hồi ngay
     - Guest: không lưu gì cả
  ═══════════════════════════════════════════════════════════ */
  const Favorites = {

    /* ── Thêm yêu thích ── */
    async add(place) {
      if (APP_STATE.isGuest) {
        showToast('Đăng nhập để lưu yêu thích ❤️');
        AuthModal.open('login');
        return;
      }

      // Toggle: nếu đã có thì xóa
      if (this.has(place.id)) {
        await this.remove(place.id);
        return;
      }

      // Cập nhật state + UI ngay (optimistic)
      APP_STATE.favorites.push(place);
      SidePanel.render();
      showToast(`Đã lưu "${place.name}" ❤️`, 'success', 2500);

      // Sync lên Firestore
      try {
        await API.post('/favorites', place, true);
      } catch(e) {
        // Rollback nếu lỗi
        APP_STATE.favorites = APP_STATE.favorites.filter(f => f.id !== place.id);
        SidePanel.render();
        showToast('Không lưu được yêu thích. Thử lại nhé!');
        console.error('[Favorites] add error:', e);
      }
    },

    /* ── Xóa yêu thích ── */
    async remove(id) {
      const strId = String(id);
      const removed = APP_STATE.favorites.find(f => String(f.id) === strId);
      if (!removed) return;

      // Cập nhật state + UI ngay (optimistic)
      APP_STATE.favorites = APP_STATE.favorites.filter(f => String(f.id) !== strId);
      SidePanel.render();
      showToast(`Đã xóa "${removed.name}"`, 'success', 2000);

      // Sync lên Firestore
      try {
        await API.delete(`/favorites/${encodeURIComponent(strId)}`, true);
      } catch(e) {
        // Rollback
        APP_STATE.favorites.push(removed);
        SidePanel.render();
        showToast('Không xóa được. Thử lại nhé!');
        console.error('[Favorites] remove error:', e);
      }
    },

    /* ── Kiểm tra đã lưu chưa ── */
    has(id) {
      return APP_STATE.favorites.some(f => String(f.id) === String(id));
    },

    /* ── Load từ Firestore khi login ── */
    async load() {
      if (APP_STATE.isGuest || !APP_STATE.user) {
        APP_STATE.favorites = [];
        SidePanel.render();
        return;
      }
      try {
        const data = await API.get('/favorites', {}, true);
        APP_STATE.favorites = data.favorites || [];
        SidePanel.render();
      } catch(e) {
        // Fallback về localStorage nếu API lỗi
        loadFavoritesLocal();
        console.warn('[Favorites] load from Firestore failed, using local cache:', e);
      }
    },

    /* ── Xóa hết khi logout ── */
    clear() {
      APP_STATE.favorites = [];
      SidePanel.render(); // badge sẽ về 0 trong render()
    },
  };