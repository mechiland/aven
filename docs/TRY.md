# Try the focused prototype

## Existing workspace

The Aven laboratory guest is available on **VNC `127.0.0.1:5921`**. Stock is
on `127.0.0.1:5920` while running. Start a stopped guest from the repository:

```sh
python3 scripts/vm.py boot --name aven --gpu
```

The VM logs in automatically as the disposable `aven` user. Open the pinned
Dolphin, Firefox, Thunderbird or Gwenview application from the bottom panel.

- **Files:** `Documents/日常 · Everyday` contains images, Chinese text, a PDF,
  audio and video. Use the native list/grid controls and breadcrumbs.
- **Preview:** select a file in Dolphin and press **Ctrl+Alt+P**. **Esc** returns
  to the same selection. **Enter** opens the mature default application. Video
  opens paused; **Space** starts or pauses it.
- **Browser:** ordinary HTTPS browsing uses Firefox. The local reading/download
  fixture is `http://127.0.0.1:8765/browser/index.html` when its laboratory
  service is running.
- **Mail:** the pinned launcher opens Thunderbird's normal profile for account
  setup. The inspected mailbox is a separate fictional offline fixture; launch
  it with the command below. No mail has been sent by this prototype task.
- **Photos:** open `Pictures/京都春日` in Gwenview for the eight-image album.
  Arrow keys browse neighboring photos; native fullscreen and fit controls work.

Start the optional local browser fixture after a new boot:

```sh
python3 scripts/vm.py ssh --name aven 'systemd-run --user --collect --unit=aven-fixture-http python3 -m http.server 8765 --bind 127.0.0.1 --directory /home/aven/aven/fixtures'
```

Launch the separate offline mailbox from the host:

```sh
python3 scripts/vm.py ssh --name aven 'systemd-run --user --collect --unit=aven-mail-demo env LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8 LANGUAGE=zh_CN bash ~/aven/scripts/guest-session.sh python3 ~/aven/mail/profile.py launch --profile /home/aven/.local/share/aven/mail/aven-demo'
```

In the portable VM, open a terminal and run the guest portion directly:

```sh
LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8 LANGUAGE=zh_CN \
  python3 ~/aven/mail/profile.py launch \
  --profile /home/aven/.local/share/aven/mail/aven-demo
```

The login session is English. Chinese application evidence uses explicit
Simplified or Traditional Chinese launch locales. This prototype does not
redesign the language settings or account-setup flows.

## Portable disk

The final handoff uses `output/aven-prototype-round04.qcow2`, a compressed,
independent QEMU disk exported after clean shutdown. Its checksum and build
identity are recorded in `output/BUILD.json`. Keep that disk as an immutable
base and create a writable test overlay:

```sh
qemu-img create -f qcow2 -F qcow2 \
  -b "$(realpath output/aven-prototype-round04.qcow2)" output/aven-try.qcow2
```

On an x86_64 Linux host with KVM and a working render node, the following matches
the graphics path used for screenshots. Port 5931 keeps it separate from the
existing laboratory guests:

```sh
qemu-system-x86_64 \
  -name 'Aven prototype' -machine q35,accel=kvm -cpu host -smp 4 -m 6144 \
  -drive file=output/aven-try.qcow2,format=qcow2,if=virtio \
  -device virtio-vga-gl,xres=1920,yres=1200 \
  -display egl-headless,rendernode=/dev/dri/renderD128 -vnc 127.0.0.1:31 \
  -device qemu-xhci -device usb-tablet \
  -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
  -audiodev none,id=lab-audio -device ich9-intel-hda \
  -device hda-duplex,audiodev=lab-audio -device virtio-rng-pci
```

Connect a VNC viewer to `127.0.0.1:5931`. For hosts without a usable render node,
replace `virtio-vga-gl` with `virtio-vga` and the `-display` value with `none`;
that software-rendered path was not used for the final visual assessment.

This is a laboratory prototype, with automatic login, a locked password,
passwordless sudo and a lab SSH public key. The portable command exposes only
loopback VNC, and forwards no SSH port. The disk contains no private VM SSH key.
Audio is silent in the harness. See [BUILD.md](BUILD.md) for Atomic deployment,
rollback and motion-measurement limits, and [restore.md](restore.md) for
preference restoration.
