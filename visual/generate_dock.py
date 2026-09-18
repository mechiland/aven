#!/usr/bin/env python3
"""Generate a small Plasma style overriding only the panel and task frames.

The stock task manager owns activation, grouping, menus and running state.
No screenshots or upstream SVG graphics are used as generated assets.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'plasma/aven-dock'


def put(name, data):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data.rstrip() + '\n')


def rect(x, y, w, h, fill='none', opacity=1, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" opacity="{opacity}" {extra}/>'


def panel(alpha):
    # A 48px nine-slice with fixed 16px corners; layout margins are independent.
    parts = {'topleft': (0, 0, 16, 16), 'top': (16, 0, 16, 16),
             'topright': (32, 0, 16, 16), 'left': (0, 16, 16, 16),
             'center': (16, 16, 16, 16), 'right': (32, 16, 16, 16),
             'bottomleft': (0, 32, 16, 16), 'bottom': (16, 32, 16, 16),
             'bottomright': (32, 32, 16, 16)}
    corners = {
        'topleft': 'M16 0A16 16 0 0 0 0 16H16Z',
        'topright': 'M32 0A16 16 0 0 1 48 16H32Z',
        'bottomleft': 'M0 32A16 16 0 0 0 16 48V32Z',
        'bottomright': 'M48 32A16 16 0 0 1 32 48V32Z'}
    inner = {'topleft': 'M16 1A15 15 0 0 0 1 16H16Z',
             'topright': 'M32 1A15 15 0 0 1 47 16H32Z',
             'bottomleft': 'M1 32A15 15 0 0 0 16 47V32Z',
             'bottomright': 'M47 32A15 15 0 0 1 32 47V32Z'}
    edges = {'top': (16, 0, 16, 1), 'bottom': (16, 47, 16, 1),
             'left': (0, 16, 1, 16), 'right': (47, 16, 1, 16)}
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">']
    for prefix, color, opacity in [('', '#F8F8F8', alpha), ('mask-', '#000000', 1)]:
        for name, box in parts.items():
            shape = (f'<path d="{corners[name]}" fill="{color}" opacity="{opacity}"/>'
                     if name in corners else rect(*box, color, opacity))
            # Filled border segments keep each slice's exact 16px bounds.
            # Stroke end caps would enlarge bounds and break native slicing.
            border = ''
            if not prefix and name in corners:
                border = f'<path d="{corners[name]}{inner[name]}" fill="#FFFFFF" opacity=".42" fill-rule="evenodd"/>'
            elif not prefix and name in edges:
                border = rect(*edges[name], '#FFFFFF', .42)
            elements.append(f'<g id="{prefix}{name}">{rect(*box, "#000000", 0)}{shape}{border}</g>')
    for side, size in [('top', 4), ('bottom', 4), ('left', 10), ('right', 10)]:
        elements.append(f'<rect id="hint-{side}-margin" width="{size}" height="{size}" fill="none"/>')
    elements.append('<rect id="hint-stretch-borders" width="1" height="1" fill="none"/></svg>')
    return '\n'.join(elements)


def tasks():
    parts = {'topleft': (0, 0, 8, 8), 'top': (8, 0, 36, 8),
             'topright': (44, 0, 8, 8), 'left': (0, 8, 8, 32),
             'center': (8, 8, 36, 32), 'right': (44, 8, 8, 32),
             'bottomleft': (0, 40, 8, 8), 'bottom': (8, 40, 36, 8),
             'bottomright': (44, 40, 8, 8)}
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="52" height="48" viewBox="0 0 52 48">']
    for state in ['normal', 'focus', 'minimized', 'attention', 'hover', 'launcher-hover',
                  'normal-hover', 'focus-hover', 'minimized-hover', 'attention-hover', 'progress']:
        running = state.split('-')[0] in {'normal', 'focus', 'minimized', 'attention'}
        for direction in ['', 'south-']:
            prefix = direction + state
            for name, box in parts.items():
                contents = rect(*box, '#000000', 0)
                if name == 'center' and ('hover' in state):
                    contents += rect(*box, '#000000', .045, 'rx="5"')
                if name == 'bottom' and running:
                    # Native frame stretching only changes this small dot's width
                    # slightly as task spacing changes; never a full-width bar.
                    contents += '<circle cx="26" cy="43" r="1.65" fill="#151515"/>'
                if name == 'bottom' and state == 'progress':
                    contents += rect(8, 46, 36, 2, '#007AFF', .65)
                elements.append(f'<g id="{prefix}-{name}">{contents}</g>')
    for side, size in [('top', 3), ('bottom', 9), ('left', 6), ('right', 6)]:
        elements.append(f'<rect id="normal-hint-{side}-margin" width="{size}" height="{size}" fill="none"/>')
    elements.append('<rect id="hint-stretch-borders" width="1" height="1" fill="none"/></svg>')
    return '\n'.join(elements)


def main():
    put('metadata.json', json.dumps({'KPlugin': {'Id': 'aven-dock', 'Name': 'Aven Dock',
        'Description': 'Translucent panel and quiet native running indicators; other shell assets inherit Breeze.',
        'Version': '0.3.1', 'License': 'MIT', 'Authors': [{'Name': 'Aven contributors'}]},
        'X-Plasma-API': '5.0'}, indent=2))
    put('plasmarc', '[Settings]\nFallbackTheme=default\n\n[AdaptiveTransparency]\nenabled=true\n\n[BlurBehindEffect]\nenabled=true\n\n[ContrastEffect]\nenabled=false')
    put('widgets/panel-background.svg', panel(.54))
    put('translucent/widgets/panel-background.svg', panel(.54))
    put('solid/widgets/panel-background.svg', panel(.92))
    put('opaque/widgets/panel-background.svg', panel(1))
    put('widgets/tasks.svg', tasks())


if __name__ == '__main__':
    main()
