#!/bin/bash

export TERM=foot 

# Starta terminalen i bakgrunden
foot -c /home/pi/.config/foot/foot.ini /home/pi/smart-mirror-tui/.venv/bin/python /home/pi/smart-mirror-tui/smart_mirror/core/app.py &
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
