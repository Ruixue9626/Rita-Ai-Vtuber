# AI VTuber Controller (Gemini + VTube Studio)

這是一個使用 Python 編寫的 AI VTuber 控制器。它將 **Google Gemini** (LLM) 作為大腦，透過 **VTube Studio API** 控制 Live2D 模型，並結合 **Edge TTS** 與 **Speech Recognition** 實現全語音的即時互動。

## ✨ 功能特色

*   **🧠 智慧大腦**: 使用 Google Gemini (gemma-3-27b-it) 進行角色扮演與對話生成。
*   **🗣️ 語音互動**:
    *   **聽**: 支援麥克風語音辨識 (Google Speech Recognition)，具備 VAD (語音活動偵測) 與 PTT (按鍵發話) 功能。
    *   **說**: 使用 Edge TTS 生成高品質且自然的語音 (支援調整語速與音調)。
*   **🎭 VTube Studio 整合**:
    *   **表情控制**: AI 可根據對話情緒自動觸發 VTS 的熱鍵 (Hotkeys) 表情。
    *   **嘴型同步 (Lip Sync)**: 說話時模型嘴巴會隨語音開合。
    *   **待機動作**: 閒置時模型會自動呼吸與擺動頭部，增加生動感。
    *   **參數控制**: AI 可直接控制 Live2D 參數 (如鼓臉頰、眼神等)。
*   **📝 記憶系統**: 自動儲存與讀取對話歷史 (`memory.txt`)，讓 AI 記住你是誰。
*   **📺 字幕系統**: 內建透明置頂的字幕視窗，即時顯示使用者輸入與 AI 回應。
*   **🤖 自言自語模式**: 可切換模式讓 AI 在沒人說話時自動發起話題。

## 🛠️ 安裝需求

### 1. 軟體
*   Python 3.10+
*   VTube Studio (需在 Steam 下載)

### 2. Python 套件
請在終端機 (Terminal) 或 CMD 執行以下指令安裝所需套件：

```bash
pip install requirements.txt
```

> **注意**: `pyaudio` 在某些 Windows 環境下可能需要額外編譯工具。如果安裝失敗，可嘗試下載對應版本的 `.whl` 檔案安裝，或使用 `pipwin install pyaudio`。

## ⚙️ 設定說明

在使用前，請打開 `Rita_Ai_Vt.py` 並修改以下設定區塊：

1.  **Google API Key**:
    ```python
    GEMINI_API_KEY = "你的_GOOGLE_API_KEY"
    ```
    *   請至 Google AI Studio 申請 API Key。

2.  **記憶檔案路徑**:
    ```python
    MEMORY_FILE = r"你的/檔案/路徑/memory.txt"
    ```
    *   請確保路徑正確，建議使用絕對路徑。

3.  **VTube Studio 設定**:
    *   開啟 VTube Studio。
    *   進入設定 -> 插件 (Plugins) -> 開啟 **"Start API"** (預設 Port 為 8001)。
    *   確保你的模型已經設定好熱鍵 (Hotkeys)，程式會自動讀取並讓 AI 使用。

4.  **角色人設 (Persona)**:
    *   修改 `PERSONA_DESCRIPTION` 變數來改變 AI 的個性、名字與背景故事。

## 🚀 使用方法

1.  **啟動程式**:
    ```bash
    python Rita_Ai_Vt.py
    ```

2.  **VTube Studio 授權**:
    *   第一次執行時，VTube Studio 視窗會跳出「允許插件連線」的請求，請點選 **Allow**。

3.  **開始對話**:
    *   程式啟動後會顯示字幕視窗，並進行麥克風環境音校正 (請保持安靜 1 秒)。
    *   **自動偵測 (VAD)**: 直接對著麥克風說話，停頓後 AI 會自動回應。
    *   **按鍵發話 (PTT)**: 按住鍵盤 **`O`** 鍵說話，放開後送出。

4.  **控制指令**:
    *   **`C` 鍵**: 切換「自言自語模式」(開啟/關閉)。開啟後若一段時間無人說話，AI 會主動說話。
    *   **口語指令**: 對 AI 說「離開」或「結束」可關閉程式。

## 📂 檔案結構

```text
Ai Vt/
├── Rita_Ai_Vt.py  # 主程式
├── memory.txt             # 對話記憶 (自動生成)
├── token.txt              # VTS 授權 Token (自動生成)
└── README.md              # 說明文件
```

## 🐛 常見問題排除

*   **無法連接 VTube Studio**:
    *   請確認 VTS 已開啟。
    *   請確認 VTS 設定中的 "Start API" 已開啟，且 Port 為 8001。
*   **聽不到聲音**:
    *   請檢查電腦音量。
    *   程式會產生暫存的 `.mp3` 檔案，請確保資料夾有寫入權限。
*   **AI 沒有表情變化**:
    *   請確認 VTS 模型中已設定熱鍵 (Keybinds)。
    *   AI 是根據熱鍵名稱來觸發的，建議熱鍵名稱設為英文 (如 `Angry`, `Smile`) 以便 AI 辨識。

## 📝 開發者資訊

*   **開發者**:Ruixue
*   **Discord**: https://discord.gg/mqfKKmQ4Tt
*   **官網**: https://ruixue.onrender.com
---
*Enjoy your AI Waifu!*
