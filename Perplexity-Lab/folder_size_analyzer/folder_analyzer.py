import os
import time
from datetime import datetime, timedelta

def get_folder_size(folder_path):
    """計算資料夾總大小"""
    total_size = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    # 忽略無法存取的檔案
                    continue
    except (OSError, IOError):
        # 忽略無法存取的資料夾
        pass
    return total_size

def get_folder_growth(folder_path, days=30):
    """計算資料夾在指定天數內的增長量"""
    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)  # 一個月前的時間戳
    
    growth_size = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    # 檢查檔案修改時間
                    if os.path.getmtime(file_path) >= cutoff_time:
                        growth_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    # 忽略無法存取的檔案
                    continue
    except (OSError, IOError):
        # 忽略無法存取的資料夾
        pass
    return growth_size

def analyze_folder_growth(base_path):
    """分析資料夾增長情況"""
    folder_data = []
    
    print(f"正在分析目錄: {base_path}")
    print("這可能需要一些時間，請稍候...")
    
    try:
        # 遞迴遍歷所有子資料夾
        for root, dirs, files in os.walk(base_path):
            for dir_name in dirs:
                folder_path = os.path.join(root, dir_name)
                
                # 計算資料夾總大小
                total_size = get_folder_size(folder_path)
                
                # 計算一個月內的增長量
                growth_size = get_folder_growth(folder_path, 30)
                
                # 只記錄有增長的資料夾
                if growth_size > 0:
                    folder_data.append({
                        'path': folder_path,
                        'total_size': total_size,
                        'growth_size': growth_size
                    })
                
                # 顯示進度
                if len(folder_data) % 10 == 0:
                    print(f"已處理 {len(folder_data)} 個有增長的資料夾...")
    
    except KeyboardInterrupt:
        print("\n分析被中斷")
        return folder_data
    except Exception as e:
        print(f"發生錯誤: {e}")
        return folder_data
    
    return folder_data

def format_size(size_bytes):
    """將位元組轉換為人類可讀的格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def main():
    base_path = r"C:\Users\tingsung"
    
    # 檢查路徑是否存在
    if not os.path.exists(base_path):
        print(f"錯誤: 路徑 '{base_path}' 不存在")
        return
    
    # 分析資料夾增長
    folder_data = analyze_folder_growth(base_path)
    
    if not folder_data:
        print("未找到任何在過去一個月內有增長的資料夾")
        return
    
    # 按增長量排序（從大到小）
    folder_data.sort(key=lambda x: x['growth_size'], reverse=True)
    
    # 輸出前 20 個資料夾
    print("\n" + "="*100)
    print("過去一個月內容量增加最多的前 20 個資料夾:")
    print("="*100)
    print(f"{'資料夾名稱(完整路徑)':<60} {'資料夾大小':<15} {'增加的大小':<15}")
    print("-"*100)
    
    for i, folder in enumerate(folder_data[:20], 1):
        path = folder['path']
        total_size = format_size(folder['total_size'])
        growth_size = format_size(folder['growth_size'])
        
        # 如果路徑太長，截短顯示
        if len(path) > 57:
            display_path = "..." + path[-54:]
        else:
            display_path = path
        
        print(f"{display_path:<60} {total_size:<15} {growth_size:<15}")
    
    print("-"*100)
    print(f"總共找到 {len(folder_data)} 個有增長的資料夾")

if __name__ == "__main__":
    main()
