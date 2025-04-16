#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MP4影片完整性檢測工具 (Python版本)
Video Integrity Checker for MP4 files

使用方法: python check_videos.py [資料夾路徑]
Usage: python check_videos.py [folder_path]

如果不指定路徑，將檢測當前資料夾
If no path specified, checks current folder
"""

import os
import sys
import subprocess
import glob
import datetime
from pathlib import Path

class VideoIntegrityChecker:
    def __init__(self, folder_path="."):
        self.folder_path = Path(folder_path)
        self.ffmpeg_path = "ffmpeg"  # 假設ffmpeg在PATH中
        self.results = []

    def check_ffmpeg_available(self):
        """檢查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_mp4_files(self):
        """獲取資料夾中的所有MP4檔案"""
        pattern = self.folder_path / "*.mp4"
        return list(glob.glob(str(pattern)))

    def check_single_video(self, video_path):
        """檢測單個影片檔案"""
        try:
            # 使用ffmpeg檢測影片完整性
            cmd = [
                self.ffmpeg_path,
                "-v", "error",
                "-i", str(video_path),
                "-f", "null",
                "-"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )

            file_info = {
                "filename": os.path.basename(video_path),
                "filepath": video_path,
                "size": os.path.getsize(video_path),
                "has_errors": len(result.stderr) > 0,
                "error_details": result.stderr,
                "status": "錯誤" if len(result.stderr) > 0 else "正常"
            }

            return file_info

        except subprocess.TimeoutExpired:
            return {
                "filename": os.path.basename(video_path),
                "filepath": video_path,
                "size": os.path.getsize(video_path),
                "has_errors": True,
                "error_details": "檢測超時",
                "status": "超時"
            }
        except Exception as e:
            return {
                "filename": os.path.basename(video_path),
                "filepath": video_path,
                "size": 0,
                "has_errors": True,
                "error_details": str(e),
                "status": "檢測失敗"
            }

    def run_check(self):
        """執行完整性檢測"""
        print("MP4影片完整性檢測工具 (Python版本)")
        print("=" * 50)

        # 檢查ffmpeg
        if not self.check_ffmpeg_available():
            print("錯誤：找不到ffmpeg或ffmpeg無法執行")
            print("請確認ffmpeg已正確安裝並在PATH環境變數中")
            return False

        # 獲取MP4檔案
        mp4_files = self.get_mp4_files()
        if not mp4_files:
            print(f"在資料夾 {self.folder_path} 中找不到MP4檔案")
            return False

        print(f"找到 {len(mp4_files)} 個MP4檔案，開始檢測...")
        print()

        # 檢測每個檔案
        for i, video_file in enumerate(mp4_files, 1):
            print(f"[{i}/{len(mp4_files)}] 檢測: {os.path.basename(video_file)}")

            result = self.check_single_video(video_file)
            self.results.append(result)

            if result["has_errors"]:
                print(f"    ✗ {result['status']}")
            else:
                print(f"    ✓ 檢測通過")

        return True

    def generate_report(self):
        """生成檢測報告"""
        if not self.results:
            return

        # 統計結果
        total_files = len(self.results)
        error_files = sum(1 for r in self.results if r["has_errors"])
        success_files = total_files - error_files

        print()
        print("=" * 50)
        print("檢測完成！統計結果：")
        print("=" * 50)
        print(f"總檔案數：{total_files}")
        print(f"檢測通過：{success_files}")
        print(f"發現錯誤：{error_files}")
        print(f"成功率：{success_files/total_files*100:.1f}%")

        # 保存詳細報告
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"video_check_report_{timestamp}.txt"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"MP4影片完整性檢測報告\n")
            f.write(f"檢測時間：{datetime.datetime.now()}\n")
            f.write(f"檢測資料夾：{self.folder_path}\n")
            f.write("=" * 50 + "\n")
            f.write(f"總檔案數：{total_files}\n")
            f.write(f"檢測通過：{success_files}\n")
            f.write(f"發現錯誤：{error_files}\n")
            f.write("=" * 50 + "\n\n")

            f.write("詳細結果：\n")
            for result in self.results:
                f.write(f"檔案：{result['filename']}\n")
                f.write(f"大小：{result['size']:,} bytes\n")
                f.write(f"狀態：{result['status']}\n")
                if result["has_errors"] and result["error_details"]:
                    f.write(f"錯誤詳情：{result['error_details']}\n")
                f.write("-" * 30 + "\n")

        print(f"\n詳細報告已保存到：{report_file}")

        # 如果有錯誤檔案，單獨列出
        if error_files > 0:
            error_list_file = f"corrupted_videos_{timestamp}.txt"
            with open(error_list_file, "w", encoding="utf-8") as f:
                f.write("有問題的影片檔案列表\n")
                f.write("=" * 30 + "\n")
                for result in self.results:
                    if result["has_errors"]:
                        f.write(f"{result['filename']}\n")

            print(f"有問題的檔案列表：{error_list_file}")

def main():
    # 檢查命令列參數
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = "."

    # 執行檢測
    checker = VideoIntegrityChecker(folder_path)

    if checker.run_check():
        checker.generate_report()

    input("\n按Enter鍵結束...")

if __name__ == "__main__":
    main()
