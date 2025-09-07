import os
import time
import struct
import threading
from datetime import datetime
from gtts import gTTS
import pygame
import pvporcupine
import pyaudio
import speech_recognition as sr
import google.generativeai as genai
import face_engine_nam
import re

# ========== CẤU HÌNH ========== #
GEMINI_API_KEY = "..."// an KEY
ACCESS_KEY = "==" // an KEY
genai.configure(api_key=GEMINI_API_KEY)

# ========== KHỞI TẠO ========== #
porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=["hey siri"])

pa = pyaudio.PyAudio()
audio_stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length * 2
)

nhan_dien_giong_noi = sr.Recognizer()
micro = sr.Microphone()

# ========== XỬ LÝ GIỌNG NÓI ========== #
def nghe_lenh():
    with micro as source:
        print("Đang lắng nghe lệnh...")
        nhan_dien_giong_noi.adjust_for_ambient_noise(source, duration=1)
        try:
            am_thanh = nhan_dien_giong_noi.listen(source, timeout=10, phrase_time_limit=6)
            lenh = nhan_dien_giong_noi.recognize_google(am_thanh, language="vi-VN")
            print(f"Nhận diện được: {lenh}")
            return lenh.lower()
        except sr.UnknownValueError:
            print("Không nghe rõ lệnh!")
            return None
        except sr.RequestError:
            print("Lỗi kết nối Google Speech Recognition!")
            return None
        except sr.WaitTimeoutError:
            print("Không có lệnh nào.")
            return None

def hoi_gemini(cau_hoi):
    try:
        # Phân tích cảm xúc từ câu hỏi
        if "buồn" in cau_hoi or "khóc" in cau_hoi:
            face_engine_nam.update_face("sad")
        elif "ngại" in cau_hoi or "xấu hổ" in cau_hoi:
            face_engine_nam.update_face("shy")
        elif "vui" in cau_hoi or "hạnh phúc" in cau_hoi:
            face_engine_nam.update_face("happy")
        else:
            face_engine_nam.update_face("thinking")

        # Gọi API Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(cau_hoi)
        if hasattr(response, "text"):
            return response.text
        else:
            return "Xin lỗi, tôi chưa thể trả lời ngay."
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
        return "Xin lỗi, tôi không thể trả lời lúc này."

# ========== CHỈNH ÂM LƯỢNG ========== #
def chinh_am_luong(lenh: str):
    """
    Xử lý lệnh chỉnh âm lượng dựa trên giọng nói.
    - Nếu chứa số từ 0 đến 100 thì set âm lượng tuyệt đối.
    - Nếu vượt ngoài 0-100 thì chỉ log ra, không phát loa.
    """
    match = re.search(r"(\d+)", lenh)
    if match:
        volume = int(match.group(1))
        if 0 <= volume <= 100:
            os.system(f"amixer -c 2 sset Speaker {volume}%")
            noi(f"Đã chỉnh âm lượng ở mức {volume} phần trăm.")
        else:
            print(f"Yêu cầu âm lượng {volume}% không hợp lệ (0-100). Bỏ qua.")
    else:
        noi("Xin hãy nói mức âm lượng mong muốn, ví dụ 30 phần trăm.")

# ========== PHÁT ÂM VÀ BIỂU CẢM ========== #
def noi(text):
    print(f"Trợ lý ảo: {text}")
    tts = gTTS(text=text, lang="vi")
    tts.save("voice.mp3")

    # convert mp3 -> wav 48kHz, stereo, 32bit PCM (chuẩn WM8960)
    os.system("ffmpeg -y -i voice.mp3 -ar 48000 -ac 2 -acodec pcm_s16le voice.wav > /dev/null 2>&1")

    # lấy thời lượng file wav để mô phỏng miệng
    try:
        duration = float(os.popen(
            "ffprobe -i voice.wav -show_entries format=duration -v quiet -of csv=\"p=0\""
        ).read().strip())
    except:
        duration = 2.0

    # phát qua WM8960 (card 2)
    os.system("aplay -D hw:2,0 voice.wav &")

    # nhấp nháy miệng trong khi phát
    open_mouth = False
    start = time.time()
    while time.time() - start < duration:
        face_engine_nam.update_face("speaking", mouth_open=open_mouth)
        open_mouth = not open_mouth
        time.sleep(0.4)

    face_engine_nam.update_face("sleeping")

# ========== CHẠY CHƯƠNG TRÌNH CHÍNH ========== #
print("Trợ lý ảo đang khởi động...")
face_engine_nam.update_face("sleeping")

try:
    while True:
        # CHỜ TỪ KHÓA
        while True:
            am_thanh_pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            am_thanh_pcm = struct.unpack_from("h" * porcupine.frame_length, am_thanh_pcm)

            vi_tri_tu_khoa = porcupine.process(am_thanh_pcm)
            if vi_tri_tu_khoa >= 0:
                print("Phát hiện 'Hey Siri'!")
                face_engine_nam.update_face("listening")
                noi("Tôi đang nghe.")
                break

        # NHẬN LỆNH
        #code cua hoang
        while True:
            lenh = nghe_lenh()
            if lenh:
                if "tạm biệt" in lenh:
                    noi("Tạm biệt, hẹn gặp lại!")
                    raise KeyboardInterrupt

                elif "mấy giờ" in lenh or "thời gian" in lenh:
                    gio = datetime.now().strftime("%H:%M")
                    noi(f"Bây giờ là {gio}")

                elif "ngày" in lenh or "hôm nay" in lenh:
                    ngay = datetime.now().strftime("%d/%m/%Y")
                    noi(f"Hôm nay là ngày {ngay}")

                elif "âm lượng" in lenh:
                    chinh_am_luong(lenh)

                else:
                    face_engine_nam.update_face("thinking")
                    tra_loi = hoi_gemini(lenh)
                    noi(tra_loi)
            else:
                face_engine_nam.update_face("sleeping")
                break

except KeyboardInterrupt:
    print("Dừng trợ lý ảo...")

finally:
    audio_stream.close()
    pa.terminate()
    porcupine.delete()
    print("Đã tắt.")
