#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$root/.cache/pdf-profile" "$root/output/pdf"
google-chrome --headless --disable-gpu --user-data-dir="$root/.cache/pdf-profile" \
  --no-pdf-header-footer --print-to-pdf="$root/output/pdf/weekend-walk.pdf" \
  "file://$root/fixtures/documents/weekend.html"
cp "$root/output/pdf/weekend-walk.pdf" "$root/fixtures/documents/周末散步计划.pdf"
