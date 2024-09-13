FROM alpine:3.20


ARG ttyd_binary="https://github.com/macarooni-man/auto-mcs-ttyd/releases/download/v1.0.0/auto-mcs-ttyd"

RUN apk update && apk upgrade && \
    apk add --no-cache wget unzip json-c libcrypto3 libssl3 libuv libwebsockets libwebsockets-evlib_uv tmux musl zlib && \
    wget -O auto-mcs.zip "$binary" && \
    unzip auto-mcs.zip && \
    rm -rf auto-mcs.zip && \
    chmod +x auto-mcs && \
    wget -O /usr/bin/auto-mcs-ttyd "$ttyd_binary" && \
    chmod +x /usr/bin/auto-mcs-ttyd
