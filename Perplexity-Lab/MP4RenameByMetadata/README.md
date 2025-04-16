<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# 請問.mp4檔案有metadata關於檔案標題的嗎？

為我現在有一推.mp4檔案，名都是隨機的英數想要問能用 shell script 或或是寫程式來讀.mp4檔，然後重新命名.mp4檔，這樣就看檔名知道影片是什麼了？

Answer skipped.

---

# 請問.mp4檔案有metadata關於檔案標題的嗎？

為我現在有一推.mp4檔案，名都是隨機的英數想要問能用 shell script 或或是寫程式來讀.mp4檔，然後重新命名.mp4檔，這樣就看檔名知道影片是什麼了？

是的，.mp4檔案確實包含metadata，其中可能包含標題資訊。以下是幾種方法來讀取metadata並重新命名檔案：

## MP4 Metadata 說明

MP4檔案通常包含以下metadata欄位：

- **Title** (標題)
- **Artist** (藝術家/作者)
- **Album** (專輯)
- **Year** (年份)
- **Genre** (類型)
- **Comment** (註解)


## 使用 Shell Script 解決方案

### 方法1：使用 ffprobe (推薦)

```bash
#!/bin/bash

# 批量重新命名MP4檔案
for file in *.mp4; do
    if [ -f "$file" ]; then
        # 提取標題metadata
        title=$(ffprobe -v quiet -show_entries format_tags=title -of csv=p=0 "$file" 2>/dev/null)

        # 如果有標題，則重新命名
        if [ ! -z "$title" ] && [ "$title" != "" ]; then
            # 清理標題中的特殊字符
            clean_title=$(echo "$title" | sed 's/[^a-zA-Z0-9\u4e00-\u9fff ]/_/g' | sed 's/__*/_/g' | sed 's/^_\|_$//g')
            new_name="${clean_title}.mp4"

            # 避免檔名衝突
            counter=1
            while [ -f "$new_name" ]; do
                new_name="${clean_title}_${counter}.mp4"
                ((counter++))
            done

            mv "$file" "$new_name"
            echo "重新命名: $file -> $new_name"
        else
            echo "無標題metadata: $file"
        fi
    fi
done
```


### 方法2：使用 exiftool

```bash
#!/bin/bash

for file in *.mp4; do
    if [ -f "$file" ]; then
        title=$(exiftool -Title -s -s -s "$file" 2>/dev/null)

        if [ ! -z "$title" ]; then
            clean_title=$(echo "$title" | tr -cd '[:alnum:][:space:]' | tr ' ' '_')
            new_name="${clean_title}.mp4"

            if [ ! -f "$new_name" ]; then
                mv "$file" "$new_name"
                echo "重新命名: $file -> $new_name"
            fi
        fi
    fi
done
```


## Python 解決方案

```python
#!/usr/bin/env python3
import os
import re
from mutagen.mp4 import MP4

def clean_filename(title):
    # 移除或替換不適合檔名的字符
    title = re.sub(r'[<>:"/\\|?*]', '_', title)
    title = re.sub(r'_+', '_', title)  # 合併多個底線
    return title.strip('_')

def rename_mp4_files():
    for filename in os.listdir('.'):
        if filename.lower().endswith('.mp4'):
            try:
                # 讀取MP4 metadata
                mp4_file = MP4(filename)

                # 嘗試不同的標題欄位
                title = None
                if '\xa9nam' in mp4_file:  # 標準標題欄位
                    title = mp4_file['\xa9nam'][0]
                elif 'title' in mp4_file:
                    title = mp4_file['title'][0]

                if title:
                    clean_title = clean_filename(title)
                    new_filename = f"{clean_title}.mp4"

                    # 避免檔名衝突
                    counter = 1
                    while os.path.exists(new_filename):
                        new_filename = f"{clean_title}_{counter}.mp4"
                        counter += 1

                    os.rename(filename, new_filename)
                    print(f"重新命名: {filename} -> {new_filename}")
                else:
                    print(f"無標題metadata: {filename}")

            except Exception as e:
                print(f"處理 {filename} 時發生錯誤: {e}")

if __name__ == "__main__":
    rename_mp4_files()
```


## 安裝必要工具

### Linux/macOS:

```bash
# 安裝 ffmpeg (包含 ffprobe)
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS

# 安裝 exiftool
sudo apt install libimage-exiftool-perl  # Ubuntu/Debian
brew install exiftool                     # macOS

# Python 套件
pip install mutagen
```


## 使用建議

1. **先備份檔案**：在執行批量重新命名前，請先備份重要檔案
2. **測試模式**：可以先修改script只顯示會如何重新命名，而不實際執行
3. **檢查metadata**：不是所有MP4檔案都有標題metadata，可能需要手動處理部分檔案

這些方法可以有效地根據MP4檔案的metadata來重新命名檔案，讓您更容易識別影片內容。

---

# 承上，請問你可以幫忙改一下 python 檔，先印出每個檔案的可能關於檔名或檔案描述的欄位嗎？

當然可以！以下是一個Python程式，可以印出每個MP4檔案中所有可能與檔名/描述相關的metadata欄位：

## Python 程式：檢視 MP4 Metadata

```python
#!/usr/bin/env python3
import os
from mutagen.mp4 import MP4
from mutagen import File

def print_mp4_metadata():
    """印出所有MP4檔案的metadata欄位"""

    mp4_files = [f for f in os.listdir('.') if f.lower().endswith('.mp4')]

    if not mp4_files:
        print("目前目錄中沒有找到MP4檔案")
        return

    for filename in mp4_files:
        print(f"\n{'='*60}")
        print(f"檔案: {filename}")
        print(f"{'='*60}")

        try:
            # 使用 mutagen 讀取檔案
            mp4_file = MP4(filename)

            if not mp4_file.tags:
                print("此檔案沒有metadata標籤")
                continue

            # 常見的與檔名相關的欄位
            title_related_fields = {
                '\xa9nam': '標題 (Title)',
                '\xa9alb': '專輯 (Album)',
                '\xa9ART': '藝術家 (Artist)',
                '\xa9wrt': '作者 (Writer)',
                '\xa9cmt': '註解 (Comment)',
                'desc': '描述 (Description)',
                'ldes': '長描述 (Long Description)',
                '\xa9des': '描述 (Description)',
                '\xa9gen': '類型 (Genre)',
                '\xa9day': '日期 (Date)',
                'tvsh': '電視節目 (TV Show)',
                'tven': '集數 (Episode)',
                'tvsn': '季數 (Season)',
                'stik': '媒體類型 (Media Kind)',
                'catg': '分類 (Category)',
                'keyw': '關鍵字 (Keywords)',
                'cprt': '版權 (Copyright)',
                'soal': '排序專輯 (Sort Album)',
                'soar': '排序藝術家 (Sort Artist)',
                'sonm': '排序標題 (Sort Title)',
                'purd': '購買日期 (Purchase Date)',
                'hdvd': 'HD影片 (HD Video)',
                'pgap': '專輯間隙 (Gapless Album)',
            }

            print("與檔名相關的欄位:")
            print("-" * 40)

            found_any = False
            for tag, description in title_related_fields.items():
                if tag in mp4_file:
                    value = mp4_file[tag]
                    if isinstance(value, list) and value:
                        value = value[0]
                    print(f"{description}: {value}")
                    found_any = True

            if not found_any:
                print("沒有找到與檔名相關的欄位")

            # 印出所有可用的欄位
            print(f"\n所有可用的metadata欄位:")
            print("-" * 40)
            for tag in sorted(mp4_file.keys()):
                value = mp4_file[tag]
                if isinstance(value, list) and value:
                    value = value[0]
                # 限制顯示長度
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"{tag}: {value}")

        except Exception as e:
            print(f"讀取檔案時發生錯誤: {e}")

def print_detailed_metadata(filename):
    """印出單一檔案的詳細metadata"""
    print(f"\n詳細分析檔案: {filename}")
    print("=" * 50)

    try:
        # 使用不同的方法讀取
        file = File(filename)

        if file is None:
            print("無法讀取檔案")
            return

        print("檔案資訊:")
        print(f"- 檔案格式: {file.mime[0] if file.mime else 'Unknown'}")
        print(f"- 長度: {file.info.length if hasattr(file.info, 'length') else 'Unknown'} 秒")

        if hasattr(file, 'tags') and file.tags:
            print("\n所有標籤:")
            for key, value in file.tags.items():
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                print(f"- {key}: {value}")
        else:
            print("沒有找到標籤資訊")

    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    print("MP4檔案Metadata分析工具")
    print("=" * 60)

    # 印出所有檔案的基本資訊
    print_mp4_metadata()

    # 如果需要詳細分析特定檔案，可以取消註解下面的程式碼
    # specific_file = input("\n輸入要詳細分析的檔案名稱 (或按Enter跳過): ").strip()
    # if specific_file and os.path.exists(specific_file):
    #     print_detailed_metadata(specific_file)
```


## 安裝必要套件

```bash
pip install mutagen
```


## 使用方式

1. 將程式儲存為 `check_metadata.py`
2. 在包含MP4檔案的目錄中執行：
```bash
python check_metadata.py
```


## 程式功能

這個程式會：

1. **掃描目前目錄**中的所有MP4檔案
2. **印出與檔名相關的欄位**，如標題、藝術家、專輯等
3. **顯示所有可用的metadata欄位**
4. **處理錯誤情況**，如無法讀取的檔案

## 常見的有用欄位

- `\xa9nam`: 標題 (最常用於重新命名)
- `\xa9ART`: 藝術家
- `\xa9alb`: 專輯
- `\xa9cmt`: 註解
- `desc`: 描述
- `tvsh`: 電視節目名稱
- `tven`: 集數

執行這個程式後，您就能看到每個檔案有哪些可用的metadata，然後決定要用哪個欄位來重新命名檔案。

---

# 承上，請問你能改寫shell script一樣先印出每個檔案所有能get到的metadata？

當然可以！以下是幾個Shell Script版本，可以印出每個MP4檔案的所有metadata：

## 方法1：使用 ffprobe (推薦)

```bash
#!/bin/bash

echo "MP4檔案Metadata分析工具 (使用 ffprobe)"
echo "============================================"

# 檢查是否有MP4檔案
mp4_files=(*.mp4)
if [ ! -e "${mp4_files[0]}" ]; then
    echo "目前目錄中沒有找到MP4檔案"
    exit 1
fi

for file in *.mp4; do
    if [ -f "$file" ]; then
        echo ""
        echo "============================================"
        echo "檔案: $file"
        echo "============================================"

        # 取得所有格式metadata
        echo "格式資訊 (Format metadata):"
        echo "--------------------------------------------"
        ffprobe -v quiet -show_entries format_tags -of csv=p=0 "$file" 2>/dev/null | while IFS='=' read -r key value; do
            if [ ! -z "$key" ] && [ ! -z "$value" ]; then
                echo "$key: $value"
            fi
        done

        # 取得串流metadata
        echo ""
        echo "串流資訊 (Stream metadata):"
        echo "--------------------------------------------"
        ffprobe -v quiet -show_entries stream_tags -of csv=p=0 "$file" 2>/dev/null | while IFS='=' read -r key value; do
            if [ ! -z "$key" ] && [ ! -z "$value" ]; then
                echo "$key: $value"
            fi
        done

        # 取得所有metadata (詳細版本)
        echo ""
        echo "所有Metadata (詳細版本):"
        echo "--------------------------------------------"
        ffprobe -v quiet -show_format -show_streams "$file" 2>/dev/null | grep -E "^(TAG:|title=|artist=|album=|date=|genre=|comment=|description=|show=|episode=|season=)"

        echo ""
    fi
done
```


## 方法2：使用 exiftool

```bash
#!/bin/bash

echo "MP4檔案Metadata分析工具 (使用 exiftool)"
echo "============================================"

# 檢查exiftool是否安裝
if ! command -v exiftool &> /dev/null; then
    echo "錯誤: 請先安裝 exiftool"
    echo "Ubuntu/Debian: sudo apt install libimage-exiftool-perl"
    echo "macOS: brew install exiftool"
    exit 1
fi

for file in *.mp4; do
    if [ -f "$file" ]; then
        echo ""
        echo "============================================"
        echo "檔案: $file"
        echo "============================================"

        # 顯示所有metadata
        echo "所有Metadata:"
        echo "--------------------------------------------"
        exiftool "$file" 2>/dev/null

        echo ""
        echo "與檔名相關的重要欄位:"
        echo "--------------------------------------------"

        # 提取重要欄位
        title=$(exiftool -Title -s -s -s "$file" 2>/dev/null)
        artist=$(exiftool -Artist -s -s -s "$file" 2>/dev/null)
        album=$(exiftool -Album -s -s -s "$file" 2>/dev/null)
        description=$(exiftool -Description -s -s -s "$file" 2>/dev/null)
        comment=$(exiftool -Comment -s -s -s "$file" 2>/dev/null)
        genre=$(exiftool -Genre -s -s -s "$file" 2>/dev/null)
        year=$(exiftool -Year -s -s -s "$file" 2>/dev/null)

        [ ! -z "$title" ] && echo "標題 (Title): $title"
        [ ! -z "$artist" ] && echo "藝術家 (Artist): $artist"
        [ ! -z "$album" ] && echo "專輯 (Album): $album"
        [ ! -z "$description" ] && echo "描述 (Description): $description"
        [ ! -z "$comment" ] && echo "註解 (Comment): $comment"
        [ ! -z "$genre" ] && echo "類型 (Genre): $genre"
        [ ! -z "$year" ] && echo "年份 (Year): $year"

        if [ -z "$title" ] && [ -z "$artist" ] && [ -z "$album" ] && [ -z "$description" ] && [ -z "$comment" ]; then
            echo "沒有找到與檔名相關的metadata"
        fi

        echo ""
    fi
done
```


## 方法3：結合多種工具的完整版本

```bash
#!/bin/bash

echo "MP4檔案完整Metadata分析工具"
echo "============================================"

# 檢查工具是否可用
check_tools() {
    local tools_available=0

    if command -v ffprobe &> /dev/null; then
        echo "✓ ffprobe 可用"
        tools_available=1
    else
        echo "✗ ffprobe 不可用"
    fi

    if command -v exiftool &> /dev/null; then
        echo "✓ exiftool 可用"
        tools_available=1
    else
        echo "✗ exiftool 不可用"
    fi

    if command -v mediainfo &> /dev/null; then
        echo "✓ mediainfo 可用"
        tools_available=1
    else
        echo "✗ mediainfo 不可用"
    fi

    if [ $tools_available -eq 0 ]; then
        echo ""
        echo "錯誤: 沒有找到任何可用的metadata工具"
        echo "請安裝以下工具之一:"
        echo "- ffmpeg (包含 ffprobe): sudo apt install ffmpeg"
        echo "- exiftool: sudo apt install libimage-exiftool-perl"
        echo "- mediainfo: sudo apt install mediainfo"
        exit 1
    fi
    echo ""
}

analyze_with_ffprobe() {
    local file="$1"
    echo "使用 ffprobe 分析:"
    echo "--------------------------------------------"

    # 格式metadata
    echo "格式標籤:"
    ffprobe -v quiet -print_format json -show_format "$file" 2>/dev/null | grep -A 20 '"tags"' | sed 's/^[ ]*//'

    echo ""
}

analyze_with_exiftool() {
    local file="$1"
    echo "使用 exiftool 分析:"
    echo "--------------------------------------------"
    exiftool -j "$file" 2>/dev/null | jq -r '.[] | to_entries[] | "\(.key): \(.value)"' 2>/dev/null || exiftool "$file" 2>/dev/null
    echo ""
}

analyze_with_mediainfo() {
    local file="$1"
    echo "使用 mediainfo 分析:"
    echo "--------------------------------------------"
    mediainfo "$file" 2>/dev/null
    echo ""
}

# 主程式
check_tools

for file in *.mp4; do
    if [ -f "$file" ]; then
        echo ""
        echo "============================================"
        echo "檔案: $file"
        echo "檔案大小: $(du -h "$file" | cut -f1)"
        echo "============================================"

        # 使用可用的工具分析
        if command -v ffprobe &> /dev/null; then
            analyze_with_ffprobe "$file"
        fi

        if command -v exiftool &> /dev/null; then
            analyze_with_exiftool "$file"
        fi

        if command -v mediainfo &> /dev/null; then
            analyze_with_mediainfo "$file"
        fi

        echo "============================================"
    fi
done

echo ""
echo "分析完成！"
```


## 使用方式

1. 選擇其中一個版本，儲存為 `check_metadata.sh`
2. 給予執行權限：
```bash
chmod +x check_metadata.sh
```

3. 在包含MP4檔案的目錄中執行：
```bash
./check_metadata.sh
```


## 安裝必要工具

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg libimage-exiftool-perl mediainfo

# macOS
brew install ffmpeg exiftool mediainfo

# CentOS/RHEL
sudo yum install ffmpeg exiftool mediainfo
```

這些腳本會詳細顯示每個MP4檔案的所有可用metadata，讓您可以決定要使用哪些欄位來重新命名檔案。建議先使用方法1（ffprobe版本），因為它通常預裝在大多數系統中。

---

# ting@tingsung-1:/mnt/a/..tmp/尚未整理/video\$ ./check_metadata-ffprobe.sh

-bash: ./check_metadata-ffprobe.sh: /bin/bash^M: bad interpreter: No such file or directory

遇到這個錯誤？

這個錯誤是因為Shell Script檔案包含Windows格式的換行符號（CRLF）造成的。`^M` 表示回車符號（Carriage Return）。

## 解決方法

### 方法1：使用 dos2unix 轉換（推薦）

```bash
# 安裝 dos2unix
sudo apt install dos2unix  # Ubuntu/Debian
# 或
sudo yum install dos2unix  # CentOS/RHEL

# 轉換檔案格式
dos2unix check_metadata-ffprobe.sh

# 然後執行
./check_metadata-ffprobe.sh
```


### 方法2：使用 sed 移除回車符號

```bash
sed -i 's/\r$//' check_metadata-ffprobe.sh
```


### 方法3：使用 tr 命令

```bash
tr -d '\r' < check_metadata-ffprobe.sh > temp_script.sh
mv temp_script.sh check_metadata-ffprobe.sh
chmod +x check_metadata-ffprobe.sh
```


### 方法4：重新建立檔案

如果上述方法都不行，可以重新建立檔案：

```bash
# 刪除原檔案
rm check_metadata-ffprobe.sh

# 使用 nano 或 vim 重新建立
nano check_metadata-ffprobe.sh
```

然後貼上腳本內容，確保使用Linux換行格式。

### 方法5：直接用 bash 執行

```bash
bash check_metadata-ffprobe.sh
```


## 預防措施

為了避免這個問題，建議：

1. **在Linux系統上直接建立腳本**，而不是從Windows複製
2. **使用Linux文字編輯器**（如nano、vim、gedit）
3. **設定編輯器使用Unix換行格式**

## 檢查檔案格式

可以用以下命令檢查檔案格式：

```bash
file check_metadata-ffprobe.sh
```

正確的輸出應該是：

```
check_metadata-ffprobe.sh: Bourne-Again shell script, ASCII text executable
```

如果看到 `CRLF line terminators`，就表示需要轉換格式。

最簡單的解決方法就是使用 `dos2unix` 命令轉換檔案格式。

---

# ting@tingsung-1:/mnt/a/..tmp/尚未整理/video\$ dos2unix check_metadata-ffprobe.sh

dos2unix: Failed to change the permissions of temporary output file ./d2utmpf1o5jZ: Operation not permitted
dos2unix: problems converting file check_metadata-ffprobe.sh

問這又是什麼錯誤？

這個錯誤是因為 `dos2unix` 嘗試保留原檔案的權限設定時失敗了。從您的路徑 `/mnt/a/` 可以看出您可能在使用掛載的檔案系統或 WSL 環境，這些環境對權限操作有限制[^6_1][^6_2]。

## 解決方法

### 方法1：使用新檔案模式（推薦）

```bash
dos2unix -n check_metadata-ffprobe.sh temp_file.sh
mv temp_file.sh check_metadata-ffprobe.sh
chmod +x check_metadata-ffprobe.sh
```


### 方法2：使用 sed 替代 dos2unix

```bash
sed -i 's/\r$//' check_metadata-ffprobe.sh
```


### 方法3：使用 tr 命令

```bash
tr -d '\r' < check_metadata-ffprobe.sh > temp_script.sh
mv temp_script.sh check_metadata-ffprobe.sh
chmod +x check_metadata-ffprobe.sh
```


### 方法4：如果您在 WSL 環境中

如果您使用的是 WSL（Windows Subsystem for Linux），需要配置 WSL 允許權限操作[^6_1]：

```bash
# 編輯 WSL 配置檔
sudo nano /etc/wsl.conf

# 加入以下內容
[automount]
options = "metadata"

# 儲存檔案後重新啟動 WSL 或重開機
```


### 方法5：直接重新建立檔案

```bash
# 檢視原檔案內容
cat check_metadata-ffprobe.sh

# 刪除原檔案
rm check_metadata-ffprobe.sh

# 重新建立檔案
nano check_metadata-ffprobe.sh
```

然後貼上腳本內容，確保使用 Unix 換行格式。

## 快速解決方案

最簡單的方法是使用 `sed`：

```bash
sed -i 's/\r$//' check_metadata-ffprobe.sh
chmod +x check_metadata-ffprobe.sh
./check_metadata-ffprobe.sh
```

這個錯誤主要是因為新版本的 `dos2unix` 為了安全考量會嘗試保留原檔案的擁有者和權限，但在某些檔案系統（如掛載的 Windows 磁碟或 WSL）上無法執行這些權限操作[^6_2][^6_3]。使用上述任一方法都能解決這個問題。

<div style="text-align: center">⁂</div>

[^6_1]: https://community.intel.com/t5/Nios-V-II-Embedded-Design-Suite/dos2unix-fails-to-change-permissions-when-creating-project-from/m-p/1193060

[^6_2]: https://access.redhat.com/solutions/3168671

[^6_3]: https://bugzilla.redhat.com/show_bug.cgi?id=1483633

[^6_4]: https://www.tenforums.com/software-apps/71469-dos2unix-problem-operation-not-permitted-when-using-dos2unix-file.html

[^6_5]: https://community.intel.com/t5/Nios-V-II-Embedded-Design-Suite/dos2unix-fails-to-change-permissions-when-creating-project-from/m-p/1244940?profile.language=pt

[^6_6]: https://forums.raspberrypi.com/viewtopic.php?t=151340

[^6_7]: https://docs.oracle.com/cd/E86824_01/html/E54763/dos2unix-1.html

[^6_8]: https://stackoverflow.com/questions/72356907/failed-to-open-temporary-output-file-permission-denied

[^6_9]: https://stackoverflow.com/questions/68344035/dos2unix-doesnt-convert-the-env-file-even-with-f-option

[^6_10]: https://askubuntu.com/questions/675296/changing-ownership-operation-not-permitted-even-as-root

[^6_11]: https://community.intel.com/t5/Nios-V-II-Embedded-Design-Suite/dos2unix-fails-to-change-permissions-when-creating-project-from/td-p/1193060?profile.language=ko

