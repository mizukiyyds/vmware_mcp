# coding: gbk

"""干净桌面下对比 calc.exe interactive True/False。先杀光计算器再测。"""

import time

from vmware_mcp.vmrun import Vmrun

VMX = r"C:\path\to\vm.vmx"
USER = "guest"
CALC = r"C:\Windows\System32\calc.exe"

v = Vmrun()


def kill_calc() -> None:
    out = v.list_processes_in_guest(VMX, guest_user=USER)
    killed = 0
    for line in out.splitlines():
        low = line.lower()
        if "calc" in low or "calculator" in low:
            print("  found:", line)
            # pid=1234, owner=..., cmd=...
            if line.startswith("pid="):
                pid = int(line.split(",")[0].split("=")[1])
                print("  kill", pid, ":", v.kill_process_in_guest(VMX, pid, guest_user=USER))
                killed += 1
    print(f"killed {killed} calc-related processes")


print("=== kill existing calc ===")
kill_calc()
time.sleep(2)
print("baseline 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\calc_baseline.png", guest_user=USER))

print("=== t1 interactive=False ===")
print(v.run("runProgramInGuest", VMX, "-noWait", CALC, guest_user=USER))
time.sleep(4)
print("t1 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\calc_ifalse_clean.png", guest_user=USER))
print("t1 进程含 calc:", "calc" in v.list_processes_in_guest(VMX, guest_user=USER).lower())

print("=== t2 interactive=True ===")
print(v.run("runProgramInGuest", VMX, "-noWait", "-interactive", CALC, guest_user=USER))
time.sleep(4)
print("t2 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\calc_itrue_clean.png", guest_user=USER))
print("t2 进程含 calc:", "calc" in v.list_processes_in_guest(VMX, guest_user=USER).lower())
