# coding: gbk

from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from .inventory import list_registered_vms as read_inventory
from .paths import product_info
from .vmcli import Vmcli
from .vmrun import Vmrun

mcp = MCPServer(
    "vmware_mcp",
    description="通过 vmrun 与 vmcli 管理本机 VMware Workstation 虚拟机。客户机登录信息在 mcp.json 的 VMWARE_GUEST_USER / VMWARE_GUEST_PASSWORD 中一次配置，或用 set_guest_credentials 更新。",
)

vmrun = Vmrun()
vmcli = Vmcli()



# ---- 参数描述别名（schema 中展示给 AI agent，帮助其理解参数含义） ----
VmxPath = Annotated[str, Field(description="虚拟机 vmx 文件的完整路径，可用 list 或 list_registered_vms 获取")]
GuestUser = Annotated[str, Field(description="客户机 OS 登录用户名")]
GuestPassword = Annotated[str, Field(description="客户机 OS 登录密码；空密码账户传空字符串")]
GuestPath = Annotated[str, Field(description="客户机内的完整路径，如 C:\\mcp_test\\a.txt")]
HostPath = Annotated[str, Field(description="宿主机上的完整路径，如 D:\\files\\a.txt")]
SnapshotName = Annotated[str, Field(description="快照名称，可用 list_snapshots 查看")]
ShareName = Annotated[str, Field(description="共享文件夹名称")]
DeviceLabel = Annotated[str, Field(description="设备标签，如 ethernet0")]

# ============ 电源管理 ============


@mcp.tool()
def list() -> str:
    """列出当前正在运行的 VMware 虚拟机（vmx 路径与数量）"""
    return vmrun.list()

@mcp.tool()
def list_registered_vms() -> str:
    """列出 Workstation 虚拟机库中的全部虚拟机（含关机/暂停），读取 %APPDATA%\\VMware\\inventory.vmls"""
    return read_inventory()

@mcp.tool()
def get_product_info() -> str:
    """查看本机 VMware Workstation 版本以及 vmrun/vmcli 是否可用"""
    return product_info()

@mcp.tool()
def set_guest_credentials(
    username: GuestUser,
    password: GuestPassword = "",
) -> str:
    """设置后续客户机操作使用的登录用户名与密码。也可在 mcp.json 的 env 里一次配好 VMWARE_GUEST_USER / VMWARE_GUEST_PASSWORD。"""
    vmrun.set_guest_credentials(username, password)
    vmcli.set_guest_credentials(username, password)
    return "OK"

@mcp.tool()
def start(
    vmx_path: VmxPath,
    gui: Annotated[bool, Field(description="True 显示虚拟机界面，False 后台无界面启动")] = False,
) -> str:
    """启动虚拟机。gui=True 显示界面，False 后台无界面启动"""
    return vmrun.start(vmx_path, gui)

@mcp.tool()
def stop(
    vmx_path: VmxPath,
    hard: Annotated[bool, Field(description="False 软关机（需 Tools），True 强制断电")] = False,
) -> str:
    """关闭虚拟机。hard=False 软关机（需 Tools），True 强制断电"""
    return vmrun.stop(vmx_path, hard)

@mcp.tool()
def reset(
    vmx_path: VmxPath,
    hard: Annotated[bool, Field(description="True 强制重置，False 软重启")] = False,
) -> str:
    """重启虚拟机。hard=True 强制重置"""
    return vmrun.reset(vmx_path, hard)

@mcp.tool()
def suspend(
    vmx_path: VmxPath,
    hard: Annotated[bool, Field(description="True 强制挂起，False 软挂起")] = False,
) -> str:
    """挂起虚拟机（保存状态到磁盘）"""
    return vmrun.suspend(vmx_path, hard)

# ============ 快照 ============


@mcp.tool()
def list_snapshots(
    vmx_path: VmxPath,
    show_tree: Annotated[bool, Field(description="True 以树形显示快照层级")] = False,
) -> str:
    """列出虚拟机的所有快照，show_tree=True 以树形显示层级"""
    return vmrun.list_snapshots(vmx_path, show_tree)

@mcp.tool()
def create_snapshot(
    vmx_path: VmxPath,
    name: SnapshotName,
    description: Annotated[str, Field(description="快照说明，非空时改走 vmcli Snapshot Take")] = "",
    include_memory: Annotated[bool, Field(description="True 保存运行中内存状态（经 vmcli）")] = False,
) -> str:
    """为虚拟机创建快照。需要说明或保存内存时走 vmcli，否则走 vmrun"""
    if description or include_memory:
        return vmcli.snapshot_take(vmx_path, name, description, include_memory)
    return vmrun.create_snapshot(vmx_path, name)

@mcp.tool()
def delete_snapshot(
    vmx_path: VmxPath,
    name: SnapshotName,
    delete_children: Annotated[bool, Field(description="True 同时删除该快照的所有子快照")] = False,
) -> str:
    """删除指定快照，delete_children=True 同时删除其子快照"""
    return vmrun.delete_snapshot(vmx_path, name, delete_children)

@mcp.tool()
def revert_to_snapshot(vmx_path: VmxPath, name: SnapshotName) -> str:
    """将虚拟机恢复到指定快照的状态（注意：恢复后虚拟机处于关机状态，需要 start 重新开机）"""
    return vmrun.revert_to_snapshot(vmx_path, name)

# ============ 客户机 OS ============


@mcp.tool()
def get_guest_ip(
    vmx_path: VmxPath,
    wait: Annotated[bool, Field(description="True 阻塞等待直到获取到 IP")] = False,
) -> str:
    """获取客户机 IP 地址，wait=True 阻塞等待直到获取成功"""
    return vmrun.get_guest_ip(vmx_path, wait)

@mcp.tool()
def run_program_in_guest(
    vmx_path: VmxPath,
    program: Annotated[str, Field(description="客户机内程序完整路径，如 C:\\Windows\\System32\\cmd.exe")],
    program_args: Annotated[str, Field(description='程序参数，整串传递；cmd 场景需形如 /c "命令 > 输出文件"')] = "",
    no_wait: Annotated[bool, Field(description="True 不等待程序结束立即返回")] = False,
    interactive: Annotated[bool, Field(description="GUI 程序必须 True 才会显示在客户机用户桌面；纯命令行可 False")] = False,
    active_window: Annotated[bool, Field(description="True 启动后激活窗口（vmrun -activeWindow）")] = False,
) -> str:
    """在客户机内运行程序。GUI 程序需 interactive=True 才显示在用户桌面，且 program 直接给完整路径（如 C:\\Windows\\System32\\calc.exe）；不要用 cmd /c start 开 GUI（引号会被错切）。不返回程序 stdout，需让程序把输出写到客户机文件再 copy_file_from_guest 捞回"""
    return vmrun.run_program_in_guest(
        vmx_path,
        program,
        program_args,
        no_wait,
        interactive,
        active_window,
    )

@mcp.tool()
def run_script_in_guest(
    vmx_path: VmxPath,
    interpreter: Annotated[str, Field(description="解释器完整路径，如 cmd.exe / powershell.exe / /bin/bash")],
    script_text: Annotated[str, Field(description="脚本文本")],
    no_wait: Annotated[bool, Field(description="True 不等待脚本结束立即返回")] = False,
    interactive: Annotated[bool, Field(description="True 以交互会话运行，便于 GUI 可见")] = False,
    active_window: Annotated[bool, Field(description="True 启动后激活窗口")] = False,
) -> str:
    """在客户机内用指定解释器执行脚本文本（Windows cmd 建议改用 run_program_in_guest 的 /c 形态）"""
    return vmrun.run_script_in_guest(
        vmx_path,
        interpreter,
        script_text,
        no_wait,
        interactive,
        active_window,
    )

@mcp.tool()
def list_processes_in_guest(vmx_path: VmxPath) -> str:
    """列出客户机内正在运行的进程"""
    return vmrun.list_processes_in_guest(vmx_path)

@mcp.tool()
def kill_process_in_guest(
    vmx_path: VmxPath,
    pid: Annotated[int, Field(description="要结束的进程 PID，可用 list_processes_in_guest 查看")],
) -> str:
    """按 PID 结束客户机内的进程"""
    return vmrun.kill_process_in_guest(vmx_path, pid)

@mcp.tool()
def file_exists_in_guest(
    vmx_path: VmxPath, guest_path: GuestPath
) -> str:
    """检查客户机内文件是否存在"""
    return vmrun.file_exists_in_guest(vmx_path, guest_path)

@mcp.tool()
def directory_exists_in_guest(
    vmx_path: VmxPath, guest_path: GuestPath
) -> str:
    """检查客户机内目录是否存在"""
    return vmrun.directory_exists_in_guest(vmx_path, guest_path)

@mcp.tool()
def list_directory_in_guest(
    vmx_path: VmxPath, guest_path: GuestPath
) -> str:
    """列出客户机内目录内容"""
    return vmrun.list_directory_in_guest(vmx_path, guest_path)

@mcp.tool()
def create_directory_in_guest(
    vmx_path: VmxPath, guest_path: GuestPath
) -> str:
    """在客户机内创建目录"""
    return vmrun.create_directory_in_guest(vmx_path, guest_path)

@mcp.tool()
def delete_file_in_guest(
    vmx_path: VmxPath, guest_path: GuestPath
) -> str:
    """删除客户机内文件"""
    return vmrun.delete_file_in_guest(vmx_path, guest_path)

@mcp.tool()
def delete_directory_in_guest(
    vmx_path: VmxPath, guest_path: GuestPath
) -> str:
    """删除客户机内目录"""
    return vmrun.delete_directory_in_guest(vmx_path, guest_path)

@mcp.tool()
def copy_file_to_guest(
    vmx_path: VmxPath,
    host_path: HostPath,
    guest_path: GuestPath,
) -> str:
    """把宿主机文件复制到客户机"""
    return vmrun.copy_file_to_guest(vmx_path, host_path, guest_path)

@mcp.tool()
def copy_file_from_guest(
    vmx_path: VmxPath,
    guest_path: GuestPath,
    host_path: HostPath,
) -> str:
    """把客户机文件复制到宿主机"""
    return vmrun.copy_file_from_guest(vmx_path, guest_path, host_path)

@mcp.tool()
def rename_file_in_guest(
    vmx_path: VmxPath,
    original: Annotated[str, Field(description="客户机内原文件完整路径")],
    new: Annotated[str, Field(description="新文件完整路径")],
) -> str:
    """重命名客户机内文件"""
    return vmrun.rename_file_in_guest(vmx_path, original, new)

@mcp.tool()
def capture_screen(
    vmx_path: VmxPath,
    host_path: Annotated[str, Field(description="截图保存到宿主机的完整路径，如 D:\\shot.png")],
) -> str:
    """截取虚拟机屏幕，保存为宿主机上的图片文件"""
    return vmrun.capture_screen(vmx_path, host_path)

@mcp.tool()
def type_keystrokes_in_guest(
    vmx_path: VmxPath,
    keystrokes: Annotated[str, Field(description="要输入的按键字符串")],
) -> str:
    """向客户机输入按键（vmrun typeKeystrokesInGuest）"""
    return vmrun.type_keystrokes_in_guest(
        vmx_path, keystrokes
    )

# ============ 宿主网络 ============


@mcp.tool()
def list_host_networks() -> str:
    """列出宿主机所有虚拟网络（如 vmnet0/vmnet1/vmnet8）"""
    return vmrun.list_host_networks()

@mcp.tool()
def list_port_forwardings(
    network: Annotated[str, Field(description="宿主网络名，如 vmnet8，可用 list_host_networks 查看")],
) -> str:
    """列出指定宿主网络上的端口转发规则"""
    return vmrun.list_port_forwardings(network)

@mcp.tool()
def set_port_forwarding(
    network: Annotated[str, Field(description="宿主网络名，如 vmnet8")],
    protocol: Annotated[str, Field(description="协议：tcp | udp")],
    host_port: Annotated[int, Field(description="宿主机端口")],
    guest_ip: Annotated[str, Field(description="客户机 IP，可用 get_guest_ip 获取")],
    guest_port: Annotated[int, Field(description="客户机端口")],
    description: Annotated[str, Field(description="规则备注")] = "",
) -> str:
    """在宿主网络上添加/更新端口转发。protocol: tcp | udp"""
    return vmrun.set_port_forwarding(network, protocol, host_port, guest_ip, guest_port, description)

@mcp.tool()
def delete_port_forwarding(
    network: Annotated[str, Field(description="宿主网络名，如 vmnet8")],
    protocol: Annotated[str, Field(description="协议：tcp | udp")],
    host_port: Annotated[int, Field(description="宿主机端口")],
) -> str:
    """删除宿主网络上的端口转发规则"""
    return vmrun.delete_port_forwarding(network, protocol, host_port)

# ============ 共享文件夹 ============


@mcp.tool()
def list_shared_folders(vmx_path: VmxPath) -> str:
    """列出虚拟机的共享文件夹及运行时状态（经 vmcli HGFS query，需要虚拟机处于运行状态）"""
    return vmcli.hgfs_query(vmx_path)

@mcp.tool()
def add_shared_folder(vmx_path: VmxPath, share_name: ShareName, host_path: HostPath) -> str:
    """添加宿主机-客户机共享文件夹（客户机中经 \\\\vmware-host\\Shared Folders\\<名称> 访问）"""
    return vmrun.add_shared_folder(vmx_path, share_name, host_path)

@mcp.tool()
def remove_shared_folder(vmx_path: VmxPath, share_name: ShareName) -> str:
    """移除共享文件夹"""
    return vmrun.remove_shared_folder(vmx_path, share_name)

# ============ 通用 ============


@mcp.tool()
def check_tools_state(vmx_path: VmxPath) -> str:
    """检查客户机 VMware Tools 状态（running/notInstalled 等）"""
    return vmrun.check_tools_state(vmx_path)

@mcp.tool()
def clone_vm(
    vmx_path: VmxPath,
    dest_vmx_path: Annotated[str, Field(description="克隆目标 vmx 完整路径")],
    linked: Annotated[bool, Field(description="True 链接克隆（省空间，依赖源 VM），False 完整克隆")] = False,
    snapshot_name: Annotated[str, Field(description="基于哪个快照克隆，留空基于当前状态")] = "",
    clone_name: Annotated[str, Field(description="克隆后的显示名称")] = "",
) -> str:
    """克隆虚拟机。linked=True 链接克隆（省空间，依赖源），False 完整克隆"""
    return vmrun.clone_vm(vmx_path, dest_vmx_path, linked, snapshot_name, clone_name)

# ============ vmcli 扩展（电源查询 / 建机 / 硬件配置 / 磁盘 / 键鼠屏幕） ============


@mcp.tool()
def get_power_state(vmx_path: VmxPath) -> str:
    """查询虚拟机电源状态（on/off/suspended 等；vmrun 的 list 只能看到运行中的 VM，查关机状态用本工具）"""
    return vmcli.power_query(vmx_path)

@mcp.tool()
def get_chipset(vmx_path: VmxPath) -> str:
    """查询虚拟机 CPU/内存等芯片组配置"""
    return vmcli.chipset_query(vmx_path)

@mcp.tool()
def set_vcpu_count(
    vmx_path: VmxPath,
    vcpus: Annotated[int, Field(description="vCPU 总数")],
) -> str:
    """设置虚拟机 vCPU 数量"""
    return vmcli.chipset_set_vcpu_count(vmx_path, vcpus)

@mcp.tool()
def set_memory_mb(
    vmx_path: VmxPath,
    size_mb: Annotated[int, Field(description="内存大小，单位 MB")],
) -> str:
    """设置虚拟机内存大小（MB）"""
    return vmcli.chipset_set_mem_size(vmx_path, size_mb)

@mcp.tool()
def list_disks(vmx_path: VmxPath) -> str:
    """查询虚拟机磁盘列表与状态（设备标签如 scsi0:0、容量等）"""
    return vmcli.disk_query(vmx_path)

@mcp.tool()
def list_ethernet(vmx_path: VmxPath) -> str:
    """查询虚拟机网卡配置（设备标签、连接类型等）"""
    return vmcli.ethernet_query(vmx_path)

@mcp.tool()
def set_ethernet_connection_type(
    vmx_path: VmxPath,
    device_label: DeviceLabel,
    connection_type: Annotated[str, Field(description="连接类型，如 nat | bridged | hostonly")],
) -> str:
    """设置网卡连接类型（如 nat / bridged / hostonly）"""
    return vmcli.ethernet_set_connection_type(vmx_path, device_label, connection_type)

@mcp.tool()
def ethernet_connection_control(
    vmx_path: VmxPath,
    connect_op: Annotated[str, Field(description="connect 或 disconnect")],
    device_label: Annotated[str, Field(description="网卡标签，如 ethernet0；部分版本可留空")] = "",
) -> str:
    """运行时连接或断开虚拟网卡"""
    return vmcli.ethernet_connection_control(vmx_path, connect_op, device_label)

@mcp.tool()
def set_ethernet_start_connected(
    vmx_path: VmxPath,
    device_label: DeviceLabel,
    start_connected: Annotated[bool, Field(description="True 开机连接该网卡")],
) -> str:
    """设置下次开机是否连接该网卡"""
    return vmcli.ethernet_set_start_connected(vmx_path, device_label, start_connected)

# ============ 未单独封装的命令逃生口 ============


@mcp.tool()
def vmrun_command(
    extra_args: Annotated[str, Field(description="vmrun 命令与参数，不含可执行文件本身，如 'listSnapshots D:\\\\vm\\\\a.vmx showTree'")],
) -> str:
    """直接调用 vmrun（已自动加 -T ws）。用于尚未单独封装的命令"""
    return vmrun.command(extra_args)

@mcp.tool()
def vmcli_command(
    module: Annotated[str, Field(description="模块名，如 Disk / Nvme / Guest / MKS")],
    command: Annotated[str, Field(description="模块内命令，如 query / SetPresent")],
    vmx_path: Annotated[str, Field(description="需要操作虚拟机时填 vmx 路径，否则留空")] = "",
    extra_args: Annotated[str, Field(description="其余参数，按 vmcli 帮助原样填写")] = "",
) -> str:
    """直接调用 vmcli 模块命令。用于尚未单独封装的高级选项（例如 Disk SetBandwidthCap）"""
    return vmcli.command(
        module,
        command,
        extra_args,
        vmx=vmx_path,
    )

# ============ Resources ============


@mcp.resource(
    "vmware://vms/running",
    name="running_vms",
    title="正在运行的虚拟机",
    description="当前正在运行的 VMware 虚拟机列表（vmx 路径与数量）",
    mime_type="text/plain",
)
def running_vms() -> str:
    return vmrun.list()


@mcp.resource(
    "vmware://vms/registered",
    name="registered_vms",
    title="虚拟机库中的全部虚拟机",
    description="Workstation 虚拟机库清单（含关机/暂停），来自 inventory.vmls",
    mime_type="text/plain",
)
def registered_vms() -> str:
    return read_inventory()


@mcp.resource(
    "vmware://host/networks",
    name="host_networks",
    title="宿主机虚拟网络",
    description="宿主机上所有 VMware 虚拟网络列表",
    mime_type="text/plain",
)
def host_networks() -> str:
    return vmrun.list_host_networks()


@mcp.resource(
    "vmware://host/product",
    name="product_info",
    title="本机 VMware 产品信息",
    description="Workstation 安装路径与 vmrun/vmcli 版本",
    mime_type="text/plain",
)
def product_info_resource() -> str:
    return product_info()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
