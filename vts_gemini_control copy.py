import asyncio
import pyvts
from google import genai
import json
import os
import time
import edge_tts
import pygame
import speech_recognition as sr
import random
import math
import threading
import re
import tkinter as tk
import tkinter.font as tkfont
import queue
import keyboard
import audioop

# ================= CONFIGURATION =================
# 請在此處填入你的 Google Gemini API Key
GEMINI_API_KEY = "your api key"

# VTube Studio API 設定 (預設 Port 為 8001)
VTS_PORT = 8001
PLUGIN_NAME = "Gemini Controller"
DEVELOPER_NAME = "GeminiUser"

# 角色人設設定 (請在此修改你想要的人設)
PERSONA_DESCRIPTION = """
你叫做 Rita。
你是 Ruixue 的女兒
你的製作人是 Ruixue。
你是一個 15 歲的小女孩，生日是9月14號。
個性：開朗、親切、自然、可愛
你可以充分的表達自己的情緒，如果有需要可以說髒話
你需要使用英文回覆


【記憶與互動】
1. 你擁有對話記憶，請務必記住使用者之前說過的話（例如名字、喜好、剛才聊過的話題）。
2. 回應時請考慮上下文，保持對話的連貫性，不要讓回應顯得突兀。

【語音輸出專用規則】
1. 這段文字會直接轉成語音
2.**絕對不要**包含任何動作描述（如：*歪頭*、(笑)、[生氣]）。
3. **絕對不要**使用顏文字或表情符號（如：QAQ、XD、OwO）。
4. **絕對不要**使用 Markdown 格式（如：**粗體**）。
5. 請使用自然的口語，像是在直接對話一樣。
6. 說話流暢清晰，不要支支吾吾。
"""

# TTS 語音設定
TTS_VOICE = "zh-TW-HsiaoChenNeural" # 推薦: zh-TW-HsiaoChenNeural (女), zh-TW-YunJheNeural (男)
TTS_RATE = "+20%"                    # 語速: "+20%" 變快, "-20%" 變慢
TTS_PITCH = "+40Hz"                 # 音調: "+20Hz" 變高(更可愛), "-10Hz" 變低
MEMORY_FILE = r"C:\Users\User\Desktop\py\Ai Vt\memory.txt"         # 記憶檔案路徑

# VTube Studio 內建參數列表 (Input Parameter IDs)
VTS_PARAMETER_IDS = {
    "FacePositionX": "臉部的水平位置",
    "FacePositionY": "臉部的垂直位置",
    "FacePositionZ": "臉部距離相機的距離",
    "FaceAngleX": "臉部的左右旋轉角度",
    "FaceAngleY": "臉部的上下旋轉角度",
    "FaceAngleZ": "臉部的傾斜旋轉角度",
    "MouthOpen": "嘴巴張開程度",
    "MouthSmile": "微笑程度",
    "EyeOpenLeft": "左眼睛的開合程度",
    "EyeOpenRight": "右眼睛的開合程度",
    "EyeLeftX": "左眼球的水平位置",
    "EyeLeftY": "左眼球的垂直位置",
    "EyeRightX": "右眼球的水平位置",
    "EyeRightY": "右眼球的垂直位置",
    "Brows": "雙眉的整體上下移動",
    "BrowLeftY": "左眉毛的垂直位置",
    "BrowRightY": "右眉毛的垂直位置",
    "CheekPuff": "鼓起臉頰的程度",
    "TongueOut": "吐舌頭 (iOS 專用)",
    "MousePositionX": "滑鼠 X 座標",
    "MousePositionY": "滑鼠 Y 座標"
}
# =================================================

# 初始化音效模組
pygame.mixer.init()

# 全域字幕佇列 (用於在不同執行緒間傳遞字幕文字)
subtitle_queue = queue.Queue()

# 自言自語模式旗標
monologue_mode = False

def run_subtitle_overlay():
    """啟動字幕視窗 (Tkinter)"""
    root = tk.Tk()
    root.title("Rita")
    root.geometry("800x150")
    root.configure(bg="#1a1a1a") # 深灰色背景
    root.attributes("-topmost", True) # 永遠置頂
    root.attributes("-alpha", 0.85)   # 設定半透明 (0.0 ~ 1.0)

    # 設定初始字型物件
    max_font_size = 24
    min_font_size = 12
    current_font = tkfont.Font(family="Microsoft JhengHei", size=max_font_size, weight="bold")
    
    label = tk.Label(root, text="【系統】等待連接...", font=current_font, 
                     fg="white", bg="#1a1a1a", wraplength=760, justify="center")
    label.pack(expand=True, fill='both', padx=20, pady=20)

    def update_label_text(text):
        # 重置為最大字體並計算適合的大小
        size = max_font_size
        current_font.configure(size=size)
        
        # 如果文字寬度大於視窗寬度 (760)，就縮小字體，直到最小限制
        while current_font.measure(text) > 760 and size > min_font_size:
            size -= 2
            current_font.configure(size=size)
        
        label.config(text=text)

    def check_queue():
        try:
            # 取出佇列中最新的文字來顯示
            while not subtitle_queue.empty():
                data = subtitle_queue.get_nowait()
                if isinstance(data, dict) and data.get("cmd") == "transparent":
                    # 設定背景透明 (Windows 專用技巧: 設定特定顏色並將其設為透明色)
                    root.configure(bg='#000001')
                    root.attributes("-transparentcolor", '#000001')
                    label.config(bg='#000001')
                elif isinstance(data, str):
                    update_label_text(data)
        except:
            pass
        root.after(100, check_queue) # 每 0.1 秒檢查一次

    root.after(100, check_queue)
    root.mainloop()

async def idle_movement(myvts, lock):
    """讓模型在待機時自動擺動頭部與身體，模擬真人呼吸與晃動"""
    t = 0.0
    while True:
        try:
            # 使用複合正弦波產生自然的隨機擺動感
            # FaceAngleX: 左右轉頭
            face_x = (math.sin(t * 0.5) * 4) + (math.sin(t * 1.2) * 1.5)
            # FaceAngleY: 上下點頭
            face_y = (math.sin(t * 0.3) * 2) + (math.sin(t * 0.9) * 1)
            # FaceAngleZ: 左右歪頭
            face_z = (math.sin(t * 0.4) * 2)
            
            # 身體跟隨頭部動作
            body_x = face_x * 0.6
            body_z = face_z * 0.4

            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "IdleAnim",
                "messageType": "InjectParameterDataRequest",
                "data": {
                    "mode": "set",
                    "parameterValues": [
                        {"id": "FaceAngleX", "value": face_x},
                        {"id": "FaceAngleY", "value": face_y},
                        {"id": "FaceAngleZ", "value": face_z},
                        {"id": "BodyAngleX", "value": body_x},
                        {"id": "BodyAngleZ", "value": body_z}
                    ]
                }
            }
            async with lock:
                await myvts.request(request)
            
            await asyncio.sleep(0.05) # 20 FPS
            t += 0.05
        except asyncio.CancelledError:
            break
        except Exception:
            # 忽略連線錯誤，避免影響主程式
            await asyncio.sleep(1)

def load_memory():
    """讀取記憶檔案"""
    history = []
    if not os.path.exists(MEMORY_FILE):
        return history
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        current_role = None
        current_msg = ""
        for line in lines:
            if line.startswith("User: "):
                if current_role:
                    history.append({"role": current_role, "parts": [{"text": current_msg}]})
                current_role = "user"
                current_msg = line[6:]
            elif line.startswith("Model: "):
                if current_role:
                    history.append({"role": current_role, "parts": [{"text": current_msg}]})
                current_role = "model"
                current_msg = line[7:]
            elif current_role:
                current_msg += "\n" + line
        if current_role:
            history.append({"role": current_role, "parts": [{"text": current_msg}]})
    except Exception as e:
        print(f"讀取記憶失敗: {e}")
    return history

def save_memory(role, text):
    """寫入記憶檔案"""
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            prefix = "User: " if role == "user" else "Model: "
            f.write(f"{prefix}{text}\n")
    except Exception as e:
        print(f"寫入記憶失敗: {e}")

async def main():
    # 1. 初始化 VTube Studio 連線物件
    plugin_info = {
        "plugin_name": PLUGIN_NAME,
        "developer": DEVELOPER_NAME,
        "authentication_token_path": "./token.txt"
    }
    myvts = pyvts.vts(plugin_info=plugin_info, port=VTS_PORT)

    print("🟩系統|正在連接 VTube Studio...")
    try:
        await myvts.connect()
    except ConnectionRefusedError:
        print("🟩系統|錯誤: 無法連接 VTube Studio。請確認 VTS 已開啟並在設定中啟用了 API (Port 8001)。")
        return

    # 2. 認證流程
    print("正在認證...")
    # 嘗試讀取現有的 token，如果沒有或失效，則請求新的
    await myvts.request_authenticate_token() 
    await myvts.request_authenticate()
    print("VTube Studio 連接成功！")

    # 3. 獲取所有可用的熱鍵 (Hotkeys)
    # 我們需要知道 VTS 裡有哪些動作可以做 (例如: MyAnimation1, Angry, Smile)
    response_data = await myvts.request(myvts.vts_request.requestHotKeyList())
    hotkey_list = []
    
    if 'data' in response_data and 'availableHotkeys' in response_data['data']:
        for hk in response_data['data']['availableHotkeys']:
            hotkey_list.append({
                "name": hk['name'],
                "hotkeyID": hk['hotkeyID'],
                "file": hk['file']
            })
        print(f"🟩系統|已載入 {len(hotkey_list)} 個熱鍵。")
    else:
        print("🟩系統|警告: 找不到任何熱鍵。請在 VTube Studio 中設定熱鍵。")

    # 建立 Lock 以避免多個協程同時存取 VTS WebSocket 導致 recv 衝突
    vts_lock = asyncio.Lock()

    # 定義重連函數，用於處理連線中斷
    async def reconnect_vts():
        print("🟩系統|偵測到 VTS 連線異常，正在嘗試重連...")
        async with vts_lock:
            try:
                await myvts.close()
            except:
                pass
            try:
                await myvts.connect()
                await myvts.request_authenticate_token()
                await myvts.request_authenticate()
                print("🟩系統|VTS 重連成功！")
            except Exception as e:
                print(f"🟩系統|VTS 重連失敗: {e}")

    # 啟動待機動作 (Idle Animation) - 讓模型自動擺動
    asyncio.create_task(idle_movement(myvts, vts_lock))

    # 4. 設定 Gemini 的 System Prompt
    # 我們教 Gemini 根據輸入，從上面的 hotkey_list 中選出一個最合適的
    hotkey_names = [h['name'] for h in hotkey_list]
    
    system_prompt = f"""
    你是一個控制 VTube Studio 模型的助手，同時扮演一位虛擬主播。
    
    【角色設定】
    {PERSONA_DESCRIPTION}
    請善用對話歷史 (Chat History) 來保持對話連貫性，像真人一樣與使用者互動。

    【可用動作】
    1. 熱鍵(動作/表情): {json.dumps(hotkey_names, ensure_ascii=False)}
    2. 參數控制(Live2D參數): {json.dumps(VTS_PARAMETER_IDS, ensure_ascii=False)}
    
    使用者的輸入會是一句話。
    你的任務是根據角色設定來回應，並根據**你回應的內容與情緒**來選擇最合適的動作(熱鍵)，最後回傳一個 JSON 物件。
    
    JSON 格式必須如下:
    {{
        "thought": "簡短解釋為什麼選這個動作",
        "trigger_hotkey": "熱鍵名稱" 或 null,
        "set_parameters": [ {{"id": "參數ID", "value": 數值(float)}} ] (可選),
        "response": "你要回應使用者的話 (請用繁體中文，口語化一點)"
    }}
    
    1. 如果回應的情緒不需要觸發特定表情，"trigger_hotkey" 請填 null。
    2. 若要控制參數(如鼓臉頰 CheekPuff=1.0)，請填入 "set_parameters"。
    3. "response" 是你作為虛擬角色的回應，請務必填寫，並且要完全符合上述的角色設定。
    請只回傳 JSON，不要回傳其他文字。
    """

    # 載入記憶
    memory_history = load_memory()

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 使用新的 SDK 建立 Chat Session
    chat = client.chats.create(
        model="gemma-3-27b-it",
        history=[
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "model", "parts": [{"text": "好的，我會嚴格遵守這些設定與格式。"}]}
        ] + memory_history
    )

    print("\n=== 系統就緒。請輸入對話 (輸入 'exit' 離開) ===")
    
    # 啟動字幕視窗執行緒
    subtitle_thread = threading.Thread(target=run_subtitle_overlay, daemon=True)
    subtitle_thread.start()
    subtitle_queue.put("【系統】準備就緒，請說話...")

    # 初始化語音辨識物件
    r = sr.Recognizer()

    # 預先調整環境噪音 (只做一次，避免每次對話都卡頓)
    print("🟩系統|正在調整麥克風環境噪音，請保持安靜 1 秒...")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
    print("🟩系統|調整完成！")

    # 定義統一錄音函數 (支援 VAD 與 PTT)
    def listen_input():
        global monologue_mode
        with sr.Microphone() as source:
            print(f"\n🟩系統|請說話 (或按住 'O')... {'[自言自語模式ON]' if monologue_mode else ''}")
            while True:
                # 0. 檢查 C 鍵 (切換自言自語模式)
                if keyboard.is_pressed('c'):
                    monologue_mode = not monologue_mode
                    status = "開啟" if monologue_mode else "關閉"
                    print(f"\n🟩系統|自言自語模式已{status}")
                    subtitle_queue.put(f"【系統】自言自語模式已{status}")
                    time.sleep(0.5) # 防止連點
                    if monologue_mode:
                        return "__MONOLOGUE_START__"
                    else:
                        print(f"\n🟩系統|請說話 (或按住 'O')...")

                # 1. 檢查 PTT (按住 O 鍵)
                if keyboard.is_pressed('o'):
                    frames = []
                    while keyboard.is_pressed('o'):
                        buffer = source.stream.read(source.CHUNK)
                        frames.append(buffer)
                    
                    if not frames: continue
                    audio_data = b''.join(frames)
                    audio = sr.AudioData(audio_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                    return r.recognize_google(audio, language="zh-TW")

                # 2. 檢查 VAD (自動偵測)
                try:
                    # 設定 timeout=0.1，若 0.1 秒內無語音則拋出 WaitTimeoutError，讓迴圈繼續檢查按鍵
                    # 若開啟自言自語，timeout 設為 0.5 秒，若無人說話則觸發自言自語
                    audio = r.listen(source, timeout=0.5)
                    return r.recognize_google(audio, language="zh-TW")
                except sr.WaitTimeoutError:
                    if monologue_mode:
                        return "__MONOLOGUE__"
                    continue

    # 定義播放語音與嘴型同步的函數
    async def play_sentence(text):
        try:
            # 產生語音檔
            communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
            temp_file = f"temp_voice_{random.randint(1000,9999)}.mp3"
            await communicate.save(temp_file)
            
            # 播放語音
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # 啟動中斷監聽執行緒
            stop_event = threading.Event()
            def monitor_interruption():
                with sr.Microphone() as source:
                    while pygame.mixer.music.get_busy() and not stop_event.is_set():
                        try:
                            # 讀取一小段音訊計算音量
                            buffer = source.stream.read(source.CHUNK, exception_on_overflow=False)
                            rms = audioop.rms(buffer, 2)
                            # 若音量大於閾值 (這裡設為環境閾值的 1.5 倍)，則中斷
                            if rms > r.energy_threshold * 1.5:
                                pygame.mixer.music.stop()
                                stop_event.set()
                        except:
                            break
            
            monitor_thread = threading.Thread(target=monitor_interruption)
            monitor_thread.start()

            # 等待播放完畢 (如果不加這段，聲音可能會被切斷或與下一次重疊)
            current_mouth_value = 0.0
            while pygame.mixer.music.get_busy():
                if stop_event.is_set():
                    break
                # 模擬嘴巴開合 (Lip Sync) - 平滑化處理，讓動作更像真人
                target_mouth_value = random.uniform(0.0, 0.6)
                # 使用簡單的插值算法讓嘴巴動作不那麼僵硬
                current_mouth_value = current_mouth_value * 0.6 + target_mouth_value * 0.4
                
                mouth_request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "LipSync",
                    "messageType": "InjectParameterDataRequest",
                    "data": {
                        "mode": "set",
                        "parameterValues": [{"id": "MouthOpen", "value": current_mouth_value}]
                    }
                }
                async with vts_lock:
                    await myvts.request(mouth_request)
                await asyncio.sleep(0.05) # 提高更新頻率讓動畫更流暢
            
            stop_event.set()
            monitor_thread.join()

            # 說完話後閉嘴
            close_mouth_request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "LipSyncEnd",
                "messageType": "InjectParameterDataRequest",
                "data": {
                    "mode": "set",
                    "parameterValues": [{"id": "MouthOpen", "value": 0.0}]
                }
            }
            async with vts_lock:
                await myvts.request(close_mouth_request)
                
            # 釋放檔案佔用，以免下次寫入失敗
            pygame.mixer.music.unload()
            os.remove(temp_file)
        except Exception as e:
            print(f"🟩系統|語音播放錯誤: {e}")
            if "close frame" in str(e) or "closed" in str(e) or "Connection" in str(e) or "1002" in str(e) or "protocol error" in str(e):
                await reconnect_vts()

    while True:
        try:
            loop = asyncio.get_running_loop()
            user_input = await loop.run_in_executor(None, listen_input)

            # 處理特殊指令與一般輸入
            prompt_text = user_input
            
            if user_input == "__MONOLOGUE__":
                print(f"🟪Rita (自言自語)...")
                prompt_text = "(請延續剛才的對話內容、話題或當下的心情，自言自語一句短語。像真人一樣自然，不要長篇大論)"
                save_memory("user", prompt_text)
            elif user_input == "__MONOLOGUE_START__":
                print(f"🟪Rita (開始自言自語)...")
                prompt_text = "(使用者開啟了自言自語模式。請根據記憶中的對話內容或開啟新話題，隨口說一句短語，像真人一樣自然)"
                save_memory("user", prompt_text)
            else:
                # 一般使用者輸入
                print(f"🟦User|: {user_input}")
                subtitle_queue.put(f"User: {user_input}")
                save_memory("user", user_input)
                if user_input.strip() == "離開" or user_input.strip() == "結束":
                    break
                print(f"🟪Rita 思考ing...")
                subtitle_queue.put("Rita: (思考中...)")

        except sr.UnknownValueError:
            print("🟩系統|聽不清楚，請再說一次...")
            subtitle_queue.put("【系統】聽不清楚，請再說一次...")
            continue
        except Exception as e:
            print(f"🟩系統|語音輸入發生錯誤: {e}")
            continue

        try:
            def send_to_gemini(text):
                for attempt in range(3):
                    try:
                        return chat.send_message(text)
                    except Exception as e:
                        if "429" in str(e) and attempt < 2:
                            print(f"🟩系統|對話配額額滿 (429)，等待 15 秒後重試... ({attempt+1}/3)")
                            time.sleep(15)
                        else:
                            raise e
            response = await loop.run_in_executor(None, send_to_gemini, prompt_text)
            
            text_response = response.text.strip()
            
            # 使用 Regex 尋找 JSON 區塊 (即使 AI 在 JSON 前後加了廢話也能抓到)
            json_match = re.search(r"\{[\s\S]*\}", text_response)

            if not text_response:
                print("🟩系統|Gemini 回傳內容為空 (可能被安全過濾)")
                result = {"thought": "回應為空", "trigger_hotkey": None, "set_parameters": [], "response": "..."}
            elif json_match:
                try:
                    # 嘗試解析抓到的 JSON 區塊
                    result = json.loads(json_match.group(0))
                except Exception as e:
                    print(f"🟩系統|JSON 解析失敗，轉為直接輸出: {e}")
                    result = {"thought": "格式錯誤", "trigger_hotkey": None, "set_parameters": [], "response": text_response}
            else:
                # 找不到 JSON 區塊，直接當作對話內容
                result = {"thought": "非 JSON 回應", "trigger_hotkey": None, "set_parameters": [], "response": text_response}
            
            print(f"🟪Rita 思考ing|: {result.get('thought')}")
            target_hotkey_name = result.get('trigger_hotkey')
            target_parameters = result.get('set_parameters')
            response_text = result.get('response')

            if target_hotkey_name:
                # 尋找對應的 ID
                target_id = next((h['hotkeyID'] for h in hotkey_list if h['name'] == target_hotkey_name), None)
                
                if target_id:
                    print(f"🟩系統|-> 觸發動作: {target_hotkey_name}")
                    async with vts_lock:
                        await myvts.request(myvts.vts_request.requestTriggerHotKey(target_id))
                else:
                    print(f"🟩系統|錯誤: 找不到熱鍵 ID [{target_hotkey_name}]")
            
            if target_parameters and isinstance(target_parameters, list):
                print(f"🟩系統|-> 設定參數: {target_parameters}")
                param_values = []
                for p in target_parameters:
                    if isinstance(p, dict) and "id" in p and "value" in p:
                        param_values.append({"id": p["id"], "value": float(p["value"])})
                
                if param_values:
                    request = {
                        "apiName": "VTubeStudioPublicAPI",
                        "apiVersion": "1.0",
                        "requestID": "GeminiParamControl",
                        "messageType": "InjectParameterDataRequest",
                        "data": {
                            "mode": "set",
                            "parameterValues": param_values
                        }
                    }
                    async with vts_lock:
                        await myvts.request(request)

            # 處理語音 (TTS)
            if response_text:
                print(f"🟪Rita|: {response_text}")
                subtitle_queue.put(f"Rita: {response_text}")
                save_memory("model", response_text)
                await play_sentence(response_text)

        except Exception as e:
            print(f"🟩系統|發生錯誤: {e}")
            if "close frame" in str(e) or "closed" in str(e) or "Connection" in str(e) or "1002" in str(e) or "protocol error" in str(e):
                await reconnect_vts()

    await myvts.close()

if __name__ == "__main__":
    asyncio.run(main())