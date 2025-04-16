import os
import concurrent.futures
from datetime import datetime, timedelta

# 取得單一資料夾總大小
def get_folder_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += get_folder_size(entry.path)
                except Exception:
                    continue
    except Exception:
        pass
    return total

# 取得單一資料夾過去N天的檔案增長量
def get_growth_size(path, days=30):
    total = 0
    cutoff = datetime.now() - timedelta(days=days)
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        mtime = datetime.fromtimestamp(entry.stat(follow_symlinks=False).st_mtime)
                        if mtime >= cutoff:
                            total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += get_growth_size(entry.path, days)
                except Exception:
                    continue
    except Exception:
        pass
    return total

# 主要分析程序
def analyze_folder_growth(base_path, days=30, top_n=20):
    folder_list = []
    # 先收集所有子資料夾清單
    for root, dirs, _ in os.walk(base_path):
        for d in dirs:
            folder_list.append(os.path.join(root, d))

    results = []
    def worker(folder_path):
        total_size = get_folder_size(folder_path)
        growth_size = get_growth_size(folder_path, days)
        return (folder_path, total_size, growth_size)

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futs = [executor.submit(worker, d) for d in folder_list]
        for fut in concurrent.futures.as_completed(futs):
            folder_path, total_size, growth_size = fut.result()
            if growth_size > 0:
                results.append({
                    'path': folder_path,
                    'total_size': total_size,
                    'growth_size': growth_size
                })
    # 依增長量大→小排序
    results.sort(key=lambda x: x['growth_size'], reverse=True)
    return results[:top_n]

# 格式化檔案大小
def format_size(s):
    for unit in ['B','KB','MB','GB','TB']:
        if s < 1024.0:
            return f"{s:.2f} {unit}"
        s /= 1024.0
    return f"{s:.2f} PB"

def main():
    base = r"C:\Users\tingsung"
    if not os.path.exists(base):
        print("Path doesn't exist.")
        return

    print(f"掃描 {base}，請稍候...")
    items = analyze_folder_growth(base)
    if not items:
        print("過去一個月內無資料夾成長。")
        return

    print(f"\n{'資料夾(完整路徑)':<60} {'總大小':<15} {'一個月增加':<15}")
    print('-'*95)
    for folder in items:
        path_disp = folder['path']
        # 顯示路徑太長時精簡
        if len(path_disp) > 55:
            path_disp = "..." + path_disp[-52:]
        print(f"{path_disp:<60} {format_size(folder['total_size']):<15} {format_size(folder['growth_size']):<15}")

if __name__ == "__main__":
    main()
