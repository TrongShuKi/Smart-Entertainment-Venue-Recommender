/* ═══════════════════════════════════════════════════════════
   settings.js — Theme & Language preferences
   Phụ thuộc: i18n.js (load trước), state.js, ui-utils.js
   KHÔNG sửa bất kỳ file JS nào khác.
   
   Tích hợp vào app hiện tại:
     1. Thêm dropdown item #dd-settings vào user-dropdown (xem hướng dẫn trong index.html patch)
     2. Bind event trong main.js (xem phần cuối file này)
═══════════════════════════════════════════════════════════ */
const Settings = {
  _STORAGE_KEY: 'st_settings',

  /* ── Đọc từ localStorage ── */
  _load() {
    try {
      const raw = localStorage.getItem(this._STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch(e) { return {}; }
  },

  /* ── Ghi vào localStorage ── */
  _save(data) {
    try { localStorage.setItem(this._STORAGE_KEY, JSON.stringify(data)); } catch(e) {}
  },

  /* ── Khởi tạo: đọc prefs, áp dụng ngay khi load trang ── */
  init() {
    const prefs = this._load();
    const theme = prefs.theme || 'dark';
    const lang  = prefs.lang  || 'vi';

    this.applyTheme(theme, false);   // false = không save lại
    this.applyLang(lang,   false);
  },

  /* ── Áp dụng theme ── */
  applyTheme(theme, save = true) {
    if (typeof APP_STATE !== 'undefined') APP_STATE.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);

    // Sync toggle UI nếu modal đang mở
    const darkBtn  = document.getElementById('st-theme-dark');
    const lightBtn = document.getElementById('st-theme-light');
    if (darkBtn)  darkBtn.classList.toggle('active',  theme === 'dark');
    if (lightBtn) lightBtn.classList.toggle('active', theme === 'light');

    if (save) {
      const prefs = this._load();
      this._save({ ...prefs, theme });
    }
  },

  /* ── Áp dụng ngôn ngữ ── */
  applyLang(lang, save = true) {
    if (typeof APP_STATE !== 'undefined') APP_STATE.lang = lang;
    I18N.setLang(lang);
    I18N.applyDOM();

    // Sync toggle UI nếu modal đang mở
    const viBtn = document.getElementById('st-lang-vi');
    const enBtn = document.getElementById('st-lang-en');
    if (viBtn) viBtn.classList.toggle('active', lang === 'vi');
    if (enBtn) enBtn.classList.toggle('active', lang === 'en');

    if (save) {
      const prefs = this._load();
      this._save({ ...prefs, lang });
    }
  },

  /* ── Mở modal ── */
  open() {
    if (!document.getElementById('settings-modal')) {
      this._injectModal();
    }

    // Render nội dung (đồng bộ state hiện tại)
    this._renderContent();

    document.getElementById('settings-modal').classList.add('open');
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', this._onKey);
  },

  /* ── Đóng modal ── */
  close() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.remove('open');
    document.body.style.overflow = '';
    document.removeEventListener('keydown', this._onKey);
  },

  _onKey(e) { if (e.key === 'Escape') Settings.close(); },

  /* ── Inject modal HTML vào body (chỉ lần đầu) ── */
  _injectModal() {
    const div = document.createElement('div');
    div.id = 'settings-modal';
    div.setAttribute('role', 'dialog');
    div.setAttribute('aria-modal', 'true');
    div.innerHTML = `
      <div class="settings-backdrop" id="settings-backdrop"></div>
      <div class="settings-panel">
        <div class="settings-header">
          <h2 class="settings-title" data-i18n="settings.title">Cài đặt</h2>
          <button class="settings-close" id="settings-close" aria-label="Đóng">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Theme -->
        <div class="settings-section-label" data-i18n="settings.theme">Giao diện</div>
        <div class="settings-theme-group">
          <button class="settings-theme-btn" id="st-theme-dark">
            <div class="theme-preview theme-preview-dark"></div>
            <span data-i18n="settings.theme.dark">Tối</span>
          </button>
          <button class="settings-theme-btn" id="st-theme-light">
            <div class="theme-preview theme-preview-light"></div>
            <span data-i18n="settings.theme.light">Sáng</span>
          </button>
        </div>

        <!-- Language -->
        <div class="settings-section-label" style="margin-top:24px;" data-i18n="settings.lang">Ngôn ngữ</div>
        <div class="settings-lang-group">
          <button class="settings-lang-btn" id="st-lang-vi">
            <span class="settings-lang-flag">🇻🇳</span>
            Tiếng Việt
          </button>
          <button class="settings-lang-btn" id="st-lang-en">
            <span class="settings-lang-flag">🇬🇧</span>
            English
          </button>
        </div>

        <div class="settings-footer" data-i18n="settings.footer">
          Tùy chọn được lưu tự động trên trình duyệt này.
        </div>
      </div>`;
    document.body.appendChild(div);

    /* Bind events cho modal */
    document.getElementById('settings-backdrop').addEventListener('click', () => this.close());
    document.getElementById('settings-close').addEventListener('click',    () => this.close());

    document.getElementById('st-theme-dark').addEventListener('click',  () => this.applyTheme('dark'));
    document.getElementById('st-theme-light').addEventListener('click', () => this.applyTheme('light'));

    document.getElementById('st-lang-vi').addEventListener('click', () => this.applyLang('vi'));
    document.getElementById('st-lang-en').addEventListener('click', () => this.applyLang('en'));
  },

  /* ── Cập nhật trạng thái active của các nút trong modal ── */
  _renderContent() {
    const prefs = this._load();
    const theme = (typeof APP_STATE !== 'undefined' ? APP_STATE.theme : null) || prefs.theme || 'dark';
    const lang  = (typeof APP_STATE !== 'undefined' ? APP_STATE.lang  : null) || prefs.lang  || 'vi';

    const darkBtn  = document.getElementById('st-theme-dark');
    const lightBtn = document.getElementById('st-theme-light');
    if (darkBtn)  darkBtn.classList.toggle('active',  theme === 'dark');
    if (lightBtn) lightBtn.classList.toggle('active', theme === 'light');

    const viBtn = document.getElementById('st-lang-vi');
    const enBtn = document.getElementById('st-lang-en');
    if (viBtn) viBtn.classList.toggle('active', lang === 'vi');
    if (enBtn) enBtn.classList.toggle('active', lang === 'en');

    // Re-apply i18n labels in modal
    I18N.applyDOM();
  },
};


/* ═══════════════════════════════════════════════════════════
   HƯỚNG DẪN TÍCH HỢP VÀO CÁC FILE HIỆN TẠI
   (không sửa file cũ — chỉ thêm, paste vào đúng chỗ)
═══════════════════════════════════════════════════════════

── 1. index.html ─────────────────────────────────────────

  a) Thêm vào <head> (sau utils.css):
     <link rel="stylesheet" href="css/settings.css" />

  b) Thêm vào user-dropdown, SAU #dd-favorites và TRƯỚC .dropdown-sep:
     <div class="dropdown-item" id="dd-settings">
       <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
         <circle cx="12" cy="12" r="3"/>
         <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
       </svg>
       <span data-i18n="nav.settings">Cài đặt</span>
     </div>

  c) Thêm data-i18n vào các phần tử HTML tĩnh.
     Ví dụ quan trọng nhất:
       <span class="nav-brand-text">Smart Tourism</span>   ← không đổi (brand name)
       <li><a ... data-i18n="nav.home">Trang Chủ</a></li>
       <li><a ... data-i18n="nav.places">Địa Điểm</a></li>
       <li><a ... data-i18n="nav.map">Bản đồ & Thời Tiết</a></li>
       <span class="guest-tag" id="nav-guest-tag" data-i18n="nav.guest">GUEST</span>
       <button ... id="nav-login-btn" data-i18n="nav.login">ĐĂNG NHẬP</button>
       <input ... id="main-search-input" data-i18n-ph="hero.placeholder" ... />
       <span class="hero-eyebrow" data-i18n="hero.eyebrow">...</span>
       <p class="hero-sub" data-i18n="hero.sub">...</p>
       <span class="scroll-label" data-i18n="hero.scroll">Cuộn xuống</span>
       <h2 class="modal-title" data-i18n="auth.welcome">Chào mừng</h2>
       ... (thêm cho các element khác tương tự)

  d) Thêm <script> TRƯỚC state.js (hoặc ngay sau):
     <script src="js/i18n.js"></script>
     <script src="js/settings.js"></script>

── 2. main.js ────────────────────────────────────────────

  Thêm vào trong DOMContentLoaded, TRƯỚC dòng Auth.restoreSession():

    // Settings (theme + lang) — phải init trước mọi thứ
    Settings.init();

  Thêm event binding cho #dd-settings:
    $('#dd-settings')?.addEventListener('click', () => {
      $('#user-dropdown').classList.remove('open');
      Settings.open();
    });

  Thêm nút settings cho guest (không cần login):
    Trong phần nav actions của index.html, trước nav-login-btn:
    <button class="nav-btn" id="nav-settings-btn" title="Cài đặt">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65..."/>
      </svg>
    </button>
    
    Và bind:
    $('#nav-settings-btn')?.addEventListener('click', () => Settings.open());

── 3. auth.js — KHÔNG cần sửa gì ──────────────────────

  Nếu muốn toast messages theo ngôn ngữ, tìm các dòng showToast(...)
  và thay hardcoded string bằng t('key'). Ví dụ:

    showToast(`Chào mừng, ${userData.email}!`, 'success')
    →  showToast(t('toast.welcome', userData.email), 'success')

    showToast('Đã đăng xuất', 'success', 2000)
    →  showToast(t('toast.logout'), 'success', 2000)

  Đây là optional — app vẫn chạy đúng nếu chưa đổi.

═══════════════════════════════════════════════════════════ */