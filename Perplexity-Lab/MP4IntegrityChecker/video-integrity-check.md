# 檢測MP4影片完整性批次檔

## check_videos.bat

```batch
@echo off
setlocal enabledelayedexpansion

:: 設定編碼頁為UTF-8以支援中文字符
chcp 65001 >nul

echo ===============================================
echo          MP4影片完整性檢測工具
echo ===============================================
echo.

:: 檢查是否已安裝ffmpeg
ffmpeg -version >nul 2>&1
if !errorlevel! neq 0 (
    echo 錯誤：找不到ffmpeg！
    echo 請先安裝ffmpeg並將其添加到系統PATH環境變數中。
    echo 下載地址：https://www.gyan.dev/ffmpeg/builds/
    echo.
    pause
    exit /b 1
)

:: 建立結果檔案
set "logfile=video_integrity_report_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "logfile=!logfile: =0!"
set "errorfile=corrupted_videos.txt"

echo 檢測開始時間：%date% %time% > "!logfile!"
echo =============================================== >> "!logfile!"
echo.

:: 統計檔案數量
set count=0
for %%f in (*.mp4) do (
    set /a count+=1
)

if !count! equ 0 (
    echo 在當前目錄中找不到MP4檔案！
    echo 請確認您在正確的目錄中運行此批次檔。
    pause
    exit /b 1
)

echo 找到 !count! 個MP4檔案，開始檢測...
echo.

:: 初始化計數器
set processed=0
set errors=0
set success=0

:: 清空錯誤檔案列表
if exist "!errorfile!" del "!errorfile!"

:: 處理每個MP4檔案
for %%f in (*.mp4) do (
    set /a processed+=1
    
    echo [!processed!/!count!] 正在檢測: %%~nxf
    echo [!processed!/!count!] 檢測檔案: %%~nxf >> "!logfile!"
    
    :: 執行ffmpeg檢測
    ffmpeg -v error -i "%%f" -f null - 2> "temp_error.log"
    
    :: 檢查錯誤日誌
    if exist "temp_error.log" (
        for %%a in ("temp_error.log") do set size=%%~za
        if !size! gtr 0 (
            echo    ✗ 發現錯誤！
            echo    ✗ 發現錯誤 >> "!logfile!"
            echo %%~nxf >> "!errorfile!"
            set /a errors+=1
            
            :: 將錯誤詳情寫入日誌
            echo    錯誤詳情： >> "!logfile!"
            type "temp_error.log" >> "!logfile!"
            echo. >> "!logfile!"
        ) else (
            echo    ✓ 檢測通過
            echo    ✓ 檢測通過 >> "!logfile!"
            set /a success+=1
        )
        del "temp_error.log"
    ) else (
        echo    ✓ 檢測通過
        echo    ✓ 檢測通過 >> "!logfile!"
        set /a success+=1
    )
    
    echo. >> "!logfile!"
)

:: 生成統計報告
echo.
echo ===============================================
echo 檢測完成！統計結果：
echo ===============================================
echo 總檔案數：!count!
echo 檢測通過：!success!
echo 發現錯誤：!errors!
echo.

:: 寫入統計到日誌
echo =============================================== >> "!logfile!"
echo 檢測統計結果： >> "!logfile!"
echo =============================================== >> "!logfile!"
echo 檢測完成時間：%date% %time% >> "!logfile!"
echo 總檔案數：!count! >> "!logfile!"
echo 檢測通過：!success! >> "!logfile!"
echo 發現錯誤：!errors! >> "!logfile!"

if !errors! gtr 0 (
    echo 有問題的檔案列表已保存到：!errorfile!
    echo.
    echo 有問題的檔案：
    type "!errorfile!"
)

echo.
echo 詳細報告已保存到：!logfile!
echo.
pause
```

## 簡化版本 (check_videos_simple.bat)

```batch
@echo off
setlocal enabledelayedexpansion

chcp 65001 >nul

echo 開始檢測MP4檔案完整性...
echo.

set count=0
set errors=0

for %%f in (*.mp4) do (
    set /a count+=1
    echo [!count!] 檢測: %%~nxf
    
    ffmpeg -v error -i "%%f" -f null - 2> nul
    if !errorlevel! neq 0 (
        echo    ✗ 檔案可能損壞
        set /a errors+=1
    ) else (
        echo    ✓ 檔案正常
    )
)

echo.
echo 檢測完成！共檢測 !count! 個檔案，發現 !errors! 個可能有問題的檔案。
pause
```

## 高級版本 (check_videos_advanced.bat)

```batch
@echo off
setlocal enabledelayedexpansion

chcp 65001 >nul

:: 設定ffmpeg路徑（如果需要）
:: set "FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe"
:: 如果ffmpeg在PATH中，使用預設
set "FFMPEG_PATH=ffmpeg"

echo ===============================================
echo          高級MP4影片完整性檢測工具
echo ===============================================
echo.

:: 檢查ffmpeg
%FFMPEG_PATH% -version >nul 2>&1
if !errorlevel! neq 0 (
    echo 錯誤：無法執行ffmpeg！
    echo 請檢查ffmpeg是否正確安裝並在PATH中。
    pause
    exit /b 1
)

:: 詢問檢測選項
echo 選擇檢測模式：
echo 1. 快速檢測（只檢查錯誤）
echo 2. 詳細檢測（檢查所有訊息）
echo 3. 深度檢測（完整讀取檔案）
echo.
set /p mode="請選擇模式 (1-3): "

if "!mode!"=="1" set "ffmpeg_opts=-v error -f null -"
if "!mode!"=="2" set "ffmpeg_opts=-v warning -f null -"
if "!mode!"=="3" set "ffmpeg_opts=-v error -f null - -benchmark"

if "!ffmpeg_opts!"=="" (
    echo 無效選擇，使用預設快速檢測模式
    set "ffmpeg_opts=-v error -f null -"
)

echo.
echo 開始檢測，請稍候...
echo.

set count=0
set errors=0
set startTime=%time%

:: 建立詳細日誌
set "detailLog=detail_log_%date:~0,4%%date:~5,2%%date:~8,2%.txt"
set "detailLog=!detailLog: =0!"
echo 詳細檢測日誌 - %date% %time% > "!detailLog!"
echo =============================================== >> "!detailLog!"

for %%f in (*.mp4) do (
    set /a count+=1
    echo [!count!] 檢測: %%~nxf
    echo [!count!] 檢測檔案: %%~nxf (大小: %%~zf bytes) >> "!detailLog!"
    
    :: 獲取檔案資訊
    echo    檔案大小: %%~zf bytes
    echo    修改時間: %%~tf
    
    :: 執行ffmpeg檢測
    %FFMPEG_PATH% -i "%%f" !ffmpeg_opts! 2> "temp_check.log"
    set exitCode=!errorlevel!
    
    if !exitCode! neq 0 (
        echo    ✗ 檢測發現問題 (錯誤代碼: !exitCode!)
        echo    ✗ 檢測發現問題 (錯誤代碼: !exitCode!) >> "!detailLog!"
        set /a errors+=1
        
        if exist "temp_check.log" (
            echo    錯誤詳情: >> "!detailLog!"
            type "temp_check.log" >> "!detailLog!"
        )
    ) else (
        echo    ✓ 檢測通過
        echo    ✓ 檢測通過 >> "!detailLog!"
    )
    
    if exist "temp_check.log" del "temp_check.log"
    echo. >> "!detailLog!"
    echo.
)

set endTime=%time%

echo ===============================================
echo 檢測完成！
echo ===============================================
echo 開始時間: !startTime!
echo 結束時間: !endTime!
echo 總檔案數: !count!
echo 問題檔案: !errors!
echo 成功率: !success!%
echo.
echo 詳細日誌: !detailLog!
echo.
pause
```

## 使用說明

1. **安裝ffmpeg**：
   - 下載：https://www.gyan.dev/ffmpeg/builds/
   - 解壓到 C:\ffmpeg
   - 將 C:\ffmpeg\bin 加入系統PATH

2. **使用批次檔**：
   - 將批次檔複製到包含MP4檔案的資料夾
   - 雙擊執行即可

3. **輸出檔案**：
   - `video_integrity_report_*.txt` - 詳細檢測報告
   - `corrupted_videos.txt` - 有問題的檔案列表

4. **檢測原理**：
   - 使用 `ffmpeg -v error -i "檔案.mp4" -f null -` 命令
   - 讀取整個檔案但不輸出，只報告錯誤
   - 如果有錯誤輸出，表示檔案可能損壞