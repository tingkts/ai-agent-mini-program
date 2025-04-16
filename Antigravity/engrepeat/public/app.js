let currentMode = 'auto';
let mainEnglishText = '';

// DOM Elements
const inputText = document.getElementById('input-text');
const charCount = document.getElementById('char-count');
const warningBox = document.getElementById('warning-box');
const warningText = document.getElementById('warning-text');
const resultsArea = document.getElementById('results-area');
const translateBtn = document.getElementById('translate-submit-btn');

// Audio elements
const audioPlayers = {
  main: document.getElementById('audio-main'),
  example1: document.getElementById('audio-example1'),
  example2: document.getElementById('audio-example2'),
  example3: document.getElementById('audio-example3')
};

// Playback state
const playState = {
  main: false,
  example1: false,
  example2: false,
  example3: false
};

// Default all players to LOOP
const loopState = {
  main: true,
  example1: true,
  example2: true,
  example3: true
};

// Global storage for dynamic examples
window.examplesEnglishTexts = [];

// Initialize event listeners
inputText.addEventListener('input', () => {
  const len = inputText.value.length;
  charCount.textContent = `${len} / 500`;
  if (len > 0) {
    hideWarning();
  }
});

// Setup audio loop defaults and state bindings
Object.keys(audioPlayers).forEach(key => {
  audioPlayers[key].loop = true;
  
  audioPlayers[key].addEventListener('play', () => {
    setPlayState(key, true);
  });
  
  audioPlayers[key].addEventListener('pause', () => {
    setPlayState(key, false);
  });
  
  audioPlayers[key].addEventListener('ended', () => {
    if (loopState[key]) {
      // Fallback for mobile browsers where native HTML5 loop might trigger ended event
      audioPlayers[key].currentTime = 0;
      audioPlayers[key].play().catch(e => console.error('Audio loop playback failed:', e));
    } else {
      setPlayState(key, false);
    }
  });
});

// Set translator mode
function setMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  if (mode === 'auto') {
    document.getElementById('mode-auto').classList.add('active');
    inputText.placeholder = "請輸入中文或英文進行翻譯 (系統將自動偵測)...";
  } else if (mode === 'zh-en') {
    document.getElementById('mode-zh-en').classList.add('active');
    inputText.placeholder = "請輸入中文翻譯成英文...";
  } else if (mode === 'en-zh') {
    document.getElementById('mode-en-zh').classList.add('active');
    inputText.placeholder = "請輸入英文翻譯成中文...";
  }
}

// Display warning
function showWarning(msg) {
  warningText.textContent = msg;
  warningBox.classList.add('show');
}

// Hide warning
function hideWarning() {
  warningBox.classList.remove('show');
}

// Validate input text helper
function validateInput(text) {
  if (!text.trim()) {
    return { valid: false, message: '請輸入需要翻譯的文字。' };
  }
  
  const cleanText = text.trim();
  
  // Guard: Reject non-Chinese and non-English scripts
  const foreignScriptRegex = /[\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]/;
  if (foreignScriptRegex.test(cleanText)) {
    return { valid: false, message: '只接受中文與英文。請勿輸入其他語言（如日文、韓文等）。' };
  }
  
  const hasChinese = /[\u4e00-\u9fa5]/.test(cleanText);
  const hasEnglish = /[a-zA-Z]/.test(cleanText);
  
  if (!hasChinese && !hasEnglish) {
    return { valid: false, message: '請輸入有效的中文或英文單字或句子（不可僅輸入符號或數字）。' };
  }
  
  let sl = 'auto';
  let tl = 'en';
  
  if (currentMode === 'auto') {
    if (hasChinese) {
      sl = 'zh-CN';
      tl = 'en';
    } else {
      sl = 'en';
      tl = 'zh-TW';
    }
  } else if (currentMode === 'zh-en') {
    if (!hasChinese && hasEnglish) {
      return { valid: false, message: '目前設定為 [中文 ➔ 英文] 模式，但偵測到您輸入的是英文，請切換模式或輸入中文。' };
    }
    sl = 'zh-CN';
    tl = 'en';
  } else if (currentMode === 'en-zh') {
    if (!hasEnglish && hasChinese) {
      return { valid: false, message: '目前設定為 [英文 ➔ 中文] 模式，但偵測到您輸入的是中文，請切換模式或輸入英文。' };
    }
    sl = 'en';
    tl = 'zh-TW';
  }
  
  return { valid: true, sl, tl };
}

// Generate YYYYMMDD_HHMM timestamp
function getFormattedTimestamp() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  return `${yyyy}${mm}${dd}_${hh}${min}`;
}

// Clean text for filename safety
function cleanFilenameText(text) {
  return text.trim()
    .replace(/[\r\n\t]+/g, ' ')
    .replace(/[\\\/:*?"<>|]/g, '') // remove illegal characters on Windows
    .substring(0, 25);
}

// Helper to render tokenized KK phonetic grid (Main Translation ONLY)
function renderPhoneticGrid(container, tokenGrid) {
  container.innerHTML = '';
  if (!tokenGrid || tokenGrid.length === 0) {
    container.style.display = 'none';
    return;
  }
  
  tokenGrid.forEach(token => {
    const tokenEl = document.createElement('div');
    tokenEl.className = 'phonetic-token';
    
    const wordEl = document.createElement('span');
    wordEl.className = 'phonetic-word';
    wordEl.textContent = token.word;
    tokenEl.appendChild(wordEl);
    
    if (token.kk) {
      const kkEl = document.createElement('span');
      kkEl.className = 'phonetic-kk';
      kkEl.textContent = `[${token.kk}]`;
      tokenEl.appendChild(kkEl);
    } else {
      tokenEl.classList.add('punctuation');
      const kkEl = document.createElement('span');
      kkEl.className = 'phonetic-kk';
      tokenEl.appendChild(kkEl);
    }
    
    container.appendChild(tokenEl);
  });
}

// Set up UI shimmer states
function showLoading() {
  resultsArea.classList.add('show');
  
  // Main Shimmer
  document.getElementById('translation-output').innerHTML = '<div class="shimmer shimmer-block-text"></div>';
  const mainGrid = document.getElementById('phonetic-grid');
  mainGrid.parentNode.style.display = 'block';
  mainGrid.innerHTML = '<div class="shimmer shimmer-block-kk" style="width: 70%;"></div>';
  
  // 3 Example Shimmers
  document.getElementById('example-sentences-list').innerHTML = `
    <div class="example-item shimmer-placeholder" style="margin-bottom: 1.5rem;">
      <div class="shimmer shimmer-block-text" style="width: 80%;"></div>
      <div class="shimmer shimmer-block-text" style="width: 50%; height: 18px; margin-bottom: 0.5rem;"></div>
      <div class="shimmer shimmer-block-player" style="height: 48px; border-radius: 8px;"></div>
    </div>
    <div class="example-item shimmer-placeholder" style="margin-bottom: 1.5rem;">
      <div class="shimmer shimmer-block-text" style="width: 75%;"></div>
      <div class="shimmer shimmer-block-text" style="width: 45%; height: 18px; margin-bottom: 0.5rem;"></div>
      <div class="shimmer shimmer-block-player" style="height: 48px; border-radius: 8px;"></div>
    </div>
    <div class="example-item shimmer-placeholder">
      <div class="shimmer shimmer-block-text" style="width: 85%;"></div>
      <div class="shimmer shimmer-block-text" style="width: 60%; height: 18px; margin-bottom: 0.5rem;"></div>
      <div class="shimmer shimmer-block-player" style="height: 48px; border-radius: 8px;"></div>
    </div>
  `;
  
  // Disable button
  translateBtn.disabled = true;
  translateBtn.innerHTML = '⚡ 分析中...';
}

function hideLoading() {
  translateBtn.disabled = false;
  translateBtn.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="16 3 21 3 21 8"></polyline>
      <line x1="4" y1="20" x2="21" y2="3"></line>
      <polyline points="21 16 21 21 16 21"></polyline>
      <line x1="15" y1="15" x2="20" y2="20"></line>
      <line x1="4" y1="4" x2="9" y2="9"></line>
    </svg>
    開始翻譯與分析
  `;
}

// Handle translation trigger
async function handleTranslation() {
  // Pause any running audio
  stopAllAudio();
  
  const text = inputText.value;
  const validation = validateInput(text);
  
  if (!validation.valid) {
    showWarning(validation.message);
    resultsArea.classList.remove('show');
    return;
  }
  
  hideWarning();
  showLoading();
  
  try {
    // 1. Fetch Translation (with resilient backend + client direct fallback)
    let transData = null;
    try {
      const transRes = await fetch(`/api/translate?text=${encodeURIComponent(text)}&sl=${validation.sl}&tl=${validation.tl}`);
      if (transRes.ok) {
        transData = await transRes.json();
      }
    } catch (e) {
      console.warn('Backend translation fetch error, trying direct fallback...', e);
    }

    // Direct browser fallback if backend was unavailable or rate-limited
    if (!transData || !transData.translation) {
      try {
        const directRes = await fetch(`https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=${validation.sl}&tl=${validation.tl}&q=${encodeURIComponent(text)}`);
        if (directRes.ok) {
          const directJson = await directRes.json();
          if (Array.isArray(directJson) && directJson.length > 0) {
            const translation = Array.isArray(directJson[0])
              ? directJson.map(item => (Array.isArray(item) ? item[0] : item)).join('')
              : directJson[0];
            const detected = Array.isArray(directJson[0]) ? (directJson[0][1] || validation.sl) : validation.sl;
            transData = { translation, sourceLang: detected, targetLang: validation.tl };
          }
        }
      } catch (directErr) {
        console.warn('Direct client fallback also failed:', directErr);
      }
    }

    if (!transData || !transData.translation) {
      throw new Error('Translation API request failed');
    }
    
    // Update translation text
    document.getElementById('translation-output').textContent = transData.translation;
    
    // Save to learning history log
    saveToHistory(text, currentMode, transData.translation);
    
    // Determine which string represents English (input or translation)
    let enTextForPhonetic = '';
    if (validation.tl === 'en') {
      enTextForPhonetic = transData.translation;
    } else {
      enTextForPhonetic = text;
    }
    
    mainEnglishText = enTextForPhonetic;
    
    // 2. Fetch KK Phonetics for main English text
    const phoneticRes = await fetch(`/api/phonetic?text=${encodeURIComponent(enTextForPhonetic)}`);
    const phoneticGrid = phoneticRes.ok ? await phoneticRes.json() : [];
    
    const pGridContainer = document.getElementById('phonetic-grid');
    const pPanel = document.getElementById('phonetic-panel');
    
    renderPhoneticGrid(pGridContainer, phoneticGrid);
    pPanel.style.display = 'block';
    
    // Set Audio source for Main translation
    audioPlayers.main.src = `/api/tts?lang=en&text=${encodeURIComponent(enTextForPhonetic)}`;
    
    // 3. Fetch Examples (input lang is zh or en)
    const inputLangParam = (validation.sl === 'zh-CN') ? 'zh' : 'en';
    const examplesRes = await fetch(`/api/examples?text=${encodeURIComponent(text)}&lang=${inputLangParam}`);
    const exampleCard = document.getElementById('card-example-result');
    
    if (examplesRes.ok) {
      const examplesData = await examplesRes.json();
      const realExamples = examplesData.examples || [];
      
      if (realExamples.length > 0) {
        exampleCard.style.display = 'block';
        
        // Store examples English sentences for download lookup
        window.examplesEnglishTexts = realExamples.map(ex => ex.english);
        
        // Render Example Sentences List
        const examplesList = document.getElementById('example-sentences-list');
        examplesList.innerHTML = '';
        
        realExamples.forEach((ex, idx) => {
          const playerKey = `example${idx + 1}`;
          
          // Set Audio source for this Example player
          audioPlayers[playerKey].src = `/api/tts?lang=en&text=${encodeURIComponent(ex.english)}`;
          
          const itemDiv = document.createElement('div');
          itemDiv.className = 'example-item';
          itemDiv.style.marginBottom = idx < realExamples.length - 1 ? '1.8rem' : '0';
          
          // Text wrapper
          const textDiv = document.createElement('div');
          textDiv.className = 'example-text';
          
          const engDiv = document.createElement('div');
          engDiv.className = 'sentence-eng';
          engDiv.textContent = ex.english;
          textDiv.appendChild(engDiv);
          
          const chiDiv = document.createElement('div');
          chiDiv.className = 'sentence-chi';
          chiDiv.textContent = ex.chinese;
          textDiv.appendChild(chiDiv);
          
          itemDiv.appendChild(textDiv);
          
          // Custom audio player panel underneath the texts
          const playerDiv = document.createElement('div');
          playerDiv.className = 'custom-audio-player';
          playerDiv.style.marginTop = '0.8rem';
          
          playerDiv.innerHTML = `
            <div class="player-controls">
              <button id="${playerKey}-play-btn" class="play-pause-btn" onclick="togglePlay('${playerKey}')">
                <svg id="${playerKey}-play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg id="${playerKey}-pause-icon" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
              </button>
              <div class="player-info">
                <span class="player-label">例句 ${idx + 1} 語音</span>
                <span id="${playerKey}-player-status" class="player-status">已停止播放</span>
              </div>
            </div>
            <div class="player-actions">
              <button id="${playerKey}-loop-btn" class="player-btn ${loopState[playerKey] ? 'loop-active' : ''}" onclick="toggleLoop('${playerKey}')">
                ${loopState[playerKey] ? '🔄 循環播放' : '🔄 單次播放'}
              </button>
              <button id="${playerKey}-download-btn" class="player-btn download-btn" onclick="downloadAudio('${playerKey}')">
                📥 下載音檔
              </button>
            </div>
          `;
          itemDiv.appendChild(playerDiv);
          examplesList.appendChild(itemDiv);
        });
      } else {
        exampleCard.style.display = 'none';
      }
    } else {
      exampleCard.style.display = 'none';
    }
  } catch (err) {
    console.error('Processing failed:', err);
    showWarning('翻譯與發音分析出錯，請稍後再試。');
    resultsArea.classList.remove('show');
  } finally {
    hideLoading();
  }
}

// Audio Player controls
function setPlayState(playerKey, isPlaying) {
  playState[playerKey] = isPlaying;
  
  const playIcon = document.getElementById(`${playerKey}-play-icon`);
  const pauseIcon = document.getElementById(`${playerKey}-pause-icon`);
  const statusLabel = document.getElementById(`${playerKey}-player-status`);
  
  if (isPlaying) {
    if (playIcon) playIcon.style.display = 'none';
    if (pauseIcon) pauseIcon.style.display = 'block';
    if (statusLabel) {
      statusLabel.textContent = loopState[playerKey] ? '循環播放中...' : '單次播放中...';
      statusLabel.style.color = '#34d399';
    }
  } else {
    if (playIcon) playIcon.style.display = 'block';
    if (pauseIcon) pauseIcon.style.display = 'none';
    if (statusLabel) {
      statusLabel.textContent = '已停止播放';
      statusLabel.style.color = 'var(--text-muted)';
    }
  }
}

function togglePlay(playerKey) {
  const audio = audioPlayers[playerKey];
  if (!audio || !audio.src) return;
  
  if (playState[playerKey]) {
    audio.pause();
  } else {
    // Pause other audios first so sounds don't overlay
    stopAllAudioExcept(playerKey);
    audio.play().catch(e => console.error('Audio playback failed:', e));
  }
}

function toggleLoop(playerKey) {
  const audio = audioPlayers[playerKey];
  const btn = document.getElementById(`${playerKey}-loop-btn`);
  
  if (!audio || !btn) return;
  
  loopState[playerKey] = !loopState[playerKey];
  audio.loop = loopState[playerKey];
  
  if (loopState[playerKey]) {
    btn.classList.add('loop-active');
    btn.innerHTML = '🔄 循環播放';
    if (playState[playerKey]) {
      document.getElementById(`${playerKey}-player-status`).textContent = '循環播放中...';
    }
  } else {
    btn.classList.remove('loop-active');
    btn.innerHTML = '🔄 單次播放';
    if (playState[playerKey]) {
      document.getElementById(`${playerKey}-player-status`).textContent = '單次播放中...';
    }
  }
}

function stopAllAudio() {
  Object.keys(audioPlayers).forEach(key => {
    const audio = audioPlayers[key];
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
  });
}

function stopAllAudioExcept(exceptKey) {
  Object.keys(audioPlayers).forEach(key => {
    if (key !== exceptKey) {
      const audio = audioPlayers[key];
      if (audio) {
        audio.pause();
        audio.currentTime = 0;
      }
    }
  });
}

// Download Audio endpoint trigger
function downloadAudio(playerKey) {
  let textToSpeak = '';
  let suffix = '';
  
  if (playerKey === 'main') {
    textToSpeak = mainEnglishText;
    suffix = '';
  } else if (playerKey.startsWith('example')) {
    const idx = parseInt(playerKey.replace('example', ''), 10);
    if (window.examplesEnglishTexts && window.examplesEnglishTexts[idx - 1]) {
      textToSpeak = window.examplesEnglishTexts[idx - 1];
      suffix = `—例句${idx}`;
    }
  }
  
  if (!textToSpeak) return;
  
  const timestamp = getFormattedTimestamp();
  const rawInput = inputText.value;
  const cleanInput = cleanFilenameText(rawInput);
  
  // Format: timestamp_inputtext_suffix.mp3
  const filename = `${timestamp}_${cleanInput}${suffix}.mp3`;
  
  const downloadUrl = `/api/tts/download?lang=en&text=${encodeURIComponent(textToSpeak)}&filename=${encodeURIComponent(filename)}`;
  
  // Trigger file download (Support both Mobile/Android Download Manager & Desktop)
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  if (isMobile) {
    window.location.href = downloadUrl;
  } else {
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

// ==========================================
// Cross-Device Synced History System (/api/history + localStorage fallback)
// ==========================================
const HISTORY_KEY = 'engrepeat_history_v3';
let currentHistoryState = [];

function getLocalHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function setLocalHistory(history) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch (e) {}
}

async function fetchRemoteHistory() {
  try {
    const res = await fetch('/api/history');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.history)) {
        currentHistoryState = data.history;
        setLocalHistory(currentHistoryState);
        renderHistory();
        return;
      }
    }
  } catch (e) {
    console.error('Failed to fetch remote history:', e);
  }
  // Fallback to local storage
  currentHistoryState = getLocalHistory();
  renderHistory();
}

async function saveToHistory(text, mode, translation) {
  const cleanText = text.trim();
  if (!cleanText) return;

  let modeLabel = '🔍 自動';
  if (mode === 'zh-en') modeLabel = '🇨🇳 ➔ 🇺🇸';
  if (mode === 'en-zh') modeLabel = '🇺🇸 ➔ 🇨🇳';

  // 1. Post to server to sync across all devices
  try {
    const res = await fetch('/api/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input: cleanText,
        mode: mode,
        modeLabel: modeLabel,
        translation: translation
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.history)) {
        currentHistoryState = data.history;
        setLocalHistory(currentHistoryState);
        renderHistory();
        return;
      }
    }
  } catch (e) {
    console.error('Failed to post history to server:', e);
  }

  // 2. Local fallback if server call fails
  const now = new Date();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  const timeStr = `${mm}/${dd} ${hh}:${min}`;

  currentHistoryState = currentHistoryState.filter(item => item.input.toLowerCase() !== cleanText.toLowerCase());
  currentHistoryState.unshift({
    id: Date.now(),
    input: cleanText,
    mode: mode,
    modeLabel: modeLabel,
    translation: translation,
    time: timeStr
  });
  setLocalHistory(currentHistoryState);
  renderHistory();
}

async function deleteHistoryItem(id, event) {
  if (event) event.stopPropagation();
  
  // 1. Sync deletion to server
  try {
    const res = await fetch(`/api/history?id=${id}`, { method: 'DELETE' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.history)) {
        currentHistoryState = data.history;
        setLocalHistory(currentHistoryState);
        renderHistory();
        return;
      }
    }
  } catch (e) {
    console.error('Failed to delete history item on server:', e);
  }

  // 2. Local fallback
  currentHistoryState = currentHistoryState.filter(item => String(item.id) !== String(id));
  setLocalHistory(currentHistoryState);
  renderHistory();
}

async function clearAllHistory() {
  if (!confirm('確定要清空所有跨裝置的學習歷史紀錄嗎？')) return;

  try {
    const res = await fetch('/api/history', { method: 'DELETE' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.history)) {
        currentHistoryState = data.history;
        setLocalHistory(currentHistoryState);
        renderHistory();
        return;
      }
    }
  } catch (e) {
    console.error('Failed to clear history on server:', e);
  }

  currentHistoryState = [];
  setLocalHistory([]);
  renderHistory();
}

function restoreHistoryItem(id) {
  const item = currentHistoryState.find(it => String(it.id) === String(id));
  if (!item) return;

  inputText.value = item.input;
  charCount.textContent = `${item.input.length} / 500`;
  setMode(item.mode || 'auto');
  
  // Smooth scroll up to input card
  window.scrollTo({ top: 0, behavior: 'smooth' });
  
  // Trigger translation
  handleTranslation();
}

function renderHistory() {
  const historyList = document.getElementById('history-list');
  if (!historyList) return;

  historyList.innerHTML = '';

  if (!currentHistoryState || currentHistoryState.length === 0) {
    historyList.innerHTML = `
      <div class="history-empty">
        尚無學習歷史紀錄。當您在 PC 或手機上輸入單字翻譯後，系統會自動同步儲存於此，方便隨時跨裝置點擊複習！
      </div>
    `;
    return;
  }

  currentHistoryState.forEach(item => {
    const card = document.createElement('div');
    card.className = 'history-chip-card';
    card.onclick = () => restoreHistoryItem(item.id);

    card.innerHTML = `
      <div class="history-chip-header">
        <span class="history-chip-mode">${item.modeLabel || '自動偵測'}</span>
        <span class="history-chip-time">${item.time}</span>
      </div>
      <div class="history-chip-body">
        <div class="history-chip-input" title="${item.input}">${item.input}</div>
        <div class="history-chip-translation" title="${item.translation}">${item.translation}</div>
      </div>
      <button class="history-chip-delete" onclick="deleteHistoryItem(${item.id}, event)" title="刪除此紀錄">
        ✕
      </button>
    `;

    historyList.appendChild(card);
  });
}

// Initial fetch from server & auto-sync when window gains focus or periodically
fetchRemoteHistory();
window.addEventListener('focus', fetchRemoteHistory);
setInterval(fetchRemoteHistory, 15000); // sync every 15s automatically

