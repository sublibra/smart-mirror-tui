#!/bin/bash

export TERM=foot

REPO="$(cd "$(dirname "$0")" && pwd)"
FOOT_INI="${FOOT_INI:-$HOME/.config/foot/foot.ini}"
UV="${UV:-$HOME/.local/bin/uv}"
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

# Rotera
wlr-randr --output HDMI-A-1 --transform 90

# Vänta på att foot stänger
wait $FOOT_PID
