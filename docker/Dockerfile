FROM alpine:3.20

RUN apk update && apk upgrade && \
    apk add --no-cache wget unzip ttyd openjdk21 openjdk17 openjdk8 && \
    mkdir -p ~/.auto-mcs/Tools/java/ && \
    ln -s /usr/lib/jvm/java-21-openjdk/ ~/.auto-mcs/Tools/java/modern && \
    ln -s /usr/lib/jvm/java-17-openjdk/ ~/.auto-mcs/Tools/java/lts && \
    ln -s /usr/lib/jvm/java-8-openjdk/ ~/.auto-mcs/Tools/java/legacy && \
    wget -O auto-mcs.zip "https://URL_GOES_HERE" && \
    unzip auto-mcs.zip && \
    rm -rf auto-mcs.zip && \
    chmod +x auto-mcs
