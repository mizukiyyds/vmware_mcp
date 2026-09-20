# coding: gbk

"""干净桌面下对比 notepad.exe interactive True/False。"""

import time

from vmware_mcp.vmrun import Vmrun

VMX = r"C:\path\to\vm.vmx"
USER = "guest"
NOTEPAD = r"C:\Windows\System32\notepad.exe"

v = Vmrun()


def kill_notepad() -> None:
    out = v.list_processes_in_guest(VMX, guest_user=USER)
    for line in out.splitlines():
        if "notepad" in line.lower() and line.startswith("pid="):
            pid = int(line.split(",")[0].split("=")[1])
            print("kill notepad", pid, ":", v.kill_process_in_guest(VMX, pid, guest_user=USER))


print("=== kill notepad ===")
kill_notepad()
time.sleep(2)

print("=== t1 interactive=False ===")
print(v.run("runProgramInGuest", VMX, "-noWait", NOTEPAD, guest_user=USER))
time.sleep(3)
print("t1 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\np_ifalse.png", guest_user=USER))
print("t1 进程含 notepad:", "notepad" in v.list_processes_in_guest(VMX, guest_user=USER).lower())

print("=== t2 interactive=True ===")
print(v.run("runProgramInGuest", VMX, "-noWait", "-interactive", NOTEPAD, guest_user=USER))
time.sleep(3)
print("t2 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\np_itrue.png", guest_user=USER))
print("t2 进程含 notepad:", "notepad" in v.list_processes_in_guest(VMX, guest_user=USER).lower())
