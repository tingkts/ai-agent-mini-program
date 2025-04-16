const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const CACHE_FILE = path.join(__dirname, 'phonetics_cache.json');
let phoneticsCache = {};

const HISTORY_FILE = path.join(__dirname, 'history_store.json');
let globalHistory = [];

// Load cache from file if it exists
if (fs.existsSync(CACHE_FILE)) {
  try {
    phoneticsCache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
  } catch (err) {
    console.error('Error reading phonetics cache:', err);
    phoneticsCache = {};
  }
}

// Load history store from file if it exists
if (fs.existsSync(HISTORY_FILE)) {
  try {
    globalHistory = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
  } catch (err) {
    console.error('Error reading history store:', err);
    globalHistory = [];
  }
}

// Helper to save cache to file
function saveCache() {
  try {
    fs.writeFileSync(CACHE_FILE, JSON.stringify(phoneticsCache, null, 2), 'utf8');
  } catch (err) {
    console.error('Error saving phonetics cache:', err);
  }
}

// Helper to save history store to file
function saveHistoryStore() {
  try {
    fs.writeFileSync(HISTORY_FILE, JSON.stringify(globalHistory, null, 2), 'utf8');
  } catch (err) {
    console.error('Error saving history store:', err);
  }
}

// GET /api/history - Retrieve shared history items across all devices
app.get('/api/history', (req, res) => {
  res.json({ history: globalHistory });
});

// POST /api/history - Add/Update a history item across devices
app.post('/api/history', (req, res) => {
  const { input, mode, modeLabel, translation } = req.body;
  if (!input || !translation) {
    return res.status(400).json({ error: 'Input and translation are required' });
  }

  const cleanText = input.trim();
  const now = new Date();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  const timeStr = `${mm}/${dd} ${hh}:${min}`;

  // Filter out duplicate inputs (case-insensitive)
  globalHistory = globalHistory.filter(item => item.input.toLowerCase() !== cleanText.toLowerCase());

  // Insert at top of global history array
  globalHistory.unshift({
    id: Date.now(),
    input: cleanText,
    mode: mode || 'auto',
    modeLabel: modeLabel || '🔍 自動',
    translation: translation,
    time: timeStr
  });

  // Limit max size to 50 items across devices
  if (globalHistory.length > 50) {
    globalHistory = globalHistory.slice(0, 50);
  }

  saveHistoryStore();
  res.json({ success: true, history: globalHistory });
});

// DELETE /api/history - Delete single item or clear all
app.delete('/api/history', (req, res) => {
  const { id } = req.query;
  if (id) {
    globalHistory = globalHistory.filter(item => String(item.id) !== String(id));
  } else {
    globalHistory = [];
  }
  saveHistoryStore();
  res.json({ success: true, history: globalHistory });
});

// IPA to KK conversion logic
function ipaToKk(ipa) {
  if (!ipa) return '';
  
  // Clean up slashes, brackets, and periods (syllable boundaries)
  let kk = ipa.replace(/[\/\[\]\.]/g, '');
  
  // Replace IPA dipthongs/vowels with KK counterparts
  const replacements = [
    // Long vowels
    { pattern: /eɪ/g, replace: 'e' },
    { pattern: /oʊ/g, replace: 'o' },
    { pattern: /əʊ/g, replace: 'o' }, // UK long o
    { pattern: /iː/g, replace: 'i' },
    { pattern: /uː/g, replace: 'u' },
    { pattern: /ɑː/g, replace: 'ɑ' },
    { pattern: /ɔː/g, replace: 'ɔ' },
    
    // Rhotics (American r-colored vowels)
    { pattern: /ɜːr/g, replace: 'ɝ' },
    { pattern: /ɝː/g, replace: 'ɝ' },
    { pattern: /ɜr/g, replace: 'ɝ' },
    { pattern: /ər/g, replace: 'ɚ' },
    { pattern: /ɚː/g, replace: 'ɚ' },
    { pattern: /ə˞/g, replace: 'ɚ' },
    { pattern: /ɜ˞/g, replace: 'ɝ' },
    
    // Consonants and other symbols
    { pattern: /ɹ/g, replace: 'r' },
    { pattern: /g/g, replace: 'g' },
  ];
  
  replacements.forEach(({ pattern, replace }) => {
    kk = kk.replace(pattern, replace);
  });
  
  return kk.trim();
}

// Clean word helper
function cleanWordForLookup(word) {
  return word.toLowerCase().replace(/[^a-z']/g, '').trim();
}

// Fetch phonetic symbol from dictionary API and convert to KK
async function getWordKKPhonetic(word) {
  const clean = cleanWordForLookup(word);
  if (!clean) return '';
  
  if (phoneticsCache[clean]) {
    return phoneticsCache[clean];
  }
  
  try {
    const url = `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(clean)}`;
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      signal: AbortSignal.timeout(5000)
    });
    
    if (!res.ok) {
      // Word not found or API error
      return '';
    }
    
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) return '';
    
    // Look for a phonetic IPA spelling
    let ipa = '';
    
    // Check main level phonetic field
    if (data[0].phonetic) {
      ipa = data[0].phonetic;
    } else if (data[0].phonetics && data[0].phonetics.length > 0) {
      // Find the first non-empty phonetic text
      const item = data[0].phonetics.find(p => p.text);
      if (item) ipa = item.text;
    }
    
    if (ipa) {
      const kk = ipaToKk(ipa);
      phoneticsCache[clean] = kk;
      saveCache();
      return kk;
    }
    
    return '';
  } catch (err) {
    console.error(`Error fetching phonetics for ${clean}:`, err.message);
    return '';
  }
}

// Multi-tier translation helper with automatic failover
async function translateText(text, sl = 'auto', tl = 'en') {
  const cleanText = text.trim();
  if (!cleanText) return { translation: '', sourceLang: sl, targetLang: tl };

  // Tier 1: clients5.google.com with dict-chrome-ex (high reliability, low rate limiting)
  try {
    const url = `https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=${sl}&tl=${tl}&q=${encodeURIComponent(cleanText)}`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': '*/*'
      },
      signal: AbortSignal.timeout(5000)
    });
    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        if (Array.isArray(data[0])) {
          const translation = data.map(item => (Array.isArray(item) ? item[0] : item)).join('');
          const detected = data[0][1] || sl;
          if (translation) {
            return { translation, sourceLang: detected, targetLang: tl };
          }
        } else if (typeof data[0] === 'string') {
          return { translation: data[0], sourceLang: data[1] || sl, targetLang: tl };
        }
      }
    }
  } catch (err) {
    console.warn('Translate Tier 1 failed:', err.message);
  }

  // Tier 2: translate.googleapis.com with client=dict-chrome-ex
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl=${sl}&tl=${tl}&dt=t&q=${encodeURIComponent(cleanText)}`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
      },
      signal: AbortSignal.timeout(5000)
    });
    if (response.ok) {
      const data = await response.json();
      if (data && data[0]) {
        const translation = data[0].map(item => item[0]).join('');
        const sourceLang = data[2] || sl;
        if (translation) {
          return { translation, sourceLang, targetLang: tl };
        }
      }
    }
  } catch (err) {
    console.warn('Translate Tier 2 failed:', err.message);
  }

  // Tier 3: translate.googleapis.com with client=gtx
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sl}&tl=${tl}&dt=t&q=${encodeURIComponent(cleanText)}`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      signal: AbortSignal.timeout(5000)
    });
    if (response.ok) {
      const data = await response.json();
      if (data && data[0]) {
        const translation = data[0].map(item => item[0]).join('');
        const sourceLang = data[2] || sl;
        if (translation) {
          return { translation, sourceLang, targetLang: tl };
        }
      }
    }
  } catch (err) {
    console.warn('Translate Tier 3 failed:', err.message);
  }

  // Tier 4: MyMemory API Fallback (great safety net against Google 429)
  try {
    const pairSl = (sl === 'auto' || sl === 'en') ? 'en' : (sl.includes('zh') ? 'zh-TW' : sl);
    const pairTl = tl.includes('zh') ? 'zh-TW' : tl;
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(cleanText)}&langpair=${pairSl}|${pairTl}`;
    const response = await fetch(url, { signal: AbortSignal.timeout(6000) });
    if (response.ok) {
      const data = await response.json();
      if (data && data.responseData && data.responseData.translatedText) {
        return {
          translation: data.responseData.translatedText,
          sourceLang: sl,
          targetLang: tl
        };
      }
    }
  } catch (err) {
    console.warn('Translate Tier 4 (MyMemory) failed:', err.message);
  }

  throw new Error('All translation services failed or rate limited');
}

// Translate API endpoint
app.get('/api/translate', async (req, res) => {
  const { text, sl = 'auto', tl = 'en' } = req.query;
  if (!text) {
    return res.status(400).json({ error: 'Text parameter is required' });
  }
  
  try {
    const result = await translateText(text, sl, tl);
    res.json(result);
  } catch (err) {
    console.error('Translation error:', err);
    res.status(500).json({ error: 'Translation failed', details: err.message });
  }
});

// TTS audio stream proxy
app.get('/api/tts', async (req, res) => {
  const { text, lang = 'en' } = req.query;
  if (!text) {
    return res.status(400).send('Text is required');
  }
  
  try {
    const ttsUrl = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${lang}&client=tw-ob&q=${encodeURIComponent(text)}`;
    const response = await fetch(ttsUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Google TTS responded with ${response.status}`);
    }
    
    res.setHeader('Content-Type', 'audio/mpeg');
    const arrayBuffer = await response.arrayBuffer();
    res.send(Buffer.from(arrayBuffer));
  } catch (err) {
    console.error('TTS error:', err);
    res.status(500).send('TTS generation failed');
  }
});

// TTS download proxy with attachment headers
app.get('/api/tts/download', async (req, res) => {
  const { text, lang = 'en', filename = 'audio.mp3' } = req.query;
  if (!text) {
    return res.status(400).send('Text is required');
  }
  
  try {
    const ttsUrl = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${lang}&client=tw-ob&q=${encodeURIComponent(text)}`;
    const response = await fetch(ttsUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Google TTS responded with ${response.status}`);
    }
    
    res.setHeader('Content-Type', 'audio/mpeg');
    // Ensure filename is safe and properly formatted for Content-Disposition (supports older and newer Android browsers)
    const safeFilename = filename.replace(/[\r\n"]/g, '');
    const encodedFilename = encodeURIComponent(safeFilename);
    res.setHeader('Content-Disposition', `attachment; filename="${encodedFilename}"; filename*=UTF-8''${encodedFilename}`);
    const arrayBuffer = await response.arrayBuffer();
    res.send(Buffer.from(arrayBuffer));
  } catch (err) {
    console.error('TTS download error:', err);
    res.status(500).send('TTS download failed');
  }
});

// Phonetics endpoint (sentence-level)
app.get('/api/phonetic', async (req, res) => {
  const { text } = req.query;
  if (!text) {
    return res.json([]);
  }
  
  try {
    // Tokenize into words and punctuation
    const tokens = text.match(/[a-zA-Z']+|[^a-zA-Z'\s]+/g) || [];
    const results = await Promise.all(
      tokens.map(async (token) => {
        const isWord = /[a-zA-Z]/.test(token);
        if (isWord) {
          const kk = await getWordKKPhonetic(token);
          return { word: token, kk };
        }
        return { word: token, kk: '' };
      })
    );
    
    res.json(results);
  } catch (err) {
    console.error('Phonetic retrieval error:', err);
    res.status(500).json({ error: 'Failed to retrieve phonetics' });
  }
});

// Multi-source real example sentence generator (No dummy fallbacks)
app.get('/api/examples', async (req, res) => {
  const { text, lang } = req.query;
  if (!text) {
    return res.status(400).json({ error: 'Text parameter is required' });
  }
  
  try {
    let englishText = text;
    
    // If input is Chinese, get English translation first
    if (lang === 'zh') {
      try {
        const transRes = await translateText(text, 'zh-CN', 'en');
        if (transRes.translation) {
          englishText = transRes.translation;
        }
      } catch (e) {}
    }
    
    // Extract candidate keywords from English text
    const words = englishText.match(/[a-zA-Z']+/g) || [];
    const stopWords = new Set([
      'the', 'a', 'an', 'and', 'but', 'or', 'if', 'because', 'as', 'what', 'why', 'how',
      'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
      'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'ours', 'theirs',
      'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
      'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should',
      'can', 'could', 'may', 'might', 'must', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
      'by', 'from', 'about', 'get', 'got'
    ]);
    
    const candidates = words.filter(w => !stopWords.has(w.toLowerCase()) && w.length > 2);
    const keywords = candidates.length > 0 ? candidates : words;
    
    // Helper function to translate English sentence to Traditional Chinese
    const translateToChinese = async (engText) => {
      try {
        const transRes = await translateText(engText, 'en', 'zh-TW');
        return transRes.translation || '';
      } catch (err) {
        return '';
      }
    };
    
    const rawSentences = [];
    const seen = new Set();
    
    function addSentence(s) {
      if (!s) return;
      const clean = s.replace(/<[^>]*>/g, '').replace(/[\r\n\t]+/g, ' ').trim();
      if (clean.length < 12 || clean.length > 140) return;
      if (clean.includes('&nbsp;') || clean.includes(' ') || clean.endsWith(':')) return;
      const lower = clean.toLowerCase();
      if (seen.has(lower)) return;
      seen.add(lower);
      rawSentences.push(clean);
    }
    
    // Loop through keywords to collect REAL examples from Google Translate, Free Dictionary, Tatoeba
    for (const kw of keywords) {
      if (rawSentences.length >= 5) break;
      const cleanKw = kw.toLowerCase();
      
      // Source 1: Google Translate Dictionary & Usage Examples (using dict-chrome-ex)
      try {
        const gtUrl = `https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl=en&tl=zh-TW&dt=t&dt=bd&dt=ex&dt=md&q=${encodeURIComponent(cleanKw)}`;
        const gtRes = await fetch(gtUrl, {
          headers: { 'User-Agent': 'Mozilla/5.0' },
          signal: AbortSignal.timeout(3000)
        });
        if (gtRes.ok) {
          const gtData = await gtRes.json();
          for (const item of gtData) {
            if (Array.isArray(item)) {
              for (const subItem of item) {
                if (Array.isArray(subItem) && Array.isArray(subItem[1])) {
                  for (const entry of subItem[1]) {
                    if (Array.isArray(entry) && entry.length >= 3 && typeof entry[2] === 'string') {
                      addSentence(entry[2]);
                    }
                  }
                }
              }
            }
          }
        }
      } catch (e) {}
      
      // Source 2: Free Dictionary API
      if (rawSentences.length < 5) {
        try {
          const fdUrl = `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(cleanKw)}`;
          const fdRes = await fetch(fdUrl, {
            headers: { 'User-Agent': 'Mozilla/5.0' },
            signal: AbortSignal.timeout(3000)
          });
          if (fdRes.ok) {
            const fdData = await fdRes.json();
            if (Array.isArray(fdData)) {
              for (const entry of fdData) {
                if (entry.meanings) {
                  for (const meaning of entry.meanings) {
                    if (meaning.definitions) {
                      for (const def of meaning.definitions) {
                        if (def.example) {
                          addSentence(def.example);
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } catch (e) {}
      }
      
      // Source 3: Tatoeba Corpus (Real-world user-contributed sentences)
      if (rawSentences.length < 5) {
        try {
          const tatoebaUrl = `https://api.tatoeba.org/v1/sentences?lang=eng&q=${encodeURIComponent(cleanKw)}&sort=words`;
          const tatoebaRes = await fetch(tatoebaUrl, {
            headers: { 'User-Agent': 'Mozilla/5.0' },
            signal: AbortSignal.timeout(3000)
          });
          if (tatoebaRes.ok) {
            const tatoebaData = await tatoebaRes.json();
            if (tatoebaData && tatoebaData.data && tatoebaData.data.length > 0) {
              const valid = tatoebaData.data.filter(s => s.text && s.text.length >= 18);
              for (const item of valid) {
                addSentence(item.text);
              }
            }
          }
        } catch (e) {}
      }
    }
    
    // Take up to 3 real examples and translate to Traditional Chinese
    const examples = [];
    for (const eng of rawSentences.slice(0, 3)) {
      const chi = await translateToChinese(eng);
      examples.push({
        english: eng,
        chinese: chi || eng
      });
    }
    
    // STRICT REQUIREMENT: Return ONLY real examples found. No dummy templates or fallbacks!
    res.json({
      examples
    });
  } catch (err) {
    console.error('Examples generation error:', err);
    res.json({ examples: [] });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
