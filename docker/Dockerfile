FROM alpine:3.16

RUN apk update && apk upgrade && \
    apk add --no-cache wget unzip ttyd && \
    wget -O auto-mcs.zip "https://URL_GOES_HERE" && \
    unzip auto-mcs.zip && \
    rm -rf auto-mcs.zip && \
    chmod +x auto-mcs
