#!/usr/bin/env sh
set -eu

WEB_PORT="${WEB_PORT:-8080}"
WEB_USERNAME="${WEB_USERNAME:-}"
WEB_PASSWORD="${WEB_PASSWORD:-}"
DISABLE_AUTH="${DISABLE_AUTH:-false}"

CRED_EXAMPLE="  - To configure the environment variable credentials:\n    - WEB_USERNAME='U\$ern4me'\n    - WEB_PASSWORD='P@s\$w0rd'"

if [ "$DISABLE_AUTH" = "true" ]; then
  AUTH_ARGS=""
else
  if [ -z "$WEB_USERNAME" ] || [ -z "$WEB_PASSWORD" ]; then
    printf "[ERROR] The environment variables 'WEB_USERNAME' and 'WEB_PASSWORD' are required\n\n$CRED_EXAMPLE"
    exit 64
  fi

  case "${WEB_USERNAME}:${WEB_PASSWORD}" in
    root:auto-mcs|admin:change-me|*:change-me|*:password|admin:admin|*:admin|'':*|*:'')
      printf "[ERROR] Default/insecure credentials are not allowed\n\n$CRED_EXAMPLE"
      exit 64
      ;;
  esac

  AUTH_ARGS="-c ${WEB_USERNAME}:${WEB_PASSWORD}"
fi

exec /usr/bin/auto-mcs-ttyd \
  -p "$WEB_PORT" \
  $AUTH_ARGS \
  -W \
  -t disableLeaveAlert=true \
  -t titleFixed="auto-mcs (docker)" \
  -t fontSize=20 \
  -t 'theme={"background":"#1A1A1A"}' \
  tmux -u -2 new -A -s auto-mcs -- sh -lc "/auto-mcs"
