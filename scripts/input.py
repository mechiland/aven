#!/usr/bin/env python3
"""Explicit native guest input for witnessed UI checks; logs every action."""
import argparse
import datetime
import json
import shlex
import subprocess
import time
from vm import qmp, ROOT, VM


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--guest', choices=['stock', 'aven'], default='stock')
    p.add_argument('--width', type=int, default=1920)
    p.add_argument('--height', type=int, default=1200)
    s = p.add_subparsers(dest='action', required=True)
    k = s.add_parser('key'); k.add_argument('keys')
    c = s.add_parser('click'); c.add_argument('x', type=int); c.add_argument('y', type=int)
    c.add_argument('--button', choices=['left', 'right'], default='left')
    c.add_argument('--double', action='store_true')
    t = s.add_parser('paste'); t.add_argument('text')
    a = p.parse_args()
    def key(keys):
        qmp(a.guest, 'human-monitor-command', {'command-line':'sendkey '+keys})
    if a.action == 'key':
        key(a.keys)
    elif a.action == 'paste':
        command = shlex.join(['qdbus-qt6','org.kde.klipper','/klipper',
                             'org.kde.klipper.klipper.setClipboardContents',a.text])
        subprocess.run(['ssh','-i',str(VM/'id_ed25519'),'-p','2222' if a.guest=='stock' else '2223',
                        '-o','BatchMode=yes','-o',f'UserKnownHostsFile={VM/"known_hosts"}',
                        'aven@127.0.0.1',command],check=True)
        key('ctrl-v')
    else:
        if not (0 <= a.x < a.width and 0 <= a.y < a.height):
            p.error('Click must lie inside the observed framebuffer')
        events = [{'type':'abs','data':{'axis':axis,'value':round(value/(size-1)*32767)}}
                  for axis,value,size in [('x',a.x,a.width),('y',a.y,a.height)]]
        qmp(a.guest,'input-send-event',{'events':events})
        time.sleep(.12)
        for _ in range(2 if a.double else 1):
            qmp(a.guest,'input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':a.button}}]})
            time.sleep(.09)
            qmp(a.guest,'input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':a.button}}]})
            time.sleep(.1)
    record = vars(a) | {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'method':'QEMU native input; clipboard text pasted through the active application' if a.action=='paste' else 'QEMU native input'}
    folder = ROOT/'evidence'/'interaction'; folder.mkdir(parents=True,exist_ok=True)
    with (folder/f'{a.guest}.jsonl').open('a') as f:
        f.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(json.dumps(record,ensure_ascii=False))
    time.sleep(.7)


if __name__ == '__main__': main()
