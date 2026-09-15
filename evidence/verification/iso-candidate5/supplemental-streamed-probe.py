import json,hashlib,subprocess,base64
from pathlib import Path
def h(p):
 b=p.read_bytes();s=p.stat();return {"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"mtime_ns":s.st_mtime_ns}
def run(argv):
 r=subprocess.run(argv,text=True,capture_output=True,timeout=30);return {"argv":argv,"exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
home=Path.home();src=Path("/var/lib/aven/source");checks=[]
for relative,target in [("preview/aven_preview",home/".local/libexec/aven-preview/aven_preview"),("browser/chrome",home/".local/share/aven/firefox/chrome"),("mail/chrome",home/".local/share/aven/mail/default/chrome")]:
 for original in sorted((src/relative).rglob("*")):
  if not original.is_file() or "__pycache__" in original.parts:continue
  deployed=target/original.relative_to(src/relative);a=h(original);b=h(deployed);checks.append({"source":str(original),"runtime":str(deployed),"source_sha256":a["sha256"],"runtime_sha256":b["sha256"],"runtime_mtime_ns":b["mtime_ns"],"passed":a["sha256"]==b["sha256"]})
from PySide6.QtCore import qVersion
report={"runtime_checks":checks,"runtime_checks_passed":all(c["passed"] for c in checks),"qt_version":qVersion(),"versions":run(["rpm","-q","--qf","%{NAME}\t%{VERSION}-%{RELEASE}\n","plasma-workspace","kwin","dolphin","firefox","thunderbird","gwenview","okular","qt6-qtbase","qt6-qtwayland","python3-pyside6"]),"mounts":run(["findmnt","--json","--output","SOURCE,TARGET,FSTYPE,OPTIONS"]),"kernel":run(["uname","-r"]),"places_backup_base64":base64.b64encode((home/".local/share/user-places.xbel.pre-aven").read_bytes()).decode(),"boot_id":Path("/proc/sys/kernel/random/boot_id").read_text().strip()}
print(json.dumps(report))
