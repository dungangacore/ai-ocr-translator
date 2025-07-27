# ai-ocr-translator

Real-time AI-powered OCR and voice translation tool with GPT correction and text-to-speech (TTS).  
Supports multiple input sources: **camera**, **microphone**, and **screen capture**.

## Features

- OCR via camera and screen capture
- Voice input and speech-to-text
- Automatic language detection
- GPT-based grammar correction
- Translation to selected language
- Text-to-speech output
- Real-time stats panel

## Installation

```bash
git clone https://github.com/dungangacore/ai-ocr-translator.git
cd ai-ocr-translator
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file from `.env.example` and add your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

```bash
python ai_ocr_translator.py
```

- Choose camera/microphone
- Select language (e.g., "en")
- Press **Speak** for voice translation
- Use **Screen OCR** for screen text
- View original + corrected + translated text live

## License

This project is licensed under the MIT License.

---

Built with 💡 by [@dungangacore](https://github.com/dungangacore)