import argparse
import asyncio
import os
import sys

# 嘗試使用微軟高品質神經網路語音 (edge-tts)
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

# 備用語音引擎 (gTTS)
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


# 常用音色別名速查表
VOICE_MAP = {
    # 英文 (English) - 各種口音
    "en": "en-US-JennyNeural",                # 美式英文 (預設女聲)
    "en-female": "en-US-JennyNeural",         # 美式英文 (Jenny，女聲)
    "en-male": "en-US-GuyNeural",             # 美式英文 (Guy，男聲)
    "en-aria": "en-US-AriaNeural",            # 美式英文 (Aria，自然生動女聲)
    "en-gb-female": "en-GB-SoniaNeural",      # 英式英文 (Sonia，女聲)
    "en-gb-male": "en-GB-RyanNeural",         # 英式英文 (Ryan，男聲)
    "en-au": "en-AU-NatashaNeural",           # 澳洲英文 (Natasha，女聲)

    # 繁體中文 (台灣 / 香港)
    "zh-tw": "zh-TW-HsiaoChenNeural",         # 台灣繁中 (預設女聲)
    "zh-tw-female": "zh-TW-HsiaoChenNeural",  # 台灣繁中 (曉臻，女聲)
    "zh-tw-male": "zh-TW-YunJheNeural",       # 台灣繁中 (雲哲，男聲)
    "zh-hk": "zh-HK-HiuMaanNeural",           # 香港粵語 (曉曼，女聲)

    # 簡體中文
    "zh-cn": "zh-CN-XiaoxiaoNeural",          # 大陸簡中 (預設女聲)
    "zh-cn-female": "zh-CN-XiaoxiaoNeural",   # 簡中 (曉曉，女聲)
    "zh-cn-male": "zh-CN-YunjianNeural",      # 簡中 (雲健，男聲)

    # 其他主要外語
    "ja": "ja-JP-NanamiNeural",               # 日語 (Nanami，女聲)
    "ja-female": "ja-JP-NanamiNeural",
    "ja-male": "ja-JP-KeitaNeural",           # 日語 (Keita，男聲)
    "ko": "ko-KR-SunHiNeural",                # 韓語 (SunHi，女聲)
    "fr": "fr-FR-DeniseNeural",               # 法語 (Denise，女聲)
    "de": "de-DE-KatjaNeural",                # 德語 (Katja，女聲)
    "es": "es-ES-ElviraNeural",               # 西班牙語 (Elvira，女聲)
}


def detect_language(text: str) -> str:
    """自動偵測文字主要語系 (英文 / 中文)"""
    cjk_count = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    latin_count = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cjk_count > 0 and cjk_count >= latin_count * 0.15:
        return "zh-tw"
    return "en"


async def list_all_voices(filter_locale: str = None):
    """列出 Edge TTS 支援的聲音列表"""
    if not HAS_EDGE_TTS:
        print("未安裝 edge-tts，無法查詢語音清單。")
        return
    voices = await edge_tts.list_voices()
    filtered = [v for v in voices if not filter_locale or filter_locale.lower() in v['Locale'].lower()]
    print(f"找到 {len(filtered)} 個可用語音 (過濾條件: {filter_locale or '全部'}):")
    print(f"{'語系代號':<15} {'性別':<8} {'模型名稱 (Voice ID)':<30}")
    print("-" * 60)
    for v in filtered[:40]:  # 顯示前 40 筆
        print(f"{v['Locale']:<15} {v['Gender']:<8} {v['ShortName']:<30}")
    if len(filtered) > 40:
        print(f"...還有 {len(filtered) - 40} 個語音未列出。")


async def text_to_speech_edge(text: str, output_path: str, voice: str, rate: str = "+0%", volume: str = "+0%"):
    """使用 Edge TTS 生成語音"""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(output_path)


def text_to_speech_gtts(text: str, output_path: str, lang: str = "en"):
    """使用 Google TTS (gTTS) 生成語音"""
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="TTS 文字轉語音腳本 (支援全球 140+ 種語言與自動語系偵測)")
    parser.add_argument("text", nargs="?", help="要轉換的文字內容。若不提供則會以互動式輸入。")
    parser.add_argument("-o", "--output", default="output.mp3", help="輸出的音訊檔案路徑 (預設: output.mp3)")
    parser.add_argument("-v", "--voice", default=None, 
                        help="語音角色，可填別名 (如 en, en-female, en-male, en-gb, zh-tw) 或直接填微軟 Voice ID")
    parser.add_argument("-r", "--rate", default="+0%", help="語速調整，例如 '+20%%' 或 '-10%%' (預設: +0%%)")
    parser.add_argument("-f", "--file", help="從文字檔案讀取要轉換的內容")
    parser.add_argument("--list-voices", nargs="?", const="all", help="查詢支援的語音清單 (可指定語系過濾，例如: --list-voices en 或 zh)")
    parser.add_argument("--engine", choices=["edge", "gtts"], default="edge", help="指定使用的 TTS 引擎 (預設: edge)")

    args = parser.parse_args()

    # 查詢語音清單功能
    if args.list_voices:
        filter_locale = None if args.list_voices == "all" else args.list_voices
        asyncio.run(list_all_voices(filter_locale))
        return

    # 取得文字內容
    text = ""
    if args.file:
        if not os.path.exists(args.file):
            print(f"錯誤：找不到檔案 {args.file}")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read().strip()
    elif args.text:
        text = args.text.strip()
    else:
        print("=== 文字轉語音 (Text-to-Speech) ===")
        try:
            text = input("請輸入要轉換為語音的文字：\n> ").strip()
        except KeyboardInterrupt:
            print("\n已取消操作。")
            sys.exit(0)

    if not text:
        print("錯誤：輸入的文字不可為空！")
        sys.exit(1)

    # 決定發音角色 (若未手動指定 -v，則自動偵測語系)
    if args.voice:
        selected_voice = VOICE_MAP.get(args.voice.lower(), args.voice)
    else:
        detected_lang = detect_language(text)
        if detected_lang == "en":
            selected_voice = VOICE_MAP["en-female"]
            print("[語系偵測] 偵測為英文，自動採用美式英文自然語音 (Jenny)")
        else:
            selected_voice = VOICE_MAP["zh-tw-female"]
            print("[語系偵測] 偵測為中文，自動採用台灣繁體中文語音 (曉臻)")

    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print(f"\n正在處理轉換...")
    print(f"文字內容 (前 60 字): {text[:60]}{'...' if len(text) > 60 else ''}")

    # 執行 TTS 轉換
    if args.engine == "edge" and HAS_EDGE_TTS:
        print(f"使用的引擎: Edge TTS (高品質神經網路語音)")
        print(f"使用的音色: {selected_voice}")
        print(f"語速設定: {args.rate}")
        try:
            asyncio.run(text_to_speech_edge(text, output_path, voice=selected_voice, rate=args.rate))
            print(f"\n轉換成功！音訊已儲存至：\n{output_path}")
        except Exception as e:
            print(f"Edge TTS 執行時發生錯誤: {e}")
            if HAS_GTTS:
                print("自動切換為備用引擎 (gTTS)...")
                lang_code = "en" if "en-" in selected_voice.lower() else "zh-TW"
                text_to_speech_gtts(text, output_path, lang=lang_code)
                print(f"轉換成功！音訊已儲存至：\n{output_path}")
            else:
                sys.exit(1)
    elif HAS_GTTS:
        print(f"使用的引擎: Google TTS (gTTS)")
        try:
            lang_code = "en" if detect_language(text) == "en" else "zh-TW"
            text_to_speech_gtts(text, output_path, lang=lang_code)
            print(f"\n轉換成功！音訊已儲存至：\n{output_path}")
        except Exception as e:
            print(f"gTTS 執行時發生錯誤: {e}")
            sys.exit(1)
    else:
        print("錯誤：尚未安裝任何 TTS 模組！請執行 pip install edge-tts 或 pip install gTTS")
        sys.exit(1)


if __name__ == "__main__":
    main()
