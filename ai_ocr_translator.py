import cv2
import easyocr
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk, ImageGrab
import difflib
import re
from googletrans import Translator
import speech_recognition as sr
import openai
import os
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from gtts import gTTS

# Ortam değişkenlerini yükle
load_dotenv()
openai.api_key = "openai-api-key"

ocr = easyocr.Reader(['en', 'tr'], gpu=True)
recognizer = sr.Recognizer()
translator = Translator()

stats = {"ocr": 0, "voice": 0, "gpt": 0, "translation": 0, "error": 0}

os.makedirs("logs", exist_ok=True)

camera_active = True
last_text = ""
last_voice = ""

def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def get_camera_indexes():
    return [i for i in range(10) if cv2.VideoCapture(i).read()[0]]

def get_microphone_names():
    return sr.Microphone.list_microphone_names()

def detect_language(text):
    text_lower = text.lower()
    turkish_sample_words = ["merhaba", "günaydın", "teşekkür", "lütfen", "evet", "hayır", "nasılsın"]

    if any(c in text for c in "çğıöşüÇĞİÖŞÜ") or any(word in text_lower for word in turkish_sample_words):
        return "tr"  # detected as Turkish
    elif re.search(r"[a-zA-Z]", text):
        return "en"  # fallback to English
    return "en"  # fallback to English
    return "en"  # fallback to English

def translate_text(text):
    try:
        source_lang = detect_language(text)
        target_lang = lang_code_combo.get()

        if source_lang == target_lang:
            write_log(f"Warning: Source and target language are the same ({source_lang}). Translation skipped.")
            return f"[Same language selected: {source_lang}] {text}", target_lang

        translation = translator.translate(text, src=source_lang, dest=target_lang).text
        stats["translation"] += 1
        write_log(f"Translation ({source_lang} → {target_lang}): {translation}")
        return translation, target_lang
    except Exception as e:
        stats["error"] += 1
        write_log(f"Translation error: {e}")
        messagebox.showerror("Translation Error", str(e))
        return str(e), "?"

def benzerlik(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def correct_with_gpt(cumle):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Correct this sentence in its original language: {cumle}"}],
            temperature=0.2
        )
        yanit = response.choices[0].message["content"]
        stats["gpt"] += 1
        write_log(f"GPT Correction: {yanit}")
        return yanit
    except Exception as e:
        stats["error"] += 1
        write_log(f"GPT Error: {e}")
        messagebox.showerror("GPT Error", str(e))
        return str(e)

def speak_text(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("out.mp3")
        os.system("start out.mp3" if os.name == "nt" else "afplay out.mp3")
    except Exception as e:
        messagebox.showerror("Text-to-speech Error", str(e))

def listen_from_mic():
    def dinle():
        global last_voice
        try:
            mic_index = mic_combo.current()
            with sr.Microphone(device_index=mic_index) as source:
                status_label.config(text="🎤 Listening...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=8)
                text = recognizer.recognize_google(audio, language="tr-TR")
                if benzerlik(text, last_voice) < 0.9:
                    last_voice = text
                    stats["voice"] += 1
                    write_log(f"Detected by microphone: {text}")
                    display_text(text, True)
        except Exception as e:
            stats["error"] += 1
            write_log(f"Mikrofon error: {e}")
            status_label.config(text=f"🎤Error: {e}")

    threading.Thread(target=dinle).start()

def ekran_goruntusu_ocr():
    try:
        screenshot = ImageGrab.grab()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        result = ocr.readtext(frame, detail=0)
        full_sentence = " ".join(result).strip()
        if full_sentence:
            display_text(full_sentence)
    except Exception as e:
        write_log(f"Screen OCR error: {e}")

def display_text(text, is_voice=False):
    original_textbox.delete(1.0, tk.END)
    corrected_textbox.delete(1.0, tk.END)
    translated_textbox.delete(1.0, tk.END)

    original_textbox.insert(tk.END, text)
    corrected = correct_with_gpt(text)
    corrected_textbox.insert(tk.END, corrected)
    translation, target_lang = translate_text(corrected)
    translated_textbox.insert(tk.END, f"[{target_lang}] {translation}")
    speak_text(translation, target_lang)
    if not is_voice:
        stats["ocr"] += 1
        write_log(f"OCR Detected: {text}")
    update_stats()
    status_label.config(text="✅ Completed" if is_voice else "")

def update_camera():
    global camera, last_text, camera_active
    if not camera_active:
        return
    ret, frame = camera.read()
    if ret:
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)

        result = ocr.readtext(frame, detail=0)
        full_sentence = " ".join(result).strip()
        if full_sentence and benzerlik(full_sentence, last_text) < 0.9:
            last_text = full_sentence
            display_text(full_sentence)

    camera_label.after(100, update_camera)

def update_stats():
    stats_label.config(text=f"OCR: {stats['ocr']} | voice: {stats['voice']} | GPT: {stats['gpt']} | Translation: {stats['translation']} | Error: {stats['error']}")

def toggle_kamera():
    global camera_active
    camera_active = not camera_active
    if camera_active:
        update_camera()
        camera_toggle_btn.config(text="⏹️ Stop Camera")
    else:
        camera_toggle_btn.config(text="▶️ Start Camera")

# Arayüz kurulumu
window = tk.Tk()
window.title("AI-Based OCR + Voice Translation")
window.geometry("900x820")

camera_list = get_camera_indexes()
microphone_list = get_microphone_names()

cam_combo = ttk.Combobox(window, values=camera_list, state="readonly")
cam_combo.set(camera_list[0])
cam_combo.pack(pady=5)

mic_combo = ttk.Combobox(window, values=microphone_list, state="readonly")
mic_combo.set(microphone_list[0])
mic_combo.pack(pady=5)

language_codes = {
    "🇹🇷 Türkçe (tr)": "tr",
    "🇬🇧 İngilizce (en)": "en",
    "🇩🇪 Almanca (de)": "de",
    "🇫🇷 Fransızca (fr)": "fr",
    "🇪🇸 İspanyolca (es)": "es",
    "🇮🇹 İtalyanca (it)": "it",
    "🇷🇺 Rusça (ru)": "ru",
    "🇯🇵 Japonca (ja)": "ja",
    "🇰🇷 Korece (ko)": "ko",
    "🇨🇳 Çince (zh-CN)": "zh-CN"
}
lang_code_combo = ttk.Combobox(window, values=list(language_codes.values()), state="readonly")
lang_code_combo.set("en")
lang_code_combo.pack(pady=5)

camera_label = tk.Label(window)
camera_label.pack()

camera_toggle_btn = tk.Button(window, text="⏹️ Stop Camera", command=toggle_kamera)
camera_toggle_btn.pack(pady=5)

status_label = tk.Label(window, text="🎤 Press 'Speak' to start", font=("Arial", 12))
status_label.pack(pady=10)

speak_button = tk.Button(window, text="🎙️ Speak", font=("Arial", 14), command=listen_from_mic)
speak_button.pack(pady=5)

screen_ocr_button = tk.Button(window, text="📸 Screen OCR", command=ekran_goruntusu_ocr)
screen_ocr_button.pack(pady=5)

stats_label = tk.Label(window, text="OCR: 0 | Voice: 0 | GPT: 0 | Translation: 0 | Error: 0", font=("Arial", 10))
stats_label.pack(pady=5)

original_textbox = scrolledtext.ScrolledText(window, height=4)
original_textbox.pack(padx=10, pady=5)

corrected_textbox = scrolledtext.ScrolledText(window, height=4)
corrected_textbox.pack(padx=10, pady=5)

translated_textbox = scrolledtext.ScrolledText(window, height=4)
translated_textbox.pack(padx=10, pady=5)

camera = cv2.VideoCapture(camera_list[0])
update_camera()
window.mainloop()
camera.release()
