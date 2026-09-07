#!/bin/bash

export TERM=foot

REPO="$(cd "$(dirname "$0")" && pwd)"
FOOT_INI="${FOOT_INI:-$HOME/.config/foot/foot.ini}"
UV="${UV:-$HOME/.local/bin/uv}"
OUTPUT="${MIRROR_OUTPUT:-HDMI-A-1}"
TRANSFORM="${MIRROR_TRANSFORM:-90}"
ON_HOUR="${MIRROR_ON_HOUR:-6}"
if [ ! -x "$UV" ]; then
    UV="$(command -v uv)"
fi

# Starta terminalen i bakgrunden
# --frozen/--no-dev: do not install textual-dev (msgpack) on the Pi
foot -c "$FOOT_INI" "$UV" --directory "$REPO" run --frozen --no-dev python -m smart_mirror &
FOOT_PID=$!

# Vänta tills Wayland-socketen faktiskt finns (max 10 sekunder)
# Cage sätter automatiskt WAYLAND_DISPLAY (oftast wayland-0)
for i in {1..20}; do
    if [ -e "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then
        break
    fi
    sleep 0.5
done

# Ge det en extra sekund för säkerhets skull
sleep 1

# Desired display state: off from 00:00 until ON_HOUR (default 06:00).
# Re-apply rotation when turning the output back on. Only call wlr-randr when
# the desired state changes, so a 30s poll does not flicker the panel.
apply_display_schedule() {
    local last_state=""
    local hour desired
    while true; do
        hour=$((10#$(date +%H)))
        if [ "$hour" -lt "$ON_HOUR" ]; then
            desired=off
        else
            desired=on
        fi
        if [ "$desired" != "$last_state" ]; then
            if [ "$desired" = off ]; then
                wlr-randr --output "$OUTPUT" --off && last_state=$desired
            else
                wlr-randr --output "$OUTPUT" --on --transform "$TRANSFORM" && last_state=$desired
            fi
        fi
        sleep 60
    done
}

apply_display_schedule &
DISPLAY_LOOP_PID=$!
trap 'kill "$DISPLAY_LOOP_PID" 2>/dev/null || true' EXIT

# Vänta på att foot stänger
wait $FOOT_PID
