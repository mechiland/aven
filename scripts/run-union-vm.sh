#!/usr/bin/env bash
# Start the local Union prototype with a writable working disk.
set -euo pipefail
aven_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
aven_image="$aven_root/output/Aven-Union-0.2.0-x86_64.qcow2"
aven_state="$aven_root/.cache/vm/union-preview"
test -f "$aven_image" || { echo "Missing $aven_image" >&2; exit 1; }
mkdir -p "$aven_state"
if [[ ! -f "$aven_state/session.qcow2" ]]; then
    qemu-img create -f qcow2 -F qcow2 -b "$aven_image" "$aven_state/session.qcow2"
fi
qemu-system-x86_64 \
    -name 'Aven Union 0.2.0 — Plasma 6.8 Beta' \
    -machine q35,accel=kvm -cpu host -smp 4 -m 6144 \
    -drive "file=$aven_state/session.qcow2,format=qcow2,if=virtio,cache=writeback" \
    -device virtio-vga-gl,xres=1920,yres=1200 \
    -display egl-headless,rendernode=/dev/dri/renderD128 \
    -vnc 127.0.0.1:22 \
    -device qemu-xhci -device usb-tablet -device virtio-rng-pci \
    -audiodev none,id=lab-audio -device ich9-intel-hda -device hda-duplex,audiodev=lab-audio \
    -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2224-:22 -device virtio-net-pci,netdev=net0 \
    -qmp "unix:$aven_state/control.qmp,server=on,wait=off" \
    -pidfile "$aven_state/qemu.pid" -daemonize
echo 'Aven Union: VNC 127.0.0.1:5922; SSH 127.0.0.1:2224; automatic desktop login.'
echo 'Use the desktop shutdown action to stop this VM.'
