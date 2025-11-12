# AI integrated assistant robot
Support users with fun simple features and questions

## features
- Voice chat
- Answer the questions to participate in AI Gemini
- Integrated audio noise filtering algorithm
- Integrated male and female voice discrimination
1. Model included : Gender_voice_model
- Facial emotions
## Electronic equipment
1. Virtual assistant robot
- Raspberry pi4
- Sound card Hi-Fi WM8960 Waveshare for raspberry pi4
- Raspberry Pi Screen
- Waveshare UPS HAT (B) for Raspberry Pi
- 2 Pin 18650
2. chassis part
- STM32
- H-bridge
- 4 Gear Motors
- 3 Pin 18650
# Mini Interactive Voice Assistant Robot

> Raspberry Pi 4 + WM8960 + 3.5" LCD + voice pipeline (wake word → VAD/DSP → ASR → Gemini → TTS) with a simple “face” UI.

## ✨ Key Features
- Wake word **“Hey Piti”** to auto-enter listening mode.
- Audio capture, band-pass filter, VAD (webrtcvad), and basic noise reduction.
- Vietnamese ASR via Google Speech Recognition.
- NLU/LLM using Google Gemini; non-blocking TTS playback (gTTS).
- Face UI showing states: sleeping / listening / speaking (reads from `cau_tra_loi.txt`) on a 3.5" LCD.
- Local intents that don’t need LLM: time/date queries, ALSA volume control.
- Weather queries for multiple locations (“in … and …”) using Open-Meteo.
- (WIP) Movement commands over UART using keywords “forward/back/left/right”.

## 🧱 Architecture (at a glance)
- `code_chinh_nam.py`: main loop (wake word → capture command → route intent → LLM/TTS/UI/Weather/UART).
- `face_engine_nam.py`: draws and pushes RGB565 frames to `/dev/fb0`.
- `weather.py`: geocoding (Nominatim) + Open-Meteo → short textual summary.
- `UART.py`: open port and send strings with optional ACK.
- `start_assistant.sh`: exports env vars, waits for network + WM8960, runs app, logs to files.

## 🧩 Recommended Hardware
- Raspberry Pi 4 (4GB) with 5V ≥3A power.
- WM8960 Hi-Fi Audio HAT (mic/line + I²S).
- Waveshare 3.5" SPI LCD.
- (Optional) UPS HAT, external speaker.  
> Pinout, BOM, and rationale are described in the report (I²S/I²C/SPI GPIO, tables, and notes).

## Demo
<img width="1920" height="2560" alt="image" src="https://github.com/user-attachments/assets/e432bd1a-79f8-4f20-bef2-233e633a6172" />

<img width="1920" height="2560" alt="image" src="https://github.com/user-attachments/assets/f83c66b7-80e9-43ec-b8dd-a7939536b975" />

<img width="1920" height="2560" alt="image" src="https://github.com/user-attachments/assets/e790f5f8-4589-4c49-8440-70e29190fac6" />

## 📦 Installation
### 1) OS & system packages (Raspberry Pi OS 64-bit recommended)
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev \
  portaudio19-dev ffmpeg mpg123 build-essential swig \
  libatlas-base-dev
# Enable SPI/I2C via raspi-config and apply the WM8960 HAT overlay per the HAT docs.



