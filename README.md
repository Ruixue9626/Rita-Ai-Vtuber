# 🪄 Rita Ai Vtuber 

這是一個結合 Google Gemini AI 與 VTube Studio 的自動化控制程式。透過此程式，你可以讓 AI 角色「Rita」擁有聽覺、視覺與語音表達能力，並自動觸發 VTube Studio 中的模型動作。

### 🌟 核心功能
* **AI 邏輯思考**：使用 Google Gemini API 作為對話大腦，具備上下文記憶能力。
* **視覺認知**：支援螢幕擷取功能，當使用者說出「你看」等關鍵字時，AI 會分析螢幕內容。
* **VTube Studio 連動**：自動偵測並觸發模型熱鍵（Hotkeys），讓表情與對話同步。
* **自動待機動畫**：內建呼吸與身體隨機擺動演算法，讓模型在待機時更具生命力。
* **語音與嘴型同步**：整合 Edge-TTS 與 pygame，實現語音播放並根據音量模擬嘴部開合（Lip Sync）。
* **即時字幕視窗**：內建 Tkinter 透明置頂字幕視窗，方便直播或錄影使用。

---

### 🛠️ 快速開始

#### 1. 環境需求
請確保您的系統已安裝 Python 3.9+，並安裝以下必要套件：
```bash
pip install asyncio pyvts google-genai edge-tts pygame SpeechRecognition Pillow
