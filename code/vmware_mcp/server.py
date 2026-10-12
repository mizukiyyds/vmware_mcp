"""vmware_mcp：通过 vmrun/vmcli 管理本机 VMware Workstation 虚拟机。

参照 HexRays ida-mcp 的 Code Mode 设计：只提供 6 个工具。
agent 用 reference 按需查命令用法，用 execute 组合任意 vmrun/vmcli 命令，
而不是每个操作一个工具（旧版 48 个工具的 schema 会大量占用上下文窗口）。
"""

import shlex
from pathlib import Path
from typing import Annotated, Literal

from mcp.server import MCPServer
from pydantic import Field

from .inventory import list_registered_vms as read_inventory
from .paths import product_info
from .reference import search_reference
from .vmcli import Vmcli
from .vmrun import Vmrun

_INSTRUCTIONS = (
    "管理本机 VMware Workstation 虚拟机（封装 vmrun/vmcli）。"
    "工作流：list_vms 发现虚拟机 → select_vm 选中当前 VM → "
    "不确定命令写法时 reference 查用法 → execute 执行任意 vmrun/vmcli 命令。"
    "电源、快照、客户机命令、文件传输、共享文件夹、宿主网络、硬件配置全部经 execute 完成；"
    "args 中的 {vm} 会被替换为当前选中的 vmx 路径。"
)

mcp = MCPServer("vmware_mcp", instructions=_INSTRUCTIONS)

vmrun = Vmrun()
vmcli = Vmcli()

_current_vmx = ""


@mcp.tool()
def list_vms() -> str:
    """列出虚拟机：运行中的（vmrun list）+ 虚拟机库中的全部（含关机/暂停），并标注当前选中的 VM。"""
    sections = [f"===== 运行中 =====\n{vmrun.list()}", f"===== 虚拟机库 =====\n{read_inventory()}"]
    if _current_vmx:
        sections.append(f"当前选中: {_current_vmx}")
    else:
        sections.append("当前选中: （无，用 select_vm 选中后 execute 里可用 {vm} 指代）")
    return "\n\n".join(sections)


@mcp.tool()
def select_vm(
    vmx_path: Annotated[str, Field(description="虚拟机 vmx 文件的完整路径；传空串取消选中")],
) -> str:
    """选中后续操作的当前虚拟机，execute 的 args 里用 {vm} 指代。返回该 VM 的电源状态。"""
    global _current_vmx
    vmx_path = vmx_path.strip()
    if not vmx_path:
        _current_vmx = ""
        return "已取消选中"
    if not Path(vmx_path).is_file():
        return f"错误: vmx 文件不存在: {vmx_path}（用 list_vms 查看可用虚拟机）"
    _current_vmx = vmx_path
    state = vmcli.power_query(vmx_path)
    return f"已选中: {vmx_path}\n电源状态: {state}"


@mcp.tool()
def execute(
    tool: Annotated[Literal["vmrun", "vmcli"], Field(description="执行器：vmrun（电源/快照/客户机/网络/共享文件夹）或 vmcli（建机/硬件/磁盘/网卡/MKS/HGFS/模板）")],
    args: Annotated[str, Field(description='命令与参数（不含可执行文件本身），{vm} 替换为当前 vmx。示例：vmrun "listSnapshots {vm} showTree"；vmrun "runProgramInGuest {vm} -noWait C:\\Windows\\System32\\cmd.exe /c ""whoami > C:\\t.txt"""；vmcli "{vm} Power query"（vmx 放首位）；vmrun "listHostNetworks"（无需 vm 的命令不用占位符）')],
    timeout: Annotated[float | None, Field(description="超时秒数；clone 等慢操作建议 600。默认 vmrun 60 / vmcli 120")] = None,
) -> str:
    """执行任意 vmrun/vmcli 命令。-T ws、加密 VM 密码、客户机登录信息（-gu/-gp、-u/-p）自动注入。不确定命令写法先调 reference。"""
    if "{vm}" in args:
        if not _current_vmx:
            return "错误: args 含 {vm} 但尚未选中虚拟机，先调用 select_vm"
        args = args.replace("{vm}", _current_vmx)
    argv = shlex.split(args, posix=False)
    if not argv:
        return "错误: args 为空"
    if tool == "vmrun":
        return vmrun.run(*argv, timeout=timeout)
    return vmcli.run(*argv, timeout=timeout)


@mcp.tool()
def reference(
    query: Annotated[str, Field(description="关键词（中英文均可），如 快照 / runProgramInGuest / Disk / 共享文件夹；留空查看可检索主题")] = "",
) -> str:
    """检索 vmrun/vmcli 命令用法与注意事项（内置笔记 + vmrun/vmcli 实时帮助）。执行命令前先查这里。"""
    return search_reference(query)


@mcp.tool()
def set_guest_credentials(
    username: Annotated[str, Field(description="客户机 OS 登录用户名")],
    password: Annotated[str, Field(description="客户机 OS 登录密码；空密码账户传空字符串")] = "",
) -> str:
    """设置后续客户机操作使用的登录用户名与密码。也可在 mcp.json 的 env 里一次配好 VMWARE_GUEST_USER / VMWARE_GUEST_PASSWORD。"""
    vmrun.set_guest_credentials(username, password)
    vmcli.set_guest_credentials(username, password)
    return "OK"


@mcp.tool()
def get_product_info() -> str:
    """查看本机 VMware Workstation 版本以及 vmrun/vmcli 是否可用"""
    return product_info()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
