from pathlib import Path
import json,hashlib,socket,mailbox
h=Path.home()
paths=[h/'Documents/日常 · Everyday/旅行清单.txt', h/'Documents/日常·Everyday/旅行清单.txt', h/'Downloads/周末路线.txt', h/'Documents/ISO-copy.txt', h/'Downloads/ISO-copy.txt', h/'.local/share/Trash/files/ISO-copy.txt']
paths+=list((h/'Documents').glob('*/旅行清单.txt'))
rows=[]
for path in dict.fromkeys(paths):
 r={'path':str(path),'exists':path.exists()}
 if path.is_file():
  data=path.read_bytes();r.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 rows.append(r)
drafts=[]
for path in (h/'.local/share/aven/mail').glob('*/Mail/Local Folders/Drafts'):
 data=path.read_bytes();items=[]
 for msg in mailbox.mbox(path,create=False):
  parts=msg.walk() if msg.is_multipart() else [msg];found=False
  for part in parts:
   if part.get_content_maintype()=='text':
    content=(part.get_payload(decode=True) or b'').decode(part.get_content_charset() or 'utf-8',errors='replace')
    if '路线已经核对' in content: found=True
  items.append({'subject':msg.get('Subject'),'has_saved_text':found})
 drafts.append({'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'items':items})
print(json.dumps({'hostname':socket.gethostname(),'files':rows,'drafts':drafts},ensure_ascii=False))
