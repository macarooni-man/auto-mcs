FROM alpine:3.20


ARG ttyd_binary="https://github.com/macarooni-man/auto-mcs-ttyd/releases/download/v1.0.0/auto-mcs-ttyd"

RUN apk update && apk upgrade && \
    apk add --no-cache wget json-c libcrypto3 libssl3 libuv libwebsockets libwebsockets-evlib_uv tmux musl zlib && \
    echo "set -g status off" > ~/.tmux.conf && \
    chmod +x auto-mcs && \
    wget -O /usr/bin/auto-mcs-ttyd "$ttyd_binary" && \
    chmod +x /usr/bin/auto-mcs-ttyd
