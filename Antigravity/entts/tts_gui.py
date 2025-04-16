import asyncio
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

# 導入 TTS 引擎
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


# 常用聲音模型
VOICE_OPTIONS = [
    ("自動偵測語系 (Auto Detect)", "auto"),
    ("🇺🇸 美式英文 - Jenny (女聲, 溫柔自然)", "en-US-JennyNeural"),
    ("🇺🇸 美式英文 - Guy (男聲, 沉穩成熟)", "en-US-GuyNeural"),
    ("🇺🇸 美式英文 - Aria (女聲, 充滿生動)", "en-US-AriaNeural"),
    ("🇬🇧 英式英文 - Sonia (女聲, 典雅英腔)", "en-GB-SoniaNeural"),
    ("🇬🇧 英式英文 - Ryan (男聲, 標準英腔)", "en-GB-RyanNeural"),
    ("🇦🇺 澳洲英文 - Natasha (女聲, 澳洲腔)", "en-AU-NatashaNeural"),
    ("🇹🇼 台灣繁中 - 曉臻 (女聲, 親切清晰)", "zh-TW-HsiaoChenNeural"),
    ("🇹🇼 台灣繁中 - 雲哲 (男聲, 沉穩專業)", "zh-TW-YunJheNeural"),
    ("🇭🇰 香港粵語 - 曉曼 (女聲)", "zh-HK-HiuMaanNeural"),
    ("🇨🇳 簡體中文 - 曉曉 (女聲)", "zh-CN-XiaoxiaoNeural"),
    ("🇯🇵 日語 - Nanami (女聲)", "ja-JP-NanamiNeural"),
    ("🇰🇷 韓語 - SunHi (女聲)", "ko-KR-SunHiNeural"),
]

RATE_OPTIONS = [
    ("標準語速 (+0%)", "+0%"),
    ("稍快 (+10%)", "+10%"),
    ("快速 (+20%)", "+20%"),
    ("極快 (+30%)", "+30%"),
    ("稍慢 (-10%)", "-10%"),
    ("慢速 (-20%)", "-20%"),
]


def sanitize_filename(text: str, max_length: int = 25) -> str:
    """將文字轉換為乾淨合法的檔案名稱，過長時自動截短"""
    if not text or not text.strip():
        return "text.mp3"
    
    # 移除換行與無效字元
    cleaned = re.sub(r'[\\/*?:"<>|\r\n\t]', '', text).strip()
    cleaned = re.sub(r'\s+', '_', cleaned)
    
    if not cleaned:
        return "text.mp3"
    
    # 若文字過長則自動截短
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip('_')
        
    return f"{cleaned}.mp3"


def detect_language(text: str) -> str:
    """自動判斷文字為中文或英文"""
    cjk_count = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    latin_count = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cjk_count > 0 and cjk_count >= latin_count * 0.15:
        return "zh-tw"
    return "en"


class TTSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TTS 文字轉語音工具 (Text to Speech)")
        self.geometry("760x680")
        self.minsize(680, 580)

        # 預設儲存資料夾為目前工作目錄
        self.output_dir = os.path.abspath(os.getcwd())

        # 初始化變數
        self.voice_var = tk.StringVar(value="auto")
        self.rate_var = tk.StringVar(value="+0%")
        self.auto_name_var = tk.BooleanVar(value=True)  # 是否依據文字命名
        self.open_folder_var = tk.BooleanVar(value=True) # 轉換完打開資料夾
        self.auto_play_var = tk.BooleanVar(value=False)  # 轉換完自動播放
        self.filename_preview_var = tk.StringVar(value="text.mp3")

        self.setup_ui()
        self.apply_theme()

    def apply_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            pass

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding="16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 頂部標題區
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🎙️ TTS 文字轉語音工具", font=("Segoe UI", 16, "bold"))
        title_label.pack(side=tk.LEFT)

        subtitle_label = ttk.Label(title_frame, text="支援多國語言 (微軟神經網路高音質)", font=("Segoe UI", 9), foreground="#666666")
        subtitle_label.pack(side=tk.LEFT, padx=12, pady=(6, 0))

        # 2. 文字輸入區
        text_group = ttk.LabelFrame(main_frame, text=" 輸入或貼上文字 (Text Input) ", padding="10")
        text_group.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        toolbar_frame = ttk.Frame(text_group)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))

        btn_paste = ttk.Button(toolbar_frame, text="📋 貼上剪貼簿", command=self.paste_clipboard)
        btn_paste.pack(side=tk.LEFT, padx=(0, 6))

        btn_clear = ttk.Button(toolbar_frame, text="🧹 清空內容", command=self.clear_text)
        btn_clear.pack(side=tk.LEFT, padx=(0, 6))

        btn_load_file = ttk.Button(toolbar_frame, text="📂 開啟 txt 檔", command=self.load_from_file)
        btn_load_file.pack(side=tk.LEFT)

        self.char_count_label = ttk.Label(toolbar_frame, text="字數: 0", font=("Segoe UI", 9), foreground="#666666")
        self.char_count_label.pack(side=tk.RIGHT)

        # 文本輸入框
        text_container = ttk.Frame(text_group)
        text_container.pack(fill=tk.BOTH, expand=True)

        self.text_input = tk.Text(text_container, wrap=tk.WORD, font=("Segoe UI", 11), undo=True, height=8)
        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.text_input.yview)
        self.text_input.configure(yscrollcommand=scrollbar.set)

        self.text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 綁定文字變更事件，動態更新預覽檔名與字數
        self.text_input.bind("<KeyRelease>", self.on_text_change)

        # 3. 語音與語速選項
        options_group = ttk.LabelFrame(main_frame, text=" 語音與參數設定 (Options) ", padding="10")
        options_group.pack(fill=tk.X, pady=(0, 10))

        opt_grid = ttk.Frame(options_group)
        opt_grid.pack(fill=tk.X)

        # 語音角色下拉選單
        ttk.Label(opt_grid, text="發音角色 (Voice):", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        voice_names = [opt[0] for opt in VOICE_OPTIONS]
        self.voice_combo = ttk.Combobox(opt_grid, values=voice_names, state="readonly", width=38)
        self.voice_combo.current(0)
        self.voice_combo.grid(row=0, column=1, sticky=tk.W, pady=4)

        # 語速下拉選單
        ttk.Label(opt_grid, text="語速 (Rate):", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky=tk.W, padx=(20, 8), pady=4)
        rate_names = [opt[0] for opt in RATE_OPTIONS]
        self.rate_combo = ttk.Combobox(opt_grid, values=rate_names, state="readonly", width=18)
        self.rate_combo.current(0)
        self.rate_combo.grid(row=0, column=3, sticky=tk.W, pady=4)

        # 核取選項區 (Checkboxes)
        checks_frame = ttk.Frame(options_group)
        checks_frame.pack(fill=tk.X, pady=(8, 0))

        chk_autoname = ttk.Checkbutton(
            checks_frame, 
            text="自動依輸入文字命名檔名 (過長自動截短)", 
            variable=self.auto_name_var,
            command=self.update_filename_preview
        )
        chk_autoname.pack(side=tk.LEFT, padx=(0, 16))

        chk_openfolder = ttk.Checkbutton(
            checks_frame, 
            text="轉換完成後開啟檔案資料夾", 
            variable=self.open_folder_var
        )
        chk_openfolder.pack(side=tk.LEFT, padx=(0, 16))

        chk_autoplay = ttk.Checkbutton(
            checks_frame, 
            text="轉換完成後立即播放音訊", 
            variable=self.auto_play_var
        )
        chk_autoplay.pack(side=tk.LEFT)

        # 4. 存檔路徑與檔名預覽
        save_group = ttk.LabelFrame(main_frame, text=" 儲存路徑與檔案名稱 (Output Settings) ", padding="10")
        save_group.pack(fill=tk.X, pady=(0, 10))

        save_grid = ttk.Frame(save_group)
        save_grid.pack(fill=tk.X)

        ttk.Label(save_grid, text="預計檔名:").grid(row=0, column=0, sticky=tk.W, padx=(0, 6), pady=3)
        self.entry_filename = ttk.Entry(save_grid, textvariable=self.filename_preview_var, width=35)
        self.entry_filename.grid(row=0, column=1, sticky=tk.W, pady=3)

        ttk.Label(save_grid, text="儲存目錄:").grid(row=1, column=0, sticky=tk.W, padx=(0, 6), pady=3)
        self.lbl_dir = ttk.Label(save_grid, text=self.output_dir, font=("Segoe UI", 9), foreground="#333333")
        self.lbl_dir.grid(row=1, column=1, sticky=tk.W, pady=3)

        btn_browse = ttk.Button(save_grid, text="📂 變更目錄", command=self.choose_output_dir)
        btn_browse.grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=3)

        # 5. 底部執行與進度條區
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(4, 0))

        self.btn_convert = ttk.Button(action_frame, text="🚀 開始轉換為語音檔 (Generate Audio)", command=self.start_conversion)
        self.btn_convert.pack(fill=tk.X, ipady=6)

        # 進度列與狀態說明
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(8, 0))

        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 4))

        self.status_label = ttk.Label(status_frame, text="準備就緒，請輸入文字並點擊轉換。", font=("Segoe UI", 9), foreground="#555555")
        self.status_label.pack(side=tk.LEFT)

    def paste_clipboard(self):
        try:
            content = self.clipboard_get()
            self.text_input.insert(tk.INSERT, content)
            self.on_text_change()
        except Exception:
            pass

    def clear_text(self):
        self.text_input.delete("1.0", tk.END)
        self.on_text_change()

    def load_from_file(self):
        filepath = filedialog.askopenfilename(
            title="選擇文字檔案",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert(tk.END, content)
                self.on_text_change()
            except Exception as e:
                messagebox.showerror("讀取失敗", f"無法讀取檔案: {e}")

    def on_text_change(self, event=None):
        text = self.text_input.get("1.0", tk.END).strip()
        self.char_count_label.config(text=f"字數: {len(text)}")
        self.update_filename_preview()

    def update_filename_preview(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if self.auto_name_var.get() and text:
            filename = sanitize_filename(text, max_length=25)
        else:
            filename = "text.mp3"
        self.filename_preview_var.set(filename)

    def choose_output_dir(self):
        selected_dir = filedialog.askdirectory(initialdir=self.output_dir, title="選擇存檔目錄")
        if selected_dir:
            self.output_dir = selected_dir
            self.lbl_dir.config(text=self.output_dir)

    def get_selected_voice(self, text: str) -> str:
        idx = self.voice_combo.current()
        code = VOICE_OPTIONS[idx][1]
        if code == "auto":
            lang = detect_language(text)
            if lang == "zh-tw":
                return "zh-TW-HsiaoChenNeural"
            else:
                return "en-US-JennyNeural"
        return code

    def get_selected_rate(self) -> str:
        idx = self.rate_combo.current()
        return RATE_OPTIONS[idx][1]

    def start_conversion(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "請先輸入或貼上要轉換的文字！")
            return

        filename = self.filename_preview_var.get().strip()
        if not filename:
            filename = "text.mp3"
        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"

        out_path = os.path.join(self.output_dir, filename)
        voice = self.get_selected_voice(text)
        rate = self.get_selected_rate()

        # 切換 UI 為轉換中狀態
        self.btn_convert.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.status_label.config(text=f"正在轉換語音中 (音色: {voice})...", foreground="#0066cc")

        # 啟動獨立執行緒進行非同步轉換，避免視窗卡死
        threading.Thread(
            target=self.run_tts_thread, 
            args=(text, out_path, voice, rate), 
            daemon=True
        ).start()

    def run_tts_thread(self, text: str, out_path: str, voice: str, rate: str):
        success = False
        err_msg = ""
        try:
            if HAS_EDGE_TTS:
                communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
                asyncio.run(communicate.save(out_path))
                success = True
            elif HAS_GTTS:
                lang_code = "en" if "en-" in voice.lower() else "zh-TW"
                tts = gTTS(text=text, lang=lang_code)
                tts.save(out_path)
                success = True
            else:
                err_msg = "未安裝 edge-tts 或 gTTS 模組"
        except Exception as e:
            err_msg = str(e)
            # 自動嘗試備用引擎
            if HAS_GTTS:
                try:
                    lang_code = "en" if "en-" in voice.lower() else "zh-TW"
                    tts = gTTS(text=text, lang=lang_code)
                    tts.save(out_path)
                    success = True
                except Exception as e2:
                    err_msg = f"{err_msg}\n備用引擎錯誤: {e2}"

        # 回到主執行緒更新 UI
        self.after(0, self.on_conversion_finished, success, out_path, err_msg)

    def show_success_dialog(self, out_path: str, duration_seconds: int = 2):
        """顯示轉換成功的提示對話窗，停留指定秒數後自動關閉"""
        dialog = tk.Toplevel(self)
        dialog.title("轉換成功")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # 置中顯示於主視窗
        dialog_w, dialog_h = 430, 190
        x = max(0, self.winfo_x() + (self.winfo_width() // 2) - (dialog_w // 2))
        y = max(0, self.winfo_y() + (self.winfo_height() // 2) - (dialog_h // 2))
        dialog.geometry(f"{dialog_w}x{dialog_h}+{x}+{y}")

        frame = ttk.Frame(dialog, padding="16")
        frame.pack(fill=tk.BOTH, expand=True)

        # 成功標題
        lbl_icon = ttk.Label(frame, text="✅ 語音轉換成功！", font=("Segoe UI", 12, "bold"), foreground="#008800")
        lbl_icon.pack(anchor=tk.W, pady=(0, 6))

        filename = os.path.basename(out_path)
        file_size_kb = os.path.getsize(out_path) / 1024 if os.path.exists(out_path) else 0

        lbl_msg = ttk.Label(
            frame, 
            text=f"檔案名稱: {filename} ({file_size_kb:.1f} KB)\n儲存路徑: {out_path}", 
            wraplength=390,
            font=("Segoe UI", 9)
        )
        lbl_msg.pack(fill=tk.X, pady=(0, 10))

        # 倒數提示與手動確定按鈕
        bottom_row = ttk.Frame(frame)
        bottom_row.pack(fill=tk.X, side=tk.BOTTOM)

        remaining = [duration_seconds]
        lbl_countdown = ttk.Label(
            bottom_row, 
            text=f"({remaining[0]} 秒後自動關閉...)", 
            foreground="#888888", 
            font=("Segoe UI", 8)
        )
        lbl_countdown.pack(side=tk.LEFT)

        btn_ok = ttk.Button(bottom_row, text="確定", command=dialog.destroy, width=10)
        btn_ok.pack(side=tk.RIGHT)
        btn_ok.focus_set()

        # 倒數計時器
        def update_countdown():
            if not dialog.winfo_exists():
                return
            remaining[0] -= 1
            if remaining[0] <= 0:
                dialog.destroy()
            else:
                lbl_countdown.config(text=f"({remaining[0]} 秒後自動關閉...)")
                dialog.after(1000, update_countdown)

        dialog.after(1000, update_countdown)

    def on_conversion_finished(self, success: bool, out_path: str, err_msg: str):
        self.progress_bar.stop()
        self.btn_convert.config(state=tk.NORMAL)

        if success:
            file_size_kb = os.path.getsize(out_path) / 1024
            self.status_label.config(
                text=f"✅ 轉換成功！已存至: {os.path.basename(out_path)} ({file_size_kb:.1f} KB)", 
                foreground="#008800"
            )

            # 是否自動播放
            if self.auto_play_var.get() and sys.platform == "win32":
                try:
                    os.startfile(out_path)
                except Exception:
                    pass

            # 是否打開資料夾
            if self.open_folder_var.get():
                try:
                    if sys.platform == "win32":
                        subprocess.run(["explorer", "/select,", os.path.normpath(out_path)], shell=True)
                except Exception:
                    pass

            # 成功時彈出提示對話窗，停留 2 秒後自動關閉（亦可手動點確定提前關閉）
            self.show_success_dialog(out_path, duration_seconds=2)
        else:
            # 失敗時常駐對話窗，由使用者手動關閉
            self.status_label.config(text=f"❌ 轉換失敗", foreground="#cc0000")
            messagebox.showerror("錯誤", f"轉換失敗：\n{err_msg}")



if __name__ == "__main__":
    app = TTSApp()
    app.mainloop()
