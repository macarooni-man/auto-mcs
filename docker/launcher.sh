#!/usr/bin/env sh
set -eu

error () {
    { printf '\E[31m'; printf "$@"; printf '\E[0m'; } >&2
    exit 1
}

WEB_PORT="${WEB_PORT:-8080}"
WEB_USERNAME="${WEB_USERNAME:-}"
WEB_PASSWORD="${WEB_PASSWORD:-}"

CRED_EXAMPLE="  - Example: WEB_USERNAME='U\$ern4me' WEB_PASSWORD='P@s\$w0rd'"


# Basic credentials check
if [ -z "$WEB_USERNAME" ] || [ -z "$WEB_PASSWORD" ]; then
  echo "[ERROR] The environment variables 'WEB_USERNAME' and 'WEB_PASSWORD' are required\n\n$CRED_EXAMPLE"
  exit 64
fi

case "${WEB_USERNAME}:${WEB_PASSWORD}" in
  root:auto-mcs|admin:change-me|*:change-me|*:password|admin:admin|*:admin|'':*|*:'')
    error "[ERROR] Default/insecure credentials are not allowed\n\n$CRED_EXAMPLE"
    exit 64
    ;;
esac


# Launch auto-mcs inside TTYD
exec /usr/bin/auto-mcs-ttyd \
  -p "$WEB_PORT" \
  -c "${WEB_USERNAME}:${WEB_PASSWORD}" \
  -W \
  -t disableLeaveAlert=true \
  -t titleFixed="auto-mcs (docker)" \
  -t fontSize=20 \
  -t 'theme={"background":"#1A1A1A"}' \
  tmux -u -2 new -A -s auto-mcs -- sh -lc "/auto-mcs"
