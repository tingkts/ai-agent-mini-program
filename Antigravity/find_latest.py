import os
import sys
import heapq
import argparse
from datetime import datetime

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:6.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:6.2f} TB"

def get_latest_files(target_dir: str, n: int):
    # 使用最小堆積儲存前 N 個最新檔案 (latest_time, time_type, size, full_path)
    heap = []

    for root, _, files in os.walk(target_dir):
        for f in files:
            full_path = os.path.join(root, f)
            try:
                stat = os.stat(full_path)
                mtime = stat.st_mtime
                ctime = stat.st_ctime  # Windows 上為檔案建立時間

                # 同時考慮修改時間與建立時間，取較新者
                if ctime > mtime:
                    latest_time = ctime
                    time_type = "建立"
                else:
                    latest_time = mtime
                    time_type = "修改"

                size = stat.st_size

                if len(heap) < n:
                    heapq.heappush(heap, (latest_time, time_type, size, full_path))
                elif latest_time > heap[0][0]:
                    heapq.heapreplace(heap, (latest_time, time_type, size, full_path))
            except (OSError, PermissionError):
                # 略過無權限存取或鎖定中的檔案
                continue

    # 依照最新時間由新到舊排序
    return sorted(heap, key=lambda x: x[0], reverse=True)

def main():
    parser = argparse.ArgumentParser(description="遞迴尋找指定資料夾中最新（修改/建立）的前 N 個檔案")
    parser.add_argument("path", help="目標資料夾路徑，例如：D:\\Dropbox\\婷")
    parser.add_argument("-n", "--num", type=int, default=10, help="要顯示的檔案數量 (預設: 10)")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"錯誤: 找不到路徑 '{args.path}'")
        sys.exit(1)

    print(f"搜尋路徑: {args.path}")
    print(f"取得最新異動（修改/建立）的前 {args.num} 個檔案...\n")

    results = get_latest_files(args.path, args.num)

    if not results:
        print("未找到任何檔案。")
        return

    print(f"{'最新時間':<20} {'動作':<6} {'大小':<12} {'檔案路徑'}")
    print("-" * 85)
    for latest_time, time_type, size, path in results:
        dt_str = datetime.fromtimestamp(latest_time).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{dt_str:<20} {time_type:<6} {format_size(size):<12} {path}")

if __name__ == "__main__":
    main()