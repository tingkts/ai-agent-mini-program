#!/bin/bash

# 檢查是否提供參數
if [ "$#" -eq 0 ]; then
    echo "錯誤：請提供至少一個檔案或資料夾路徑。"
    echo "用法: $0 <檔案或資料夾> [更多檔案或資料夾...]"
    exit 1
fi

# 定義處理單一檔案的函式
clean_file() {
    local file="$1"
    
    # 確保是普通檔案且不是捷徑/連結檔
    if [ -f "$file" ] && [ ! -L "$file" ]; then
        # 安全機制：確保是文字檔 (避免改壞 Jetson 的 .bin, .dtb, .encrypt 等二進位檔)
        if file "$file" | grep -qE 'text|empty'; then
            # 檢查是否真的含有行尾空白 (節省不必要的寫入動作)
            if grep -q '[[:blank:]]$' "$file"; then
                echo "🧹 清理中: $file"
                sed -i 's/[ \t]*$//' "$file"
            fi
        fi
    fi
}

echo "開始掃描與清理..."

# 走訪所有你在終端機輸入的參數
for target in "$@"; do
    if [ -d "$target" ]; then
        echo "📂 掃描資料夾: $target"
        # 排除隱藏目錄 (如 .git)，尋找所有一般檔案並逐一處理
        find "$target" -type f -not -path '*/\.*' | while read -r filepath; do
            clean_file "$filepath"
        done
    elif [ -e "$target" ]; then
        clean_file "$target"
    else
        echo "⚠️ 警告: 找不到檔案或資料夾 '$target'"
    fi
done

echo "✅ 清理完成！"