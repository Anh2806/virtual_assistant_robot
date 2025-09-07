# face_engine.py
import numpy as np
from PIL import Image, ImageDraw
import time

WIDTH, HEIGHT = 480, 320

BLUE = (0, 200, 255)  # pastel xanh duong cute
BLACK = (20, 20, 20)
BG = (15, 15, 15)

def draw_face(state="sleeping", mouth_open=False):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Mặt oval (màn hình robot)
    draw.ellipse((60, 40, 420, 280), fill=BLACK)

    # Mắt
    left_eye = (160, 130)
    right_eye = (300, 130)

    def draw_eye(pos, style="dot"):
        if style == "dot":
            draw.ellipse((pos[0]-10, pos[1]-10, pos[0]+10, pos[1]+10), fill=BLUE)
        elif style == "arc":
            draw.arc((pos[0]-20, pos[1]-10, pos[0]+20, pos[1]+20), start=0, end=180, fill=BLUE, width=4)
        elif style == "heart":
            draw.ellipse((pos[0]-6, pos[1]-8, pos[0], pos[1]-2), fill=BLUE)
            draw.ellipse((pos[0], pos[1]-8, pos[0]+6, pos[1]-2), fill=BLUE)
            draw.polygon([(pos[0]-6, pos[1]-4), (pos[0]+6, pos[1]-4), (pos[0], pos[1]+8)], fill=BLUE)

    # Mắt theo trạng thái
    if state == "neutral":
        draw_eye(left_eye, "dot")
        draw_eye(right_eye, "dot")
    elif state == "sad":
        draw.arc((left_eye[0]-15, left_eye[1]-5, left_eye[0]+15, left_eye[1]+15), start=180, end=360, fill=BLUE, width=3)
        draw.arc((right_eye[0]-15, right_eye[1]-5, right_eye[0]+15, right_eye[1]+15), start=180, end=360, fill=BLUE, width=3)
    elif state == "shy":
        draw_eye((left_eye[0]-5, left_eye[1]+5), "dot")
        draw_eye((right_eye[0]+5, right_eye[1]+5), "dot")
        draw.ellipse((140, 180, 180, 200), fill=(255, 100, 100))  # Má hồng trái
        draw.ellipse((280, 180, 320, 200), fill=(255, 100, 100))  # Má hồng phải
    elif state == "angry":
        draw.line((left_eye[0]-15, left_eye[1]-10, left_eye[0]+5, left_eye[1]+5), fill=BLUE, width=3)
        draw.line((right_eye[0]-5, right_eye[1]+5, right_eye[0]+15, right_eye[1]-10), fill=BLUE, width=3)
    elif state == "happy":
        draw.arc((left_eye[0]-15, left_eye[1]-10, left_eye[0]+15, left_eye[1]+10), start=180, end=360, fill=BLUE, width=3)
        draw.arc((right_eye[0]-15, right_eye[1]-10, right_eye[0]+15, right_eye[1]+10), start=180, end=360, fill=BLUE, width=3)
    elif state == "sleeping":
        draw.arc((left_eye[0]-15, left_eye[1]-5, left_eye[0]+15, left_eye[1]+15), start=0, end=180, fill=BLUE, width=3)
        draw.arc((right_eye[0]-15, right_eye[1]-5, right_eye[0]+15, right_eye[1]+15), start=0, end=180, fill=BLUE, width=3)
    elif state == "thinking":
        draw_eye((left_eye[0]-5, left_eye[1]-5), "dot")
        draw_eye((right_eye[0]+5, right_eye[1]-5), "dot")
    elif state == "speaking":
        draw_eye(left_eye, "dot")
        draw_eye(right_eye, "dot")
    elif state == "listening":
        draw_eye(left_eye, "arc")
        draw_eye(right_eye, "arc")

    # Miệng theo trạng thái
    if state == "neutral":
        draw.rectangle((230, 230, 250, 235), fill=BLUE)
    elif state == "sad":
        draw.arc((200, 240, 280, 260), start=0, end=180, fill=BLUE, width=2)
    elif state == "shy":
        draw.arc((200, 240, 280, 260), start=180, end=360, fill=BLUE, width=2)
    elif state == "angry":
        draw.line((220, 240, 260, 240), fill=BLUE, width=3)
    elif state == "happy":
        draw.arc((200, 220, 280, 240), start=180, end=360, fill=BLUE, width=2)
    elif state == "thinking":
        draw.arc((200, 220, 280, 240), start=180, end=360, fill=BLUE, width=2)
    elif state == "listening":
        draw.rectangle((230, 225, 250, 228), fill=BLUE)
    elif state == "speaking":
        if mouth_open:
            draw.ellipse((220, 220, 260, 245), fill=BLUE)
        else:
            draw.rectangle((230, 230, 250, 235), fill=BLUE)

    return image
def convert_to_rgb565(image):
    img_array = np.array(image)
    r = (img_array[:, :, 0] >> 3).astype(np.uint16)
    g = (img_array[:, :, 1] >> 2).astype(np.uint16)
    b = (img_array[:, :, 2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    return rgb565.astype(np.uint16).tobytes()

def update_face(state="sleeping", mouth_open=False):
    img = draw_face(state, mouth_open)
    img_rgb565 = convert_to_rgb565(img)
    with open("/dev/fb0", "wb") as f:
        f.write(img_rgb565)
