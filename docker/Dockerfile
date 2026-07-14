FROM alpine:3.23

ARG TARGETARCH

ARG ttyd_binary="https://github.com/macarooni-man/auto-mcs-ttyd/releases/download/v1.0.0/auto-mcs-ttyd-${TARGETARCH}"

COPY auto-mcs-${TARGETARCH} /auto-mcs

RUN apk upgrade --no-cache && \
    apk add --no-cache \
        ca-certificates \
        json-c \
        libcrypto3 \
        libssl3 \
        libuv \
        libwebsockets \
        libwebsockets-evlib_uv \
        tmux \
        musl \
        zlib \
        libstdc++ && \
    apk add --no-cache --virtual .download-deps wget && \
    echo "set -g status off" > ~/.tmux.conf && \
    chmod +x /auto-mcs && \
    wget -O /usr/bin/auto-mcs-ttyd "$ttyd_binary" && \
    chmod +x /usr/bin/auto-mcs-ttyd && \
    apk del .download-deps

COPY launcher.sh /usr/local/bin/launcher.sh
RUN chmod +x /usr/local/bin/launcher.sh


# Initialize default values
VOLUME ["/root/.auto-mcs"]
EXPOSE 8080 7001 25565

ENV WEB_PORT=8080 \
    WEB_USERNAME=root \
    WEB_PASSWORD=auto-mcs

CMD ["/usr/local/bin/launcher.sh"]
