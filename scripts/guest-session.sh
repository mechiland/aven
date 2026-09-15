#!/usr/bin/env bash
# Run a command in the disposable guest's existing Wayland/DBus user session.
set -euo pipefail
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=KDE
export KDE_SESSION_VERSION=6
export QT_QPA_PLATFORM=wayland
export QT_QPA_PLATFORMTHEME=kde
export MOZ_ENABLE_WAYLAND=1
exec "$@"
