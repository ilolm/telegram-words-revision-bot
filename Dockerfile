FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/* && \

    pip3 install aiogram aiosqlite --break-system-packages

COPY ["./bot.py", "/app/"]

ENTRYPOINT ["/usr/bin/python3", "/app/bot.py"]
