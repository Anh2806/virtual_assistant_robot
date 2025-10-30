# ----- Imports (chỉ import genai 1 lần ở đầu) -----
import os, time, struct, threading, queue, subprocess, logging, re, shutil
from datetime import datetime
from gtts import gTTS
from io import BytesIO
import pyaudio
import pvporcupine
import speech_recognition as sr
import google.generativeai as genai
#import pyttsx3

import numpy as np
from scipy import signal
import webrtcvad
import noisereduce as nr

import face_engine_nam
# import wave  # KHÔNG còn dùng

# ================== CẤU HÌNH & LOGGING ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

GEMINI_API_KEY = "AIzaSyBzyyyEvxfNc0yJdluD4Xiq1rK6se6Pt5I"
ACCESS_KEY = "3u9Ohx7VmPxzrVbY301m4kAxdsFG8qP1yN7t/PGRqjn13BJ0pCUOBg=="
MIC_DEVICE_INDEX = os.getenv("MIC_DEVICE_INDEX")  # None hoặc chuỗi số
AMIXER_CARD      = int(os.getenv("AMIXER_CARD", "1"))  # card cho amixer, mặc định 1
OUTPUT_DIR       =  "/home/pi/Downloads/test"
DEBUG_SAVE_MP3   = True  # đặt False nếu không muốn lưu file

# Cấu hình SDK Gemini (KHÔNG import lại)
genai.configure(api_key=GEMINI_API_KEY)
# Tạo model 1 lần (reuse)
GEN_MODEL = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=os.getenv(
        "GEMINI_STYLE",
        "Bạn là trợ lý tiếng Việt. Luôn trả lời ngắn gọn tối đa 2-10 câu."
    )
)

GEN_CFG = {
    "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.4")),
    "max_output_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "2048")),
    "response_mime_type": "text/plain",
}

# ================== TIỆN ÍCH: PCM -> MP3 ==================
def pcm16le_to_mp3(pcm_bytes: bytes, sr: int, mp3_path: str, mono: bool = True, bitrate_kbps: int = 64) -> bool:
    """
    Ghi PCM 16-bit (little-endian) thành MP3 bằng ffmpeg (ưu tiên) hoặc lame (dự phòng).
    """
    os.makedirs(os.path.dirname(mp3_path), exist_ok=True)

    if shutil.which("ffmpeg"):
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "s16le", "-ac", "1" if mono else "2", "-ar", str(sr),
            "-i", "-", "-vn", "-acodec", "libmp3lame", "-b:a", f"{bitrate_kbps}k",
            mp3_path
        ]
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            p.communicate(pcm_bytes)
            ok = (p.returncode == 0)
            logging.info("PCM->MP3 (ffmpeg): %s -> %s [%s]", len(pcm_bytes), mp3_path, "OK" if ok else "FAIL")
            return ok
        except Exception as e:
            logging.error("ffmpeg error: %s", e)

    if shutil.which("lame"):
        # -r: raw input, --little-endian mặc định; -s <kHz>; -m m: mono
        cmd = ["lame", "-r", "-s", str(sr/1000), "-b", str(bitrate_kbps)]
        if mono: cmd += ["-m", "m"]
        cmd += ["-", mp3_path]
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            p.communicate(pcm_bytes)
            ok = (p.returncode == 0)
            logging.info("PCM->MP3 (lame): %s -> %s [%s]", len(pcm_bytes), mp3_path, "OK" if ok else "FAIL")
            return ok
        except Exception as e:
            logging.error("lame error: %s", e)

    logging.error("Không tìm thấy ffmpeg/lame để ghi MP3.")
    return False

# ================== GEMINI ==================
def hoi_gemini(cau_hoi: str) -> str:
    def _extract_text(resp) -> str:
        try:
            t = getattr(resp, "text", None)
            if t: return t.strip()
        except Exception: pass
        out = []
        try:
            for c in getattr(resp, "candidates", []) or []:
                content = getattr(c, "content", None)
                parts = getattr(content, "parts", []) if content else []
                for p in parts:
                    t = getattr(p, "text", None)
                    if t is None and isinstance(p, dict): t = p.get("text")
                    if t: out.append(str(t))
        except Exception: pass
        return "\n".join(out).strip()

    def _is_blocked(resp) -> tuple[bool, str]:
        try:
            fb = getattr(resp, "prompt_feedback", None)
            if fb and getattr(fb, "block_reason", None):
                return True, f"prompt_feedback:{fb.block_reason}"
        except Exception: pass
        try:
            for c in getattr(resp, "candidates", []) or []:
                fr = (getattr(c, "finish_reason", None) or "").upper()
                if fr in {"SAFETY", "BLOCKED", "OTHER"}:
                    return True, f"candidate_finish:{fr}"
        except Exception: pass
        return False, ""

    try:
        if not GEN_MODEL:
            return "Chưa cấu hình GEMINI_API_KEY."

        s = (cau_hoi or "").lower()
        if any(k in s for k in ["buồn", "khóc"]):
            face_engine_nam.update_face("sad")
        elif any(k in s for k in ["ngại", "xấu hổ"]):
            face_engine_nam.update_face("shy")
        elif any(k in s for k in ["vui", "hạnh phúc"]):
            face_engine_nam.update_face("happy")
        else:
            face_engine_nam.update_face("thinking")

        rang_buoc = "\n\nYÊU CẦU: trả lời tiếng Việt, súc tích, 2–10 câu, không lan man, KHÔNG bullet, câu hoàn chỉnh."
        cfg = dict(GEN_CFG); cfg.setdefault("candidate_count", 1)

        t0 = time.time()
        try:
            resp = GEN_MODEL.generate_content(cau_hoi + rang_buoc, generation_config=cfg)
        except Exception as e:
            logging.warning("Gemini call error, retrying once: %s", e)
            time.sleep(0.2)
            resp = GEN_MODEL.generate_content(cau_hoi + rang_buoc, generation_config=cfg)

        blocked, reason = _is_blocked(resp)
        if blocked:
            logging.warning("Gemini blocked: %s", reason)
            if any(k in s for k in ["đau đầu", "bị đau", "sức khỏe", "triệu chứng"]):
                return ("Mình không thể tư vấn y tế cá nhân. Nếu đau đầu kéo dài, nặng lên, "
                        "kèm sốt/cứng gáy/nôn/mờ mắt hoặc sau chấn thương, hãy liên hệ cơ sở y tế.")
            return "Xin lỗi, tôi không thể trả lời câu này."

        ans = _extract_text(resp)
        if not ans:
            logging.warning("Gemini trả về rỗng: %s", getattr(resp, "candidates", None))
            return "Xin lỗi, tôi chưa có câu trả lời phù hợp."

        # rút gọn tối đa 10 câu
        ans = " ".join(re.split(r'(?<=[.!?…])\s+', ans)[:10]).strip()
        logging.info("Gemini latency: %.0f ms", (time.time() - t0) * 1000)
        return ans

    except Exception:
        logging.exception("Gemini error")
        return "Xin lỗi, tôi không thể trả lời lúc này."

# ================== PORCUPINE & AUDIO IN ==================
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keywords=["hey siri"]  # lưu ý: keyword này có thể không tồn tại trong bộ built-in
)

pa = pyaudio.PyAudio()
audio_stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length,
    input_device_index=int(MIC_DEVICE_INDEX) if MIC_DEVICE_INDEX else None
)

def wait_for_wake():
    logging.info("Đang chờ từ khóa 'Hey Siri'...")
    face_engine_nam.update_face("sleeping")
    while True:
        raw = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, raw)
        if porcupine.process(pcm) >= 0:
            logging.info("Phát hiện 'Hey Siri'!")
            return
# ================== DSP & VAD CONFIG ==================
SAMPLE_RATE = porcupine.sample_rate  # dùng cùng SR
_bp_sos = signal.butter(4, [100/(SAMPLE_RATE/2), min(8000/(SAMPLE_RATE/2), 0.99)],
                        btype='band', output='sos')
_bp_zi = signal.sosfilt_zi(_bp_sos)

def bp_filter_bytes(raw_bytes: bytes) -> bytes:
    """Band-pass streaming (giữ trạng thái) cho PCM16 mono."""
    global _bp_zi
    arr = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)
    filtered, _bp_zi = signal.sosfilt(_bp_sos, arr, zi=_bp_zi)
    return np.clip(filtered, -32768, 32767).astype(np.int16).tobytes()

vad = webrtcvad.Vad(2)  # 0..3 (3 nhạy nhất)
FRAME_MS = 20
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
FRAME_BYTES = FRAME_SAMPLES * 2  # 2 bytes/mẫu (int16)

def is_voice_frame(frame_bytes: bytes) -> bool:
    if len(frame_bytes) != FRAME_BYTES:
        return False
    try:
        return vad.is_speech(frame_bytes, SAMPLE_RATE)
    except Exception:
        return False

# ================== ASR (SpeechRecognition) ==================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.6
recognizer.non_speaking_duration = 0.3
recognizer.phrase_threshold = 0.1

def nghe_lenh() -> str | None:
    """
    Thu 1 câu lệnh từ audio_stream, cắt câu bằng VAD, xuất debug MP3 (nếu bật).
    """
    logging.info("Đang lắng nghe lệnh (1-stream)...")

    # tránh dính âm wake-word/TTS
    pre_roll_ms = 500
    drop_frames = int(pre_roll_ms / FRAME_MS)
    for _ in range(drop_frames):
        audio_stream.read(FRAME_SAMPLES, exception_on_overflow=False)

    frames = []
    voiced = 0
    silence_run = 0
    total_frames = 0

    max_sec = 8
    max_frames = int((max_sec * 1000) // FRAME_MS)
    end_silence_ms = 500

    while total_frames < max_frames:
        f = audio_stream.read(FRAME_SAMPLES, exception_on_overflow=False)
        total_frames += 1

        if is_voice_frame(f):
            frames.append(f)
            voiced += 1
            silence_run = 0
        else:
            if voiced == 0:
                continue
            frames.append(f)
            silence_run += 1
            if silence_run * FRAME_MS >= end_silence_ms:
                break

    if voiced < 1:
        logging.info("VAD: Không có giọng nói đủ rõ.")
        return None

    raw = b"".join(frames)  # PCM16LE

    # (Tuỳ chọn) Lưu RAW -> MP3
    if DEBUG_SAVE_MP3:
        raw_mp3 = os.path.join(OUTPUT_DIR, "raw.mp3")
        if pcm16le_to_mp3(raw, SAMPLE_RATE, raw_mp3): logging.info("Đã lưu %s", raw_mp3)

    # Band-pass + noisereduce (nếu đủ dài)
    bp_bytes = bp_filter_bytes(raw)
    arr = np.frombuffer(bp_bytes, dtype=np.int16).astype(np.float32)
    try:
        if voiced >= 5:
            arr = nr.reduce_noise(audio_clip=arr, sr=SAMPLE_RATE)
    except Exception:
        pass
    cleaned = np.clip(arr, -32768, 32767).astype(np.int16).tobytes()

    # (Tuỳ chọn) Lưu CLEAN -> MP3
    if DEBUG_SAVE_MP3:
        clean_mp3 = os.path.join(OUTPUT_DIR, "clean.mp3")
        if pcm16le_to_mp3(cleaned, SAMPLE_RATE, clean_mp3): logging.info("Đã lưu %s", clean_mp3)

    # Nhận dạng
    audio_data = sr.AudioData(cleaned, SAMPLE_RATE, sample_width=2)
    try:
        t0 = time.time()
        text = recognizer.recognize_google(audio_data, language="vi-VN")
        logging.info("ASR latency: %.0f ms", (time.time() - t0) * 1000)
        logging.info("ASR: %s", text)
        return text.lower()
    except sr.UnknownValueError:
        logging.info("Không nghe rõ lệnh!")
        return None
    except sr.RequestError:
        logging.error("Lỗi kết nối Google Speech Recognition!")
        return None
    except Exception as e:
        logging.error("ASR error: %s", e)
        return None

# ================== NON-BLOCKING TTS ==================
tts_queue: "queue.Queue[str | None]" = queue.Queue()

def _strip_markdown_bullets(text: str) -> str:
    lines = []
    for ln in (text or "").splitlines():
        ln = re.sub(r'^\s*(?:[\*\-\+]|•|\d+[\.)])\s+', '', ln).strip()
        if ln: lines.append(ln)
    return re.sub(r'\s{2,}', ' ', " ".join(lines)).strip()

def _chunk_sentences(text: str, max_len: int = 220):
    sents = re.split(r'(?<=[.!?…])\s+', (text or "").strip())
    chunks, cur = [], ""
    for s in sents:
        if not s: continue
        if len(cur) + (1 if cur else 0) + len(s) <= max_len:
            cur = (cur + " " + s).strip()
        else:
            if cur: chunks.append(cur)
            cur = s
    if cur: chunks.append(cur)
    return chunks or [text]

def mouth_animation(stop_event: threading.Event, period: float = 0.35):
    open_mouth = False
    while not stop_event.is_set():
        face_engine_nam.update_face("speaking", mouth_open=open_mouth)
        open_mouth = not open_mouth
        time.sleep(period)
    face_engine_nam.update_face("sleeping")

def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        if not text:
            continue

        # Làm sạch ký hiệu để TTS đọc tự nhiên
        text = _strip_markdown_bullets(text)
        logging.info("TTS (gTTS): %s", text)

        try:
            for chunk in _chunk_sentences(text):
                mp3_buf = BytesIO()
                gTTS(text=chunk, lang=os.getenv("TTS_LANG", "vi"), slow=False).write_to_fp(mp3_buf)
                # Phát MP3 trực tiếp qua stdin (không lưu file)
                p = subprocess.Popen(["mpg123", "-q", "-"], stdin=subprocess.PIPE)
                p.communicate(mp3_buf.getvalue())
        except Exception as e:
            logging.error("gTTS lỗi: %s", e)

tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

def noi(text: str):
    """Đưa câu nói vào hàng đợi (non-blocking)."""
    print(f"Trợ lý ảo: {text}")
    tts_queue.put(text)

# ================== ÂM LƯỢNG AN TOÀN ==================
def chinh_am_luong(lenh: str):
    m = re.search(r"(\d+)", lenh or "")
    if not m:
        noi("Xin hãy nói mức âm lượng mong muốn, ví dụ 30 phần trăm.")
        return
    vol = int(m.group(1))
    if not (0 <= vol <= 100):
        logging.warning("Âm lượng yêu cầu %d%% không hợp lệ", vol)
        return
    try:
        subprocess.run(['amixer', '-c', str(AMIXER_CARD), 'sset', 'Speaker', f'{vol}%'], check=False)
        noi(f"Đã chỉnh âm lượng ở mức {vol} phần trăm.")
    except Exception as e:
        logging.error("Lỗi chỉnh âm lượng: %s", e)

# ================== CHƯƠNG TRÌNH CHÍNH ==================
def main():
    print("Trợ lý ảo đang khởi động...")
    face_engine_nam.update_face("sleeping")
    try:
        while True:
            # --- CHỜ TỪ KHÓA ---
            """while True:
                raw = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, raw)
                hit = porcupine.process(pcm)
                if hit >= 0:
                    print("Phát hiện 'Hey Siri'!")
                    face_engine_nam.update_face("listening")
                    noi("Tôi đang nghe.")
                    break """

            # --- NHẬN LỆNH ---
            while True:
                wait_for_wake()
                face_engine_nam.update_face("listening")
                noi("Tôi đang nghe")
                def drain_tts(timeout=0.1):
                    t0 = time.time()
                    while not tts_queue.empty() and (time.time() - t0) < timeout:
                        time.sleep(0.05)
                drain_tts(2.0)
                cmd = nghe_lenh()
                if not cmd:
                    face_engine_nam.update_face("sleeping")
                    continue

                if "tạm biệt" in cmd:
                    noi("Tạm biệt, hẹn gặp lại!")
                    raise KeyboardInterrupt

                elif ("mấy giờ" in cmd) or ("thời gian" in cmd):
                    gio = datetime.now().strftime("%H:%M")
                    noi(f"Bây giờ là {gio}")

                elif ("ngày" in cmd) or ("hôm nay" in cmd):
                    ngay = datetime.now().strftime("%d/%m/%Y")
                    noi(f"Hôm nay là ngày {ngay}")

                elif "âm lượng" in cmd:
                    chinh_am_luong(cmd)

                else:
                    face_engine_nam.update_face("thinking")
                    reply = hoi_gemini(cmd)
                    noi(reply)

    except KeyboardInterrupt:
        print("Dừng trợ lý ảo...")
    finally:
        try:
            audio_stream.close()
            pa.terminate()
            porcupine.delete()
        except Exception:
            pass
        tts_queue.put(None)
        print("Đã tắt.")

if __name__ == "__main__":
    main()
