FROM alpine
RUN apk add --no-cache su-exec
RUN apk add --no-cache bash
RUN apk add --no-cache curl
RUN apk add --no-cache git
RUN apk add --no-cache xvfb
RUN export DISPLAY=:0.0
RUN Xvfb :0 -screen 0 1280x720x24 > /dev/null 2>&1 &
RUN sleep 1
RUN fluxbox > /dev/null 2>&1 &
