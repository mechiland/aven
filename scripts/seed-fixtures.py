#!/usr/bin/env python3
"""Seed the same synthetic daily files into a disposable stock/Aven guest home."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import wave

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home', type=Path, default=Path.home())
    a=p.parse_args()
    target=a.home/'Documents'/'日常 · Everyday'
    target.mkdir(parents=True, exist_ok=True)
    for folder in ['Downloads','Pictures','Documents','Music','Videos']:
        (a.home/folder).mkdir(exist_ok=True, parents=True)
    for source in (ROOT/'fixtures/typography').glob('*.txt'):
        shutil.copy2(source,target/source.name)
    for source in (ROOT/'fixtures/documents').glob('*.pdf'):
        shutil.copy2(source,target/source.name)
    (target/'旅行清单.txt').write_text('周末散步\n\n相机、饮用水、一本书。\n\n照片保留原始尺寸，分享副本另存为 JPEG。\nDocuments / 文档：12 个项目，合计 24.8 MB。\n',encoding='utf-8')
    (target/'行程.json').write_text(json.dumps({'title':'周末散步','date':'2026-09-19','places':['河边','咖啡店'],'photos':12},ensure_ascii=False,indent=2)+'\n')
    sound=target/'轻声提示.wav'
    with wave.open(str(sound),'wb') as w:
        rate=22050
        w.setparams((1,2,rate,rate*2,'NONE','not compressed'))
        data=[]
        for i in range(rate*2):
            t=i/rate
            env=min(1,t/.06)*max(0,1-t/2)**2
            data.append(struct.pack('<h',int(1800*env*math.sin(2*math.pi*440*t))))
        w.writeframes(b''.join(data))
    # Fixtures supplied by the photos agent retain original bytes and attribution.
    photo_dir=ROOT/'fixtures/photos'
    if photo_dir.exists():
        for source in photo_dir.rglob('*'):
            if source.is_file() and source.suffix.lower() in ['.jpg','.jpeg','.png','.webp','.avif','.webm','.mp4']:
                shutil.copy2(source,target/source.name)
                if source.suffix.lower() not in ['.webm','.mp4']:
                    dest=a.home/'Pictures'/'周末散步'
                    dest.mkdir(exist_ok=True)
                    shutil.copy2(source,dest/source.name)
    (a.home/'Downloads'/'下载说明.txt').write_text('这里保存从浏览器下载的文件。\nDownload a file in Firefox, then reveal it in Files.\n',encoding='utf-8')
    manifest={str(x.relative_to(a.home)):hashlib.sha256(x.read_bytes()).hexdigest() for x in target.rglob('*') if x.is_file()}
    (a.home/'.local/state/aven').mkdir(exist_ok=True,parents=True)
    (a.home/'.local/state/aven/fixture-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(target)

if __name__=='__main__':main()
