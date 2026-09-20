# coding: gbk

"""测试 calc 的正确启动方式：排查引号错切问题。"""

import time

from vmware_mcp.vmrun import Vmrun

VMX = r"C:\path\to\vm.vmx"
USER = "guest"
CMD = r"C:\Windows\System32\cmd.exe"

v = Vmrun()

# t1: 不带任何引号
print('t1 /c start calc（无引号）:', v.run("runProgramInGuest", VMX, "-noWait", "-interactive", CMD, "/c start calc", guest_user=USER))
time.sleep(5)
print("t1 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\calc_t1_noquote.png", guest_user=USER))

# t2: 直接运行 calc.exe 完整路径
print("t2 calc.exe 直启:", v.run("runProgramInGuest", VMX, "-noWait", "-interactive", r"C:\Windows\System32\calc.exe", guest_user=USER))
time.sleep(5)
print("t2 截屏:", v.capture_screen(VMX, r"C:\temp\vmware-mcp\calc_t2_direct.png", guest_user=USER))
