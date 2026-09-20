# coding: gbk

"""测试客户机 GUI 程序在交互会话中启动：-interactive 标志 + notepad/calc，截屏验证。"""

import time

from vmware_mcp.vmrun import Vmrun

VMX = r"C:\path\to\vm.vmx"
USER = "guest"
CMD = r"C:\Windows\System32\cmd.exe"

v = Vmrun()

# t1: notepad，无 interactive
print("t1 notepad 无interactive:", v.run("runProgramInGuest", VMX, "-noWait", r"C:\Windows\System32\notepad.exe", guest_user=USER))
time.sleep(3)
print("t1 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\t1_notepad_nointeractive.png", guest_user=USER))

# t2: notepad，interactive
print("t2 notepad interactive:", v.run("runProgramInGuest", VMX, "-noWait", "-interactive", r"C:\Windows\System32\notepad.exe", guest_user=USER))
time.sleep(3)
print("t2 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\t2_notepad_interactive.png", guest_user=USER))

# t3: calc，interactive（UWP，经 cmd start）
print("t3 calc interactive:", v.run("runProgramInGuest", VMX, "-noWait", "-interactive", CMD, '/c "start calc"', guest_user=USER))
time.sleep(5)
print("t3 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\t3_calc_interactive.png", guest_user=USER))

# 进程列表看 notepad（Win32 进程应可见）
print("进程列表含 notepad:", "notepad" in v.list_processes_in_guest(VMX, guest_user=USER).lower())
