#!/bin/bash
# GlanceOS Kiosk Launcher
# Add to /etc/xdg/lxsession/LXDE-pi/autostart or equivalent

# Wait for backend to be ready
for _ in {1..60}; do
  if curl -fsS http://localhost:8000/api/health >/dev/null; then
    break
  fi
  sleep 1
done

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Launch Chromium in kiosk mode
chromium-browser \
  --kiosk \
  --incognito \
  --disable-infobars \
  --noerrdialogs \
  --disable-translate \
  --disable-features=TranslateUI \
  --check-for-update-interval=31536000 \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  http://localhost:8000
