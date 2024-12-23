# 以 Python 3.11 的官方映像檔為基底
FROM python:3.11.11-alpine3.21

# 避免 Python 產生 pyc 檔案，並讓 stdout 不作 buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 建立並切換到 /app 工作目錄
WORKDIR /usr/app

# 如果有需求，可以先複製 requirements.txt 並安裝套件
COPY . .
# 複製 crontab 檔並放到 /etc/crontabs/root (BusyBox 預設會讀這裡)
COPY crontab /etc/crontabs/root

RUN pip install --no-cache-dir -r requirements
RUN apk update && \
    apk add --no-cache \
        bash \
        tzdata \
        busybox-extras \
        # busybox-extras 常常包含了 crond、crontab、ash 等附加功能
        # 或者你可以試試 apk add --no-cache busybox-suid
    && rm -rf /var/cache/apk/*

# 建立一個目錄儲存 cron log
RUN mkdir -p /var/log && touch /var/log/cron.log

# 設定時區 (若有需要)；例如設為台北時間
ENV TZ=Asia/Taipei

# 預設執行 main.py，你可依需求修改檔案名稱
CMD ["crond", "-f"]