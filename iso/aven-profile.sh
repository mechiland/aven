# Sourced by Plasma before its applications and shell start.
# This runs with the user's privileges and only on that user's first Aven login.
if [ ! -f "$HOME/.local/state/aven/iso-seed-v1.json" ]; then
    /usr/bin/python3 /var/lib/aven/source/iso/first-login.py seed
fi
