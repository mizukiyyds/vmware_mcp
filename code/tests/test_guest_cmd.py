# coding: gbk

"""客户机命令执行调试脚本：测试 runProgramInGuest 调用 cmd.exe 的正确参数形态。"""

from vmware_mcp.vmrun import Vmrun

VMX = r"C:\path\to\vm.vmx"
USER = "guest"
CMD = r"C:\Windows\System32\cmd.exe"

v = Vmrun()

cases = {
    # 整体作为一个带引号字符串参数
    "t3_quoted": [CMD, '/c "whoami > C:\\mcp_test\\guest_info.txt"'],
    # interactive 模式
    "t4_interactive": ["-interactive", CMD, "/c whoami > C:\\mcp_test\\guest_info.txt"],
    # activeWindow 模式
    "t5_activewindow": ["-activeWindow", CMD, "/c whoami > C:\\mcp_test\\guest_info.txt"],
}

for name, args in cases.items():
    r = v.run("runProgramInGuest", VMX, *args, guest_user=USER)
    print(f"{name}: {r}")
    print("exists:", v.file_exists_in_guest(VMX, r"C:\mcp_test\guest_info.txt", guest_user=USER))

# 追加 IP 信息并拷回宿主机
r = v.run(
    "runProgramInGuest",
    VMX,
    CMD,
    '/c "ipconfig | findstr IPv4 >> C:\\mcp_test\\guest_info.txt"',
    guest_user=USER,
)
print("append ip:", r)
print(
    "copy_back:",
    v.copy_file_from_guest(
        VMX,
        r"C:\mcp_test\guest_info.txt",
        r"C:\temp\vmware-mcp\guest_info.txt",
        guest_user=USER,
    ),
)
