# Aven offline installation through the original Fedora Anaconda interface.
# Disk selection, partitioning and user credentials remain interactive.
graphical
ostreesetup --osname=fedora --remote=fedora --url=file:///run/install/repo/aven/ostree/repo --ref=aven/44/x86_64/prototype --nogpg

%post --nochroot --erroronfail --log=/tmp/aven-post.log
/usr/bin/python3 /run/install/repo/aven/source/iso/install-target.py
%end
