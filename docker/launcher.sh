#!/usr/bin/env sh
set -eu

WEB_PORT="${WEB_PORT:-8080}"
WEB_USERNAME="${WEB_USERNAME:-}"
WEB_PASSWORD="${WEB_PASSWORD:-}"


# Basic credentials check
if [ -z "$WEB_USERNAME" ] || [ -z "$WEB_PASSWORD" ]; then
  echo "ERROR: 'WEB_USERNAME' and 'WEB_PASSWORD' are required." >&2
  exit 64
fi

case "${WEB_USERNAME}:${WEB_PASSWORD}" in
  root:auto-mcs|admin:change-me|*:change-me|*:password|admin:admin|*:admin|'':*|*:'')
    echo "ERROR: Default/insecure credentials are not allowed." >&2
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
