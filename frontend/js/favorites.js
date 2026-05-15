  /* ═══════════════════════════════════════════════════════════
     FAVORITES MANAGER
  ═══════════════════════════════════════════════════════════ */
  const Favorites = {
    add(place) {
      if (!APP_STATE.favorites.find(f => f.id === place.id)) {
        APP_STATE.favorites.push(place);
        saveFavorites();
        SidePanel.render();
        showToast(`Đã lưu "${place.name}" vào yêu thích ❤️`, 'success', 2500);
      } else {
        this.remove(place.id);
      }
    },
    remove(id) {
      APP_STATE.favorites = APP_STATE.favorites.filter(f => f.id !== id);
      saveFavorites();
      SidePanel.render();
    },
    has(id) {
      return APP_STATE.favorites.some(f => f.id === id);
    },
  };

