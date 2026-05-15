  /* ═══════════════════════════════════════════════════════════
     APP STATE — Single source of truth cho toàn bộ app
     Các phần sau chỉ cần đọc/ghi vào APP_STATE
  ═══════════════════════════════════════════════════════════ */
  const APP_STATE = {
    // Auth
    user: null,           // { uid, email, idToken } hoặc null (guest)
    isGuest: true,

    // Search results
    lastQuery: '',
    lastLocation: [10.7769, 106.7009],  // default TP.HCM center
    results: null,        // SuggestionResponse từ backend
    places: [],           // top_places array
    weather: null,        // weather_info object
    contextSummary: '',

    // UI state
    activePlaceIndex: 0,  // index đang focus ở Tầng 2
    favorites: [],        // [place object] — persist localStorage
    mapInstance: null,    // Leaflet map instance (Phần 4)
    resultsRevealed: false,

    // Config
    API_BASE: 'http://localhost:8000',
  };

