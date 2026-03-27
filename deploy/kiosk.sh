#!/bin/bash
# GlanceOS Kiosk Launcher
# Add to /etc/xdg/lxsession/LXDE-pi/autostart or equivalent

# Wait for backend to be ready
sleep 5

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
  http://localhost:5173
