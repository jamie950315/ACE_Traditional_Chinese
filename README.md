
# ACE_Traditional_Chinese 
### 轉換Assetto Corsa Evo簡體中文至繁體中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/yourusername/yourrepository)

## 說明

本專案為結合 Assetto Corsa EVO 的 KsPkg (Kunos Package) 解包工具與簡繁轉換功能，基於 [ntpopgetdope/ace-kspkg](https://github.com/ntpopgetdope/ace-kspkg) 原始碼，並採用 MIT 授權。本版本除了保留原始工具解析、解密及提取功能外，還加入以下最佳化與新功能：

- **非同步平行提取：** 利用 `asyncio` 與 `aiofiles` 實現非同步檔案 I/O，加上 `Semaphore` 限制同時開啟檔案數，確保資源不被耗盡。
- **numpy 向量化 XOR：** 以 numpy 向量化方式加速 XOR 解密運算。
- **進度條顯示：** 提供實時進度條與百分比顯示，方便監控解包進程。
- **在地化轉換：** 整合 OpenCC，針對提取後的 `uiresources\localization` 目錄下的 `cn.tooltips.loc`、`cn.loc` 與 `cn.cars.loc` 檔案進行簡體中文轉換成台灣正體中文。
- **輸出目錄設定：** 所有檔案將直接提取到遊戲安裝目錄：  
  `C:\Program Files (x86)\Steam\steamapps\common\Assetto Corsa EVO`
- **自動重命名：** 解包完成後，自動重命名原始 `content.kspkg` 檔案（附加 .bkup），以迫使遊戲使用解包後內容。

## 系統需求

- **作業系統：** Windows 64-bit
- **Python 版本：** Python 3.8 或更新版本（建議 Python 3.13）
- **依賴套件：**
  - `aiofiles`
  - `numpy`
  - `opencc` （建議使用 [opencc-python-reimplemented](https://pypi.org/project/opencc-python-reimplemented/)）

可透過 pip 安裝依賴：
```bash
pip install aiofiles numpy opencc-python-reimplemented
```

## 使用方法

1. **環境準備：**  
   請確認已安裝 Python 與上述依賴套件。

2. **確認 KsPkg 檔案存在：**  
   `content.kspkg` 應置於遊戲安裝目錄下：  
   `C:\Program Files (x86)\Steam\steamapps\common\Assetto Corsa EVO\`

3. **執行工具：**  
   在命令提示字元中進入工具所在資料夾後執行：
   ```bash
   python ACE_Traditional_Chinese.py
   ```

4. **工具流程：**  
   - 程式會自動解析並解密 `content.kspkg` 的檔案表。
   - 利用非同步方式平行提取所有檔案至遊戲安裝目錄，並在過程中顯示進度條與百分比。
   - 提取完成後，會對 `uiresources\localization` 資料夾下的 `cn.tooltips.loc`、`cn.loc` 與 `cn.cars.loc` 檔案進行簡轉台灣正體處理。
   - 最後自動重命名原始 KsPkg 檔案（加上 `.bkup` 副檔名），迫使 AC:Evo 採用解包後的內容。

## 原始碼結構說明

- **KsPck 類別：**  
  負責解析 KsPkg 檔案、解密檔案表、提取檔案與執行重命名操作。

- **非同步提取與進度追蹤：**  
  利用 `asyncio` 與 `aiofiles` 實現非同步檔案讀寫；`ProgressTracker` 類別提供進度顯示，並配合 `Semaphore` 限制同時開啟的檔案數量。

- **在地化轉換：**  
  使用 OpenCC 的 s2twp 模式，將提取後的在地化檔案從簡體中文轉換為台灣正體中文。

## 修改記錄

- 整合原始工具 (ntpopgetdope/ace-kspkg) 的基本解析與解包邏輯
- 加入非同步 I/O 與 numpy 向量化 XOR 運算，顯著提升解包效能
- 新增進度條功能，實時顯示檔案提取進度
- 修改輸出目錄為遊戲安裝資料夾
- 整合 OpenCC 進行在地化檔案的轉換處理

## 授權條款

本專案基於 [ntpopgetdope/ace-kspkg](https://github.com/ntpopgetdope/ace-kspkg) 原始碼，並採用 MIT 授權條款。詳細授權內容請參閱 [LICENSE](LICENSE) 檔案。

---

**MIT License**

```
Copyright (C) 2025 Jamie950315

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.


THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## 貢獻

歡迎提出 issues 或 pull requests。

## 聯絡

有任何疑問請在 GitHub 上提交 issue。

