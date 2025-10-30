export MIC_DEVICE_INDEX=1
export AMIXER_CARD=1

export GEMINI_TEMPERATURE=0.4
export GEMINI_MAX_TOKENS=512
export GEMINI_STYLE="Trả lời tiếng Việt, trả lời 2-10 câu; viết thành các câu hoàn chỉnh; không lan man."

#!/bin/bash
cd /home/pi/Downloads/test

# Xóa log cũ
rm -f assistant.log assistant_error.log

echo "Đang cho ket noi mang..."
# Lặp đến khi ping được Google DNS
until ping -c1 8.8.8.8 &>/dev/null; do
    sleep 5
done
echo "Đa co mang, khoi đong tro ly!"

# Ghi log ra file
exec /usr/bin/python3 -u /home/pi/Downloads/test/code_chinh_nam.py \
    >> /home/pi/Downloads/test/assistant.log \
    2>> /home/pi/Downloads/test/assistant_error.log
#file duoc chay ngam o /etc/systemd/system/assistant.service
#exec /usr/bin/python3 -u /home/pi/Downloads/test/main.py \
#    >> /home/pi/Downloads/test/assistant.log \
#    2>> /home/pi/Downloads/test/assistant_error.log