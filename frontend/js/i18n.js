/* ═══════════════════════════════════════════════════════════
   i18n.js — Internationalization (VI / EN)
   Không phụ thuộc vào bất kỳ module nào khác.
   Phải load TRƯỚC tất cả JS khác (sau state.js).
═══════════════════════════════════════════════════════════ */
const I18N = {
  _lang: 'vi',   // default, sẽ được override bởi Settings.init()

  strings: {
    vi: {
      /* Navbar */
      'nav.home':           'Trang Chủ',
      'nav.places':         'Địa Điểm',
      'nav.map':            'Bản đồ & Thời Tiết',
      'nav.search':         'Tìm kiếm',
      'nav.favorites':      'Yêu thích',
      'nav.guest':          'GUEST',
      'nav.login':          'ĐĂNG NHẬP',
      'nav.settings':       'Cài đặt',
      'nav.history':        'Lịch sử tìm kiếm',
      'nav.logout':         'Đăng xuất',

      /* Hero */
      'hero.eyebrow':       '✦ Hệ thống AI gợi ý địa điểm',
      'hero.sub':           'Nhập bất cứ điều bạn cảm thấy — AI sẽ tìm địa điểm hoàn hảo cho bạn',
      'hero.placeholder':   'VD: Đang stress, trời mưa, đi với bạn bè có ghế 300k ở Quận 1...',
      'hero.scroll':        'Cuộn xuống',
      'hero.loading':       'Đang tải...',
      'hero.chip.chill':    '☕ Chill buổi tối',
      'hero.chip.family':   '👨‍👩‍👧 Gia đình cuối tuần',
      'hero.chip.date':     '❤️ Hẹn hò lãng mạn',
      'hero.chip.rain':     '🌧️ Trời mưa ở nhà',

      /* Auth */
      'auth.welcome':       'Chào mừng',
      'auth.login':         'Đăng nhập',
      'auth.signup':        'Đăng ký',
      'auth.email':         'Email',
      'auth.password':      'Mật khẩu',
      'auth.password.hint': 'Ít nhất 6 ký tự',
      'auth.login.submit':  'Đăng nhập',
      'auth.signup.submit': 'Tạo tài khoản',
      'auth.google':        'Tiếp tục với Google',
      'auth.or':            'hoặc',
      'auth.guest':         'Không muốn đăng nhập?',
      'auth.guest.cta':     'Dùng thử với tư cách khách →',
      'auth.err.empty':     '⚠ Vui lòng nhập đầy đủ thông tin',
      'auth.err.short':     '⚠ Mật khẩu phải có ít nhất 6 ký tự',
      'auth.err.email':     '⚠ Email không hợp lệ',
      'auth.err.login':     '✕ Sai email hoặc mật khẩu. Thử lại nhé!',
      'auth.err.signup':    '✕ Tạo tài khoản thất bại. Email có thể đã tồn tại.',
      'auth.creating':      'Đang tạo tài khoản...',
      'auth.logging':       'Đang đăng nhập...',

      /* Toast */
      'toast.welcome':      (email) => `Chào mừng, ${email}!`,
      'toast.logout':       'Đã đăng xuất',
      'toast.fav.add':      (name) => `Đã lưu "${name}" ❤️`,
      'toast.fav.remove':   (name) => `Đã xóa "${name}"`,
      'toast.fav.err.add':  'Không lưu được yêu thích. Thử lại nhé!',
      'toast.fav.err.rm':   'Không xóa được. Thử lại nhé!',
      'toast.fav.login':    'Đăng nhập để lưu yêu thích ❤️',
      'toast.no.results':   'Không tìm thấy địa điểm phù hợp. Thử mô tả khác nhé!',
      'toast.no.server':    'Không kết nối được server. Kiểm tra backend đang chạy chưa?',
      'toast.google.fail':  'Đăng nhập Google thất bại. Thử lại nhé!',
      'toast.signup.ok':    'Tạo tài khoản thành công! Đang đăng nhập...',
      'toast.hist.restore': 'Dữ liệu cũ — đang tìm kiếm lại...',

      /* Side panel */
      'panel.title':        '❤ Yêu thích',
      'panel.login.msg':    'Đăng nhập để lưu địa điểm yêu thích',
      'panel.login.cta':    'Đăng nhập ngay →',
      'panel.empty':        'Chưa có địa điểm yêu thích',
      'panel.empty.hint':   'Bấm ❤ trên địa điểm để lưu',

      /* History */
      'hist.title':         'Lịch sử tìm kiếm',
      'hist.sub':           (email, count) => `${count} lượt tìm kiếm gần đây của ${email}`,
      'hist.empty.login':   'Vui lòng đăng nhập để xem lịch sử',
      'hist.empty':         'Bạn chưa tìm kiếm địa điểm nào',
      'hist.loading':       'Đang tải lịch sử...',
      'hist.error':         'Không lấy được lịch sử. Thử lại sau.',
      'hist.no.sub':        'Chưa có lịch sử tìm kiếm',
      'hist.restore':       'Khôi phục kết quả',
      'hist.search.again':  'Tìm lại',
      'hist.restore.msg':   'Khôi phục từ lịch sử',

      /* Detail modal */
      'detail.free':        'Miễn phí',
      'detail.desc':        (cat) => `Địa điểm ${cat} nổi bật tại TP.HCM.`,
      'detail.fact':        'Hãy đến tận nơi để cảm nhận không khí thực sự của địa điểm này.',
      'detail.status':      'Mở cửa',
      'detail.label.status':'Trạng thái:',
      'detail.label.price': 'Vé vào cửa:',
      'detail.label.type':  'Loại hình:',
      'detail.label.desc':  'Mô tả',
      'detail.btn.maps':    'Chỉ đường Google Maps',
      'detail.distance':    (km) => `${km} km từ bạn`,

      /* Discovery */
      'disc.place':         (cat) => `Địa điểm ${cat} tại TP.HCM`,
      'disc.select':        'Chọn địa điểm',
      'disc.km':            (n) => `${n} km từ bạn`,

      /* Decision hub */
      'dec.eyebrow':        'Phân tích & Quyết định',
      'dec.title':          'Bản đồ & Thời Tiết',
      'dec.subtitle':       'So sánh vị trí — Tất cả địa điểm trên một bản đồ',
      'dec.dir.label':      'Đường đến địa điểm',

      /* Settings */
      'settings.title':     'Cài đặt',
      'settings.theme':     'Giao diện',
      'settings.theme.dark':'Tối',
      'settings.theme.light':'Sáng',
      'settings.lang':      'Ngôn ngữ',
      'settings.footer':    'Tùy chọn được lưu tự động trên trình duyệt này.',
    },

    en: {
      /* Navbar */
      'nav.home':           'Home',
      'nav.places':         'Places',
      'nav.map':            'Map & Weather',
      'nav.search':         'Search',
      'nav.favorites':      'Favorites',
      'nav.guest':          'GUEST',
      'nav.login':          'LOG IN',
      'nav.settings':       'Settings',
      'nav.history':        'Search History',
      'nav.logout':         'Log out',

      /* Hero */
      'hero.eyebrow':       '✦ AI-powered place suggestions',
      'hero.sub':           'Tell us how you feel — AI will find the perfect spot for you',
      'hero.placeholder':   'E.g.: Stressed out, rainy day, with friends, budget ~300k in District 1...',
      'hero.scroll':        'Scroll down',
      'hero.loading':       'Loading...',
      'hero.chip.chill':    '☕ Chill tonight',
      'hero.chip.family':   '👨‍👩‍👧 Family weekend',
      'hero.chip.date':     '❤️ Romantic date',
      'hero.chip.rain':     '🌧️ Rainy day indoors',

      /* Auth */
      'auth.welcome':       'Welcome',
      'auth.login':         'Log in',
      'auth.signup':        'Sign up',
      'auth.email':         'Email',
      'auth.password':      'Password',
      'auth.password.hint': 'At least 6 characters',
      'auth.login.submit':  'Log in',
      'auth.signup.submit': 'Create account',
      'auth.google':        'Continue with Google',
      'auth.or':            'or',
      'auth.guest':         "Don't want to sign in?",
      'auth.guest.cta':     'Continue as guest →',
      'auth.err.empty':     '⚠ Please fill in all fields',
      'auth.err.short':     '⚠ Password must be at least 6 characters',
      'auth.err.email':     '⚠ Invalid email address',
      'auth.err.login':     '✕ Wrong email or password. Please try again!',
      'auth.err.signup':    '✕ Account creation failed. Email may already be in use.',
      'auth.creating':      'Creating account...',
      'auth.logging':       'Logging in...',

      /* Toast */
      'toast.welcome':      (email) => `Welcome, ${email}!`,
      'toast.logout':       'Logged out',
      'toast.fav.add':      (name) => `Saved "${name}" ❤️`,
      'toast.fav.remove':   (name) => `Removed "${name}"`,
      'toast.fav.err.add':  'Could not save favorite. Please try again!',
      'toast.fav.err.rm':   'Could not remove. Please try again!',
      'toast.fav.login':    'Log in to save favorites ❤️',
      'toast.no.results':   'No matching places found. Try a different description!',
      'toast.no.server':    'Cannot connect to server. Is the backend running?',
      'toast.google.fail':  'Google sign-in failed. Please try again!',
      'toast.signup.ok':    'Account created! Logging in...',
      'toast.hist.restore': 'Old data — searching again...',

      /* Side panel */
      'panel.title':        '❤ Favorites',
      'panel.login.msg':    'Log in to save favorite places',
      'panel.login.cta':    'Log in now →',
      'panel.empty':        'No favorites yet',
      'panel.empty.hint':   'Tap ❤ on a place to save it',

      /* History */
      'hist.title':         'Search History',
      'hist.sub':           (email, count) => `${count} recent searches by ${email}`,
      'hist.empty.login':   'Please log in to view history',
      'hist.empty':         "You haven't searched for any places yet",
      'hist.loading':       'Loading history...',
      'hist.error':         'Could not load history. Try again later.',
      'hist.no.sub':        'No search history',
      'hist.restore':       'Restore results',
      'hist.search.again':  'Search again',
      'hist.restore.msg':   'Restored from history',

      /* Detail modal */
      'detail.free':        'Free',
      'detail.desc':        (cat) => `A notable ${cat} spot in Ho Chi Minh City.`,
      'detail.fact':        'Visit in person to truly experience the atmosphere of this place.',
      'detail.status':      'Open',
      'detail.label.status':'Status:',
      'detail.label.price': 'Admission:',
      'detail.label.type':  'Type:',
      'detail.label.desc':  'Description',
      'detail.btn.maps':    'Get directions on Google Maps',
      'detail.distance':    (km) => `${km} km from you`,

      /* Discovery */
      'disc.place':         (cat) => `A ${cat} spot in Ho Chi Minh City`,
      'disc.select':        'Select this place',
      'disc.km':            (n) => `${n} km from you`,

      /* Decision hub */
      'dec.eyebrow':        'Analyse & Decide',
      'dec.title':          'Map & Weather',
      'dec.subtitle':       'Compare locations — all places on one map',
      'dec.dir.label':      'Directions',

      /* Settings */
      'settings.title':     'Settings',
      'settings.theme':     'Appearance',
      'settings.theme.dark':'Dark',
      'settings.theme.light':'Light',
      'settings.lang':      'Language',
      'settings.footer':    'Preferences are saved automatically in this browser.',
    },
  },

  /* ── Public API ── */
  setLang(lang) {
    if (!this.strings[lang]) return;
    this._lang = lang;
    document.documentElement.lang = lang;
  },

  /**
   * Translate a key.
   * t('toast.welcome', 'user@x.com')  → function keys get called with args
   * t('nav.home')                      → string keys returned directly
   */
  t(key, ...args) {
    const val = this.strings[this._lang]?.[key] ?? this.strings['vi'][key] ?? key;
    return typeof val === 'function' ? val(...args) : val;
  },

  /**
   * Apply translations to all [data-i18n] elements in the DOM.
   * Call after lang switch or on DOMContentLoaded.
   */
  applyDOM() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const val = this.t(key);
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = val;
      } else {
        el.textContent = val;
      }
    });
    // data-i18n-placeholder (inputs inside forms)
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      el.placeholder = this.t(el.dataset.i18nPh);
    });
  },
};

/* Convenience shorthand — dùng t() thay vì I18N.t() ở khắp nơi */
function t(key, ...args) { return I18N.t(key, ...args); }
