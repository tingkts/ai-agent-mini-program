<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# 請問能用一個程式遞迴找

C:\Users\tingsung

此目錄下的所有資料夾

找出這一個月內容量(佔用磁碟空間)增加最多的，從大到小排序，列出前 20 個資料夾。

請這樣列出來，一個資歷夾一行，由大到小列出 20 行。

資料夾名稱(完整路徑)   資料夾大小    增加的大小

我將為您提供一個 Python 程式，能夠遞迴找出 `C:\Users\tingsung` 目錄下一個月內容量增加最多的前 20 個資料夾。

## Python 程式碼

```python
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
```


## 程式特色說明

### **主要功能**[^1_1][^1_2][^1_3]

- **遞迴搜尋**: 使用 `os.walk()` 遞迴遍歷指定目錄下的所有子資料夾
- **容量計算**: 準確計算每個資料夾的總大小
- **時間篩選**: 識別過去 30 天內修改或新增的檔案
- **排序輸出**: 按增長量從大到小排序，輸出前 20 個資料夾


### **錯誤處理**[^1_4][^1_5]

- 自動跳過無法存取的檔案和資料夾
- 處理權限不足或檔案被佔用的情況
- 支援中斷操作（Ctrl+C）


### **輸出格式**

程式會以表格形式輸出結果，包含：

- 資料夾完整路徑
- 資料夾總大小（格式化顯示，如 MB, GB 等）
- 過去一個月增加的大小


### **使用方式**

1. 將程式碼儲存為 `.py` 檔案（例如 `folder_analyzer.py`）
2. 開啟命令提示字元或 PowerShell
3. 執行 `python folder_analyzer.py`

**注意事項:**

- 程式執行時間可能較長，取決於資料夾數量和檔案大小
- 需要足夠的權限存取目標目錄
- 建議在系統負載較低時執行，以獲得更好的效能

這個程式能有效幫您找出佔用空間增長最快的資料夾，便於進行磁碟空間管理和清理作業。

<div style="text-align: center">⁂</div>

[^1_1]: https://steam.oxxostudio.tw/category/python/basic/recursion.html

[^1_2]: https://vocus.cc/article/6487688bfd89780001315b7a

[^1_3]: https://blog.csdn.net/u010525694/article/details/80335226

[^1_4]: https://steam.oxxostudio.tw/category/python/library/os.html

[^1_5]: https://mnya.tw/cc/word/1960.html

[^1_6]: http://arxiv.org/pdf/2408.17344.pdf

[^1_7]: http://arxiv.org/pdf/2502.02464.pdf

[^1_8]: https://joss.theoj.org/papers/10.21105/joss.05213.pdf

[^1_9]: https://arxiv.org/pdf/2209.06909.pdf

[^1_10]: https://arxiv.org/pdf/2306.13785.pdf

[^1_11]: http://arxiv.org/pdf/1902.02698.pdf

[^1_12]: https://arxiv.org/pdf/2207.02476.pdf

[^1_13]: https://www.jstatsoft.org/index.php/jss/article/view/v065c01/v65c01.pdf

[^1_14]: https://blog.csdn.net/weixin_41571493/article/details/81875088

[^1_15]: https://diveintopython.dev.org.tw/learn/functions/recursion

[^1_16]: https://www.reddit.com/r/Python/comments/zd6fay/best_piece_of_obscure_advanced_python_knowledge/?tl=zh-hant

[^1_17]: https://hackmd.io/@bangyewu/SySyHxaSa

[^1_18]: https://docs.aws.amazon.com/zh_tw/systems-manager/latest/userguide/inventory-file-and-registry.html

[^1_19]: https://blog.51cto.com/u_16175472/8757036

[^1_20]: https://www.cnblogs.com/yifanrensheng/p/13771892.html

[^1_21]: https://learn.microsoft.com/zh-tw/answers/questions/3169939/question-3169939?forum=windows-all

[^1_22]: https://blog.csdn.net/weixin_39640687/article/details/109940778

[^1_23]: https://vocus.cc/article/649af72bfd89780001053665

[^1_24]: https://neohsuxoops.blogspot.com/2020/06/phpfunction-xoops.html

[^1_25]: https://blog.csdn.net/qq_34369025/article/details/78181909

[^1_26]: https://blog.csdn.net/qq_36187610/article/details/123327989

[^1_27]: https://www.youtube.com/watch?v=Y360stcBmNQ

[^1_28]: https://hackmd.io/@CynthiaChuang/How-to-count-the-lines-in-Python

[^1_29]: https://academic.oup.com/bioinformatics/advance-article-pdf/doi/10.1093/bioinformatics/btad346/50453056/btad346.pdf

[^1_30]: https://joss.theoj.org/papers/10.21105/joss.03896.pdf

[^1_31]: https://joss.theoj.org/papers/10.21105/joss.03330.pdf

[^1_32]: http://arxiv.org/pdf/2409.03803.pdf

[^1_33]: http://arxiv.org/pdf/1609.00381.pdf

[^1_34]: https://linkinghub.elsevier.com/retrieve/pii/S0010465523000954

[^1_35]: https://pubs.acs.org/doi/10.1021/acs.jcim.3c01318

[^1_36]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10246576/

[^1_37]: https://docs.python.org/zh-tw/dev/library/pathlib.html

[^1_38]: http://tzengyuxio.me/posts/legacy/python-path-walk/

[^1_39]: https://codegym.cc/tw/quests/lectures/tw.codegym.python.core.lecture.level18.lecture01

[^1_40]: https://www.cnblogs.com/even160941/p/16078464.html

[^1_41]: https://blog.csdn.net/zyp626/article/details/126566438

[^1_42]: https://m.300.cn/itzspd/596907.html

[^1_43]: https://blog.csdn.net/q610098308/article/details/134291980

[^1_44]: https://hackmd.io/@bangyewu/BJUaBjlOT

[^1_45]: https://blog.csdn.net/u013654125/article/details/120889716

[^1_46]: https://steam.oxxostudio.tw/category/python/library/calendar.html

[^1_47]: https://steam.oxxostudio.tw/category/python/library/glob.html

[^1_48]: https://ithelp.ithome.com.tw/m/articles/10344110

[^1_49]: https://sdwh.dev/posts/2020/06/Python-File-Metadata-Toys/

[^1_50]: https://dl.acm.org/doi/10.1145/3620665.3640366

[^1_51]: https://ieeexplore.ieee.org/document/10377465/

[^1_52]: https://peerj.com/articles/cs-1516

[^1_53]: https://www.nature.com/articles/s41592-019-0686-2

[^1_54]: https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-023-05385-y

[^1_55]: https://www.nature.com/articles/s41587-021-01206-w

[^1_56]: https://academic.oup.com/bioinformatics/article/doi/10.1093/bioinformatics/btac757/6847088

[^1_57]: https://dl.acm.org/doi/10.1145/3404835.3463238

[^1_58]: https://www.python.digibeatrix.com/zh/file-operations/python-get-filenames-in-folder-guide/

[^1_59]: https://hackmd.io/@LukeTseng/H1D8TUIkC

[^1_60]: https://dev.to/codemee/ji-suan-unc-lu-jing-xia-fen-xiang-zi-liao-jia-de-zong-yong-liang-5bh0

[^1_61]: https://vocus.cc/article/64734156fd89780001785b3b

[^1_62]: https://hackmd.io/@bangyewu/rJl_S-jHa

[^1_63]: https://blog.csdn.net/qq_43069920/article/details/112548368

[^1_64]: https://learnciot.github.io/ch4/ch4.1/

[^1_65]: https://www.reddit.com/r/learnpython/comments/2932xo/osstatpathst_size_printing_weird_sizes/?tl=zh-hant

[^1_66]: https://docs.python.org/zh-tw/3.13/library/heapq.html

[^1_67]: https://www.finlab.tw/超簡單-machine-learning-預測股價/

[^1_68]: https://docs.python.org/zh-tw/dev/tutorial/datastructures.html

[^1_69]: https://docs.python.org/zh-tw/3.13/library/functions.html

[^1_70]: https://hackmd.io/@xcswapJohn/rkefgq_-s

[^1_71]: https://ithelp.ithome.com.tw/m/articles/10324034

[^1_72]: https://techorange.com/2019/09/09/python-replace-excel/

[^1_73]: http://arxiv.org/pdf/2311.08727.pdf

[^1_74]: https://arxiv.org/pdf/2304.00887.pdf

[^1_75]: https://joss.theoj.org/papers/10.21105/joss.01330.pdf

[^1_76]: https://arxiv.org/pdf/2211.16479.pdf

[^1_77]: https://upload.wikimedia.org/wikiversity/en/e/ea/Binary_search_algorithm.pdf

[^1_78]: http://arxiv.org/pdf/2211.13175.pdf

[^1_79]: https://arxiv.org/pdf/2104.02461.pdf

[^1_80]: https://arxiv.org/html/2411.07526v1

[^1_81]: http://arxiv.org/pdf/2404.04552.pdf

[^1_82]: https://arxiv.org/pdf/0901.3751.pdf

[^1_83]: http://arxiv.org/pdf/2304.12313.pdf

[^1_84]: https://arxiv.org/html/2403.05113v1

[^1_85]: https://linux.vbird.org/linux_basic/centos7/0220filemanager.php

[^1_86]: https://www.nvda.org.tw/teaching/article/ui=100204tm=2003664841

[^1_87]: https://joss.theoj.org/papers/10.21105/joss.01655.pdf

[^1_88]: http://arxiv.org/pdf/2402.03693.pdf

[^1_89]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3097064/

[^1_90]: https://jurnal.polinema.ac.id/index.php/jtia/article/download/4818/3442

[^1_91]: https://sites.google.com/view/zsgititit/home/python-cheng-shi-she-ji/di-hui-python

[^1_92]: https://blog.csdn.net/weixin_47661174/article/details/125268191

[^1_93]: https://vocus.cc/article/65656e7bfd8978000155586e

[^1_94]: https://openhome.cc/zh-tw/python/math-abc/comp-assign-logic/

[^1_95]: https://doi.curvenote.com/10.25080/YADT7194

[^1_96]: https://doi.curvenote.com/10.25080/KMXN4784

[^1_97]: https://joss.theoj.org/papers/10.21105/joss.05976.pdf

[^1_98]: https://www.theoj.org/joss-papers/joss.00045/10.21105.joss.00045.pdf

[^1_99]: https://joss.theoj.org/papers/10.21105/joss.01417.pdf

[^1_100]: https://arxiv.org/pdf/1908.01711.pdf

[^1_101]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11629965/

[^1_102]: https://joss.theoj.org/papers/10.21105/joss.02823.pdf

[^1_103]: https://steam.oxxostudio.tw/category/python/basic/string.html

[^1_104]: https://acupun.site/lecture/python_data/


---

## Windows 環境高效統計資料夾大小優化建議

您的原始程式主要瓶頸來自頻繁的磁碟查詢與 Python 迴圈，下面匯整專業的大幅提升建議：

### 1. 用 `os.scandir` 取代 `os.walk` 與 `os.listdir`

- `os.scandir` 直接從系統 API 取得更多檔案屬性，極大減少系統呼叫數，效率明顯優於 `os.walk` 或 `os.listdir`[^2_1][^2_2][^2_3][^2_4][^2_5][^2_6][^2_7]。
- 例如：在 Windows 上，scandir 版本比 os.walk 可快 5-10 倍甚至更高[^2_2][^2_3]。


### 2. 並行/多執行緒加速

- 利用 Python 標準庫的 `concurrent.futures.ThreadPoolExecutor`，資料夾遍歷可平行加速到與 CPU 核心數大致線性成長[^2_8][^2_9][^2_10][^2_11]。


### 3. 實戰優化範例（可直接取用）

```python
import os
import concurrent.futures
from datetime import datetime, timedelta

def get_folder_size_scandir(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            try:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_folder_size_scandir(entry.path)
            except Exception:
                continue
    return total

def get_growth_scandir(path, days=30):
    total = 0
    cutoff = datetime.now() - timedelta(days=days)
    with os.scandir(path) as it:
        for entry in it:
            try:
                if entry.is_file() and datetime.fromtimestamp(entry.stat().st_mtime) >= cutoff:
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_growth_scandir(entry.path, days)
            except Exception:
                continue
    return total

def analyze_folder_growth_parallel(base_path):
    results = []
    dirs = [os.path.join(root, d)
            for root, dir_names, _ in os.walk(base_path) for d in dir_names]

    def worker(folder_path):
        total_size = get_folder_size_scandir(folder_path)
        growth_size = get_growth_scandir(folder_path)
        return (folder_path, total_size, growth_size)

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(worker, d): d for d in dirs}
        for future in concurrent.futures.as_completed(futures):
            try:
                folder_path, total_size, growth_size = future.result()
                if growth_size > 0:
                    results.append({
                        'path': folder_path,
                        'total_size': total_size,
                        'growth_size': growth_size})
            except Exception:
                continue
    results.sort(key=lambda x: x['growth_size'], reverse=True)
    return results[:20]
```


#### 主要差異摘要

- 用 `os.scandir()` 取代原本 `os.walk` 遍歷方式
- 主程式多處理緒平行進行多個子資料夾的大小計算，加速分析


### 4. 其他專業加速思路

- 儘量只計算「必要層級」的資料夾
- 定期快取結果（如將計算結果存入 local DB，後續對比更新）[^2_12]
- 自動忽略明顯不需計算的特殊資料夾（如雲端同步快取、隱藏資料夾等）


### 5. 注意事項

- `os.scandir` 需 Python 3.5+，舊版可手動安裝 `scandir` 套件
- 並行化數量（max_workers）不宜大於 CPU 實體核心
- 大型磁碟結構的真實瓶頸在 I/O，加快只能做到一定極限

**彙總：用 os.scandir 取代 os.walk、加多執行緒是目前 Python 在 Windows 下極速遍歷磁碟樹的最佳實戰，完全可大幅縮短執行所需時間**[^2_1][^2_2][^2_3][^2_4][^2_6][^2_8][^2_10]。

<div style="text-align: center">⁂</div>

[^2_1]: https://github.com/benhoyt/scandir

[^2_2]: https://peps.python.org/pep-0471/

[^2_3]: https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python

[^2_4]: https://wenku.csdn.net/answer/68c59246d8734a8db7de2d00af9d1725

[^2_5]: https://www.geeksforgeeks.org/python/how-to-get-size-of-folder-using-python/

[^2_6]: https://note.nkmk.me/en/python-os-path-getsize/

[^2_7]: https://www.geeksforgeeks.org/python/python-os-scandir-method/

[^2_8]: https://fabric.guru/calculating-folder-size-in-the-lakehouse

[^2_9]: https://stackoverflow.com/questions/68327682/multiprocessing-iteratively-loop-through-files-in-folders

[^2_10]: https://stackoverflow.com/questions/2485719/very-quickly-getting-total-size-of-folder/2485843

[^2_11]: https://www.slingacademy.com/article/python-calculating-total-size-of-a-folder-and-its-contents/

[^2_12]: https://stackoverflow.com/questions/11782475/python-efficient-structure-for-caching-folders-files-and-sizes

[^2_13]: https://ieeexplore.ieee.org/document/10923909/

[^2_14]: https://arxiv.org/abs/2502.10299

[^2_15]: https://ieeexplore.ieee.org/document/11022300/

[^2_16]: https://www.scitepress.org/DigitalLibrary/Link.aspx?doi=10.5220/0012556200003690

[^2_17]: https://arxiv.org/abs/2405.00686

[^2_18]: https://academic.oup.com/nargab/article/doi/10.1093/nargab/lqae177/7928179

[^2_19]: https://link.springer.com/10.1007/s00405-025-09404-x

[^2_20]: https://ieeexplore.ieee.org/document/11004843/

[^2_21]: https://stackoverflow.com/questions/51948306/is-there-a-way-to-optimize-the-time-of-os-walk

[^2_22]: https://r3n.hashnode.dev/tech-chronicles-conquer-memory-monsters-with-pythons-yield-in-large-directory-processing

[^2_23]: https://sureshjoshi.com/development/python-loop-optimization

[^2_24]: https://stackoverflow.com/questions/1987119/fast-folder-size-calculation-in-python-on-windows

[^2_25]: https://gist.github.com/anderssonfilip/8955633

[^2_26]: https://bugs.python.org/issue994057

[^2_27]: https://stackoverflow.com/questions/63479047/most-efficient-way-to-determine-the-size-of-a-directory-in-python

[^2_28]: https://www.reddit.com/r/learnpython/comments/2e2f6u/its_slow_going_traversing_a_large_directory/

[^2_29]: https://stackoverflow.com/questions/15218192/efficient-python-function-to-find-the-size-of-the-directory

[^2_30]: https://www.linkedin.com/pulse/python-calculates-total-size-directory-its-techwith-julles

[^2_31]: https://github.com/benhoyt/betterwalk

[^2_32]: https://www.reddit.com/r/learnpython/comments/1efvknx/any_way_to_speed_up_my_program_or_use_a_more/

[^2_33]: https://www.geeksforgeeks.org/how-to-get-size-of-folder-using-python/

[^2_34]: https://www.semanticscholar.org/paper/71c29d9bd88f21b6f295665c8362cbcbdd5d218f

[^2_35]: http://services.igi-global.com/resolvedoi/resolve.aspx?doi=10.4018/978-1-60960-741-8.ch008

[^2_36]: https://pubsonline.informs.org/doi/suppl/10.1287/ijoc.2022.0263

[^2_37]: https://www.semanticscholar.org/paper/8b5909e09c749aad38912421fddf34891165af07

[^2_38]: https://arxiv.org/pdf/2107.03272.pdf

[^2_39]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10074187/

[^2_40]: https://academic.oup.com/bioinformatics/article-pdf/31/2/166/49011133/bioinformatics_31_2_166.pdf

[^2_41]: https://thepythoncode.com/article/get-directory-size-in-bytes-using-python

[^2_42]: https://discuss.python.org/t/redesign-pycache/75684

[^2_43]: https://www.tutorialspoint.com/how-to-calculate-a-directory-size-using-python

[^2_44]: https://dev.to/alexiskypridemos/sort-items-in-a-directory-by-descending-size-using-python-powershell-c-or-go-17g6

[^2_45]: https://realpython.com/lru-cache-python/

[^2_46]: https://zetcode.com/python/os-scandir/

[^2_47]: https://arxiv.org/abs/2312.14949

[^2_48]: https://scientifictemper.com/index.php/tst/article/view/705

[^2_49]: https://arxiv.org/pdf/2408.01805.pdf

[^2_50]: http://conference.scipy.org/proceedings/scipy2017/pdfs/oleksandr_pavlyk.pdf

[^2_51]: https://joss.theoj.org/papers/10.21105/joss.02564.pdf

[^2_52]: https://arxiv.org/pdf/2203.14484.pdf

[^2_53]: http://conference.scipy.org/proceedings/scipy2016/pdfs/yu_feng.pdf

[^2_54]: http://arxiv.org/pdf/2303.16146.pdf

[^2_55]: https://dl.acm.org/doi/pdf/10.1145/3641885

[^2_56]: https://dl.acm.org/doi/pdf/10.1145/3588195.3592989

[^2_57]: https://arxiv.org/pdf/2309.03931.pdf

[^2_58]: https://linkinghub.elsevier.com/retrieve/pii/S0167739X22003612

[^2_59]: https://www.pythonpeople.nl/recent-python-performance-improvements/

[^2_60]: https://softwareengineering.stackexchange.com/questions/408687/how-can-i-improve-the-speed-of-scanning-multiple-directories-recursively-at-the

[^2_61]: https://discuss.python.org/t/disk-space-used-by-a-file/45205

[^2_62]: https://discuss.python.org/t/add-pathlib-path-walk-method/12968


---

## 高速多執行緒版本：folder_analyzer-opt.py

以下是**可直接執行**的 Python 程式，適用於 Windows 下大磁碟目錄，一次性遞迴找出 `C:\Users\tingsung` 這一個月容量成長最快的前20個資料夾（含完整路徑、資料夾大小、增加的大小）。建議使用 Python 3.7+。

### 用法

1. 將下方程式儲存成 `folder_analyzer-opt.py`
2. 於命令列執行

```
python folder_analyzer-opt.py
```

```python
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
```


### 優化重點

- **os.scandir**：大幅降低系統呼叫次數，顯著快於 os.walk。
- **多執行緒**：利用 ThreadPoolExecutor，實體核心數倍增查詢效率。
- **錯誤強力容忍**：任何單一檔案/目錄權限錯誤都不影響主流程。
- **完整可執行**：無外部依賴，Windows/Linux皆可執行。


### 主要輸出

- 資料夾完整路徑（可自動截斷過長）
- 資料夾總大小（格式化如 MB, GB）
- 過去 30 天的內容增長大小


### 實用說明

- 大型目錄仍需耐心等候（主要瓶頸為硬碟I/O）
- 若需更快，可先用檢查目錄層級與排除明顯不必要的目錄
- 建議提升工作管理員中 Python 執行緒的優先權

此程式適合立即用於磁碟成長偵測與空間清點。

<div style="text-align: center">⁂</div>

[^3_1]: https://arxiv.org/pdf/2205.01351.pdf

[^3_2]: https://arxiv.org/ftp/arxiv/papers/1407/1407.4378.pdf

[^3_3]: https://arxiv.org/pdf/2308.06652.pdf

[^3_4]: https://dl.acm.org/doi/pdf/10.1145/3588195.3592989

[^3_5]: https://arxiv.org/pdf/2006.03879.pdf

[^3_6]: http://arxiv.org/pdf/2403.00539.pdf

[^3_7]: https://arxiv.org/pdf/2401.13150.pdf

[^3_8]: https://digitalcommons.uri.edu/cgi/viewcontent.cgi?article=2144\&context=theses

[^3_9]: https://janakiev.com/blog/python-filesystem-analysis/

[^3_10]: https://stackoverflow.com/questions/63479047/most-efficient-way-to-determine-the-size-of-a-directory-in-python

[^3_11]: https://www.geeksforgeeks.org/how-to-get-size-of-folder-using-python/

[^3_12]: https://www.tutorialspoint.com/how-to-calculate-a-directory-size-using-python

[^3_13]: https://codereview.stackexchange.com/questions/240518/run-dir-scan-as-fast-and-efficient-as-possible-clean-code

[^3_14]: https://www.python.digibeatrix.com/zh/multithreading-async/python-threading-complete-practical-guide/

[^3_15]: https://blog.csdn.net/m0_74972192/article/details/140882022

[^3_16]: https://cloudinfrastack.com/en/about-monitoring/example-of-using-python-multiprocessing-library-for-multithread-processing-files/

[^3_17]: https://www.python.digibeatrix.com/zh/multithreading-async/python-multithreading-complete-guide/

[^3_18]: https://stackoverflow.com/questions/1987119/fast-folder-size-calculation-in-python-on-windows

[^3_19]: https://benhoyt.com/writings/scandir/

[^3_20]: https://realnewbie.com/coding/python/threadpoolexecutor-complete-guide-python-concurrency/

[^3_21]: https://blog.51cto.com/u_16213466/8073511

[^3_22]: https://www.tutorialspoint.com/get-the-list-of-files-in-a-directory-with-size-using-python

[^3_23]: https://steam.oxxostudio.tw/category/python/library/threading.html

[^3_24]: https://www.cnblogs.com/knowledgeYang/p/9459176.html

[^3_25]: http://arxiv.org/pdf/2305.05949.pdf

[^3_26]: https://arxiv.org/pdf/2309.03931.pdf

[^3_27]: https://arxiv.org/abs/2306.11177

[^3_28]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9805561/

[^3_29]: http://arxiv.org/pdf/2205.03373v1.pdf

[^3_30]: https://academic.oup.com/bioinformatics/article-pdf/30/7/1008/642768/btt737.pdf

[^3_31]: https://arxiv.org/pdf/2107.03272.pdf

[^3_32]: http://arxiv.org/pdf/2010.15444v1.pdf

[^3_33]: http://arxiv.org/pdf/2208.14908.pdf

[^3_34]: https://arxiv.org/pdf/2312.11122.pdf

[^3_35]: https://arxiv.org/html/2312.15158v1

[^3_36]: http://arxiv.org/pdf/2407.16353.pdf

[^3_37]: https://softwareengineering.stackexchange.com/questions/408687/how-can-i-improve-the-speed-of-scanning-multiple-directories-recursively-at-the

[^3_38]: https://hackmd.io/@YungHuiHsu/SJ5EgB5eT

[^3_39]: https://blog.csdn.net/zyp626/article/details/126566438

[^3_40]: https://peps.python.org/pep-0471/

