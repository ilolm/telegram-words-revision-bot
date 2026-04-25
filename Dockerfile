FROM alpine:latest

RUN apk add --no-cache python3 py3-pip && \

    pip3 install aiogram aiosqlite --break-system-packages

COPY ["./bot.py", "/app/"]

RUN adduser -H -D bot && \
    chown -R bot:bot /app

USER bot
ENTRYPOINT ["/usr/bin/python3", "/app/bot.py"]
