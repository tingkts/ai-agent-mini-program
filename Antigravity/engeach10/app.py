import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from gtts import gTTS
import json
import urllib.request
import urllib.error
import urllib.parse

app = Flask(__name__)
DB_NAME = "english_learning.db"
AUDIO_DIR = "static/audio"

# 確保音檔資料夾存在
os.makedirs(AUDIO_DIR, exist_ok=True)

# 內建精選單字庫，在沒有設定 API Key 時提供高品質的水果與機場等主題的 10 個英文學習單字/片語與例句
LOCAL_VOCAB = {
    "水果": [
        {"en": "Apple", "zh": "蘋果", "s_en": "An apple a day keeps the doctor away.", "s_zh": "一日一蘋果，醫生遠離我。"},
        {"en": "Banana", "zh": "香蕉", "s_en": "Bananas are a great source of potassium and energy.", "s_zh": "香蕉是鉀和能量的絕佳來源。"},
        {"en": "Orange", "zh": "柳橙", "s_en": "Oranges are famous for their high vitamin C content.", "s_zh": "柳橙以其高維生素 C 含量而聞名。"},
        {"en": "Strawberry", "zh": "草莓", "s_en": "She loves to eat fresh strawberries with whipped cream.", "s_zh": "她喜歡吃新鮮的草莓配鮮奶油。"},
        {"en": "Grape", "zh": "葡萄", "s_en": "Grapes can be eaten fresh or used to make wine.", "s_zh": "葡萄可以新鮮食用，也可以用來釀酒。"},
        {"en": "Watermelon", "zh": "西瓜", "s_en": "Watermelon is the perfect fruit for a hot summer day.", "s_zh": "西瓜是炎熱夏天的完美水果。"},
        {"en": "Pineapple", "zh": "鳳梨", "s_en": "Pineapples are sweet, acidic, and tropical.", "s_zh": "鳳梨甜中帶酸，具有熱帶風味。"},
        {"en": "Mango", "zh": "芒果", "s_en": "Taiwan is famous for its sweet and juicy mangoes.", "s_zh": "台灣以其甜美多汁的芒果而聞名。"},
        {"en": "Peach", "zh": "水蜜桃", "s_en": "The peach has a soft, velvety skin and sweet flesh.", "s_zh": "水蜜桃擁有柔軟如天鵝絨般的外皮與甜美的果肉。"},
        {"en": "Lemon", "zh": "檸檬", "s_en": "Lemon juice adds a refreshing sour flavor to many dishes.", "s_zh": "檸檬汁為許多菜餚增添了清爽的酸味。"}
    ],
    "機場": [
        {"en": "Boarding pass", "zh": "登機證", "s_en": "Please have your passport and boarding pass ready.", "s_zh": "請準備好您的護照和登機證。"},
        {"en": "Customs", "zh": "海關", "s_en": "You need to declare any fresh food at customs.", "s_zh": "您需要在海關申報任何新鮮食物。"},
        {"en": "Baggage claim", "zh": "行李提領處", "s_en": "We waited for our luggage at the baggage claim area.", "s_zh": "我們在行李提領區等待我們的行李。"},
        {"en": "Departure gate", "zh": "登機門", "s_en": "The flight is boarding at departure gate number twelve.", "s_zh": "該班機正在十二號登機門登機。"},
        {"en": "Security check", "zh": "安全檢查", "s_en": "Remove your laptop from your bag for the security check.", "s_zh": "安全檢查時，請將筆記型電腦從包包中取出。"},
        {"en": "Terminal", "zh": "航廈", "s_en": "International flights depart from Terminal 2.", "s_zh": "國際航班由第二航廈起飛。"},
        {"en": "Duty-free shop", "zh": "免稅店", "s_en": "I bought some perfume at the duty-free shop.", "s_zh": "我在免稅店買了一些香水。"},
        {"en": "Layover", "zh": "轉機停留時間", "s_en": "I have a three-hour layover in Tokyo.", "s_zh": "我在東京有三小時的轉機時間。"},
        {"en": "Check-in counter", "zh": "報到櫃檯", "s_en": "Where is the check-in counter for China Airlines?", "s_zh": "中華航空的報到櫃檯在哪裡？"},
        {"en": "Flight attendant", "zh": "空服員", "s_en": "The flight attendant helped us find our seats.", "s_zh": "空服員幫我們找到了座位。"}
    ],
    "預設": [
        {"en": "Persistence", "zh": "堅持不懈", "s_en": "Success requires persistence and hard work.", "s_zh": "成功需要堅持不懈和努力工作。"},
        {"en": "Consistency", "zh": "一致性/持續性", "s_en": "Consistency is the key to mastering any new language.", "s_zh": "持續性是掌握任何新語言的關鍵。"},
        {"en": "Curiosity", "zh": "好奇心", "s_en": "Children have a natural curiosity about the world.", "s_zh": "孩子們對世界有著自然的好奇心。"},
        {"en": "Empathy", "zh": "同理心", "s_en": "Showing empathy helps build strong relationships.", "s_zh": "展現同理心有助於建立牢固的關係。"},
        {"en": "Creativity", "zh": "創造力", "s_en": "Reading books is a great way to stimulate creativity.", "s_zh": "閱讀書籍是逆發創造力的好方法。"},
        {"en": "Gratitude", "zh": "感激/感恩", "s_en": "Expressing gratitude can improve your mental health.", "s_zh": "表達感恩可以改善你的心理健康。"},
        {"en": "Resilience", "zh": "韌性/復原力", "s_en": "She showed great resilience in overcoming difficulties.", "s_zh": "她在克服困難時展現了極大的韌性。"},
        {"en": "Mindfulness", "zh": "正念", "s_en": "Mindfulness practice can reduce daily stress.", "s_zh": "正念練習可以減輕日常壓力。"},
        {"en": "Optimism", "zh": "樂觀主義", "s_en": "His optimism always keeps the team motivated.", "s_zh": "他的樂觀總是讓團隊保持動力。"},
        {"en": "Integrity", "zh": "正直/誠實", "s_en": "Integrity means doing the right thing when no one is watching.", "s_zh": "正直意味著在沒人看著時做正確的事。"}
    ]
}

def load_env():
    """手動解析 .env 檔案以載入環境變數"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

def get_local_vocab(category):
    """根據輸入類別進行本地字庫的模糊匹配"""
    if not category:
        return LOCAL_VOCAB["預設"]
    cat_str = category.lower()
    if "水" in cat_str and "果" in cat_str:
        return LOCAL_VOCAB["水果"]
    elif "機" in cat_str or "航" in cat_str or "海" in cat_str or "關" in cat_str or "airport" in cat_str:
        return LOCAL_VOCAB["機場"]
    return LOCAL_VOCAB["預設"]

def clean_json_text(text):
    """去除 AI 回傳的 Markdown code block 標記"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def generate_via_gemini(category, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"""
    You are an English teacher. Please generate exactly 10 English vocabulary words, phrases, or short sentences related to the category "{category}" for learning.
    For each item, provide:
    1. The English word/phrase/sentence (en)
    2. The Chinese translation (zh)
    3. An English example sentence using the word/phrase (s_en)
    4. The Chinese translation of the example sentence (s_zh)

    Return ONLY a JSON array of objects with the keys "en", "zh", "s_en", and "s_zh".
    Do not wrap the response in markdown code blocks or add any other text.
    """
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=20) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        text = res_data['candidates'][0]['content']['parts'][0]['text']
        cleaned = clean_json_text(text)
        return json.loads(cleaned)

def generate_via_openai(category, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    prompt = f"""
    You are an English teacher. Please generate exactly 10 English vocabulary words, phrases, or short sentences related to the category "{category}" for learning.
    For each item, provide:
    1. The English word/phrase/sentence (en)
    2. The Chinese translation (zh)
    3. An English example sentence using the word/phrase (s_en)
    4. The Chinese translation of the example sentence (s_zh)

    Return ONLY a JSON array of objects with the keys "en", "zh", "s_en", and "s_zh".
    Do not wrap the response in markdown code blocks or add any other text.
    """
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=20) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        text = res_data['choices'][0]['message']['content']
        cleaned = clean_json_text(text)
        result = json.loads(cleaned)
        if isinstance(result, dict):
            for key, val in result.items():
                if isinstance(val, list):
                    return val
        return result

# 初始化資料庫
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocab_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            batch_name TEXT,
            english TEXT,
            chinese TEXT,
            sentence_en TEXT,
            sentence_zh TEXT,
            audio_file TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    category = request.form.get('category', '').strip()
    
    # 決定使用的資料來源 (優先使用 API，沒有金鑰則使用內建本地庫)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    vocab_items = None
    source = "AI"
    engine = ""
    error_msg = ""
    
    if gemini_key:
        try:
            vocab_items = generate_via_gemini(category, gemini_key)
            engine = "Gemini"
        except Exception as e:
            print(f"Gemini API 呼叫失敗: {e}")
            error_msg = f"Gemini API 錯誤: {str(e)}"
            
    if not vocab_items and openai_key:
        try:
            vocab_items = generate_via_openai(category, openai_key)
            engine = "OpenAI"
        except Exception as e:
            print(f"OpenAI API 呼叫失敗: {e}")
            error_msg = f"OpenAI API 錯誤: {str(e)}"
            
    if not vocab_items:
        # 使用本地預設字庫
        vocab_items = get_local_vocab(category)
        source = "Local"
        if gemini_key or openai_key:
            engine = "API 呼叫失敗 (已降級為本地庫)"
        else:
            engine = "未設定 API 金鑰"

    batch_name = datetime.now().strftime("%Y%m%d_%H%M")
    results = []

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 迴圈處理產生的項目，產生發音 MP3 並寫入資料庫
    for idx, item in enumerate(vocab_items):
        text_to_speak = f"{item['en']}. {item['s_en']}"
        # 產生安全的英文檔名部分 (僅保留英數字、空白、底線、減號，並把空白轉為底線)
        safe_en = "".join(c for c in item['en'] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        filename = f"{batch_name}_{idx}_{safe_en}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename).replace('\\', '/')

        try:
            tts = gTTS(text_to_speak, lang='en', slow=False)
            tts.save(filepath)
        except Exception as e:
            print(f"產生語音檔失敗: {e}")
            # 若 TTS 失敗，將 audio_file 設為空字串，前端播放器會自動跳過此項目
            filepath = ""

        c.execute('''
            INSERT INTO vocab_items (category, batch_name, english, chinese, sentence_en, sentence_zh, audio_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (category, batch_name, item['en'], item['zh'], item['s_en'], item['s_zh'], filepath))

        item['audio_file'] = filepath
        results.append(item)

    conn.commit()
    conn.close()

    return jsonify({"batch_name": batch_name, "items": results, "source": source, "engine": engine, "error_msg": error_msg})

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 根據批次分組，並計算每個批次內有多少項目
    c.execute('''
        SELECT batch_name, category, COUNT(*) as count 
        FROM vocab_items 
        GROUP BY batch_name 
        ORDER BY batch_name DESC
    ''')
    batches = [{"batch_name": row[0], "category": row[1], "count": row[2]} for row in c.fetchall()]
    conn.close()
    return render_template('history.html', batches=batches)

@app.route('/api/batch/<batch_name>', methods=['GET'])
def get_batch_items(batch_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT english, chinese, sentence_en, sentence_zh, audio_file 
        FROM vocab_items 
        WHERE batch_name = ?
    ''', (batch_name,))
    items = [
        {"en": row[0], "zh": row[1], "s_en": row[2], "s_zh": row[3], "audio_file": row[4]} 
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify({"batch_name": batch_name, "items": items})

@app.route('/api/batch/<batch_name>', methods=['DELETE'])
def delete_batch(batch_name):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # 1. 撈出該批次的所有音檔路徑，並從硬碟刪除檔案以節省空間
        c.execute('SELECT audio_file FROM vocab_items WHERE batch_name = ?', (batch_name,))
        files = [row[0] for row in c.fetchall()]
        for filepath in files:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as ex:
                    print(f"刪除硬碟音檔失敗 ({filepath}): {ex}")
                    
        # 2. 從資料庫中刪除該批次的記錄
        c.execute('DELETE FROM vocab_items WHERE batch_name = ?', (batch_name,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"批次 {batch_name} 刪除成功"})
    except Exception as e:
        print(f"刪除批次發生錯誤: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)