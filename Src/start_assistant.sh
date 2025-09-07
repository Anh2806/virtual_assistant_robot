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
