# AI integrated assistant robot

## Motivation & Impact

**Natural, accessible interface.** Voice assistants provide a natural UI for real-world needs across smart homes, teaching assistants in education, and support for older adults and people with disabilities. A small, affordable, and standalone device can expand access to services and lower technical barriers for everyday users.

**Modern stack, balanced design.** Rapid advances in large language models (LLMs) such as Google Gemini enable strong natural-language capabilities: open-ended Q&A, sustained dialogue, summarization, instruction generation, and action orchestration. Combining a cloud LLM with a local pipeline (wake word, VAD, DSP) creates a practical balance of language understanding, latency, and privacy.

**Feasible and cost-effective.** Raspberry Pi 4 is widely available, reasonably priced, and powerful enough for lightweight tasks (wake-word detection, DSP, orchestration) while connecting easily to cloud services for LLM/TTS. The WM8960 audio HAT plus a Waveshare 3.5″ display deliver low-cost audio and a physical interface that integrates cleanly. This makes the project technically and economically feasible for pilot deployments in labs or student teams.

**Research value.** Building a compact voice assistant lets us tackle real-world constraints: optimizing the pipeline to reduce latency, handling environmental noise, balancing on-device vs. cloud processing to preserve privacy, and adding an expressive face engine to improve user experience. The results can contribute to smart IoT applications, home assistants, educational support, and Vietnamese language technology research.


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

<img width="390" height="250" alt="image" src="https://github.com/user-attachments/assets/879f3245-8aec-4f5a-b8dc-11d010cd82f8" />

- WM8960 Hi-Fi Audio HAT (mic/line + I²S).
  
  <img width="246" height="214" alt="image" src="https://github.com/user-attachments/assets/52389699-3c88-4201-93e6-d3028cc4a3ee" />

- Waveshare 3.5" SPI LCD.
  
  <img width="605" height="316" alt="image" src="https://github.com/user-attachments/assets/19ae665e-149a-448e-9d83-7d9e690868d5" />

- (Optional) UPS HAT, external speaker.  
> Pinout, BOM, and rationale are described in the report (I²S/I²C/SPI GPIO, tables, and notes).

## Demo

<img width="1920" height="2560" alt="image" src="https://github.com/user-attachments/assets/46a62266-8292-4c22-810d-6fd8a0ae2eb9" />


<img width="605" height="409" alt="image" src="https://github.com/user-attachments/assets/4b06cff9-67b0-470a-bac4-93b9419e9a7d" />




## 📦 Installation
### 1) OS & system packages (Raspberry Pi OS 64-bit recommended)
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev \
  portaudio19-dev ffmpeg mpg123 build-essential swig \
  libatlas-base-dev
# Enable SPI/I2C via raspi-config and apply the WM8960 HAT overlay per the HAT docs.



