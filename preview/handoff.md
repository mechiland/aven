# Opening the previewed file

Preview hands the selected local file to Fedora's `/usr/bin/kde-open`, supplied by
the already installed `kde-cli-tools` package. Both **Enter** and **Open** use one
asynchronous `QProcess` path. Its one argument is a fully encoded local-file URL;
no shell parses filenames. KDE resolves the user's default application.

The preview remains open while the helper runs. A successful helper exit closes
it; failure leaves the file visible with a localized retry message. Repeated
activation during the handoff starts no additional helper. Escape cancels the
pending helper. No delay estimates whether an application has launched.

## Why QDesktopServices was insufficient here

On Qt 6.11.2 Wayland, [`QDesktopUnixServices::openDocument`](https://github.com/qt/qtbase/blob/v6.11.2/src/gui/platform/unix/qdesktopunixservices.cpp)
requests an activation token asynchronously and returns `true` before launching
the application. Closing Preview's last window immediately ended the event loop
before that callback ran. Candidate4 reproduced this with both Enter and Open;
Dolphin itself opened the same Chinese-named PDF in Okular successfully.

[`kde-open`](https://github.com/KDE/kde-cli-tools/blob/v6.7.5/kioclient/kioclient.cpp)
owns a native `KIO::OpenUrlJob`, runs its event loop until the job completes, and
returns a nonzero exit status on a job error. Its document path uses
`allowExec=false`. Fedora 44 uses the unversioned executable; `kioclient6` is not
installed.

## Verification

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=preview python3 -m unittest discover \
  -s preview/tests -p 'test_open_handoff.py'
```

These tests run a real child process held until an explicit release signal. They
cover Enter and button activation, delayed success, failure/retry, a missing
helper, duplicate suppression, Escape cancellation, and exact Unicode/percent/
shell-metacharacter filenames. They do not substitute for native Wayland testing.

For release verification, use Preview's Enter and Open button on the Chinese PDF
and an image. Confirm the configured native application opens the correct file,
Preview closes after handoff, and focus reaches the launched application.
