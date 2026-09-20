# coding: gbk

__all__ = ["Vmcli"]

import os
import shlex
import subprocess

from .paths import require_exe, resolve_vmware_home

_ENV_GUEST_USER = "VMWARE_GUEST_USER"
_ENV_GUEST_PASSWORD = "VMWARE_GUEST_PASSWORD"

# vmcli 命令形态: vmcli.exe [<vmx>] <Module> <Command> [args]
# 客户机认证为命令级参数（-u/-p），追加在命令参数之后，与 vmrun 的 -gu/-gp 前置不同


def _bool_str(value: bool) -> str:
    return "true" if value else "false"


class Vmcli:
    timeout: float = 120  # VM/Disk Create 等写操作可能较慢

    def __init__(self) -> None:
        home = resolve_vmware_home()
        self.vmcli_path: str = str(require_exe(home, "vmcli.exe"))
        self._default_guest_user = os.environ.get(_ENV_GUEST_USER)
        self._default_guest_password = os.environ.get(_ENV_GUEST_PASSWORD)

    def set_guest_credentials(self, username: str, password: str = "") -> None:
        self._default_guest_user = username
        self._default_guest_password = password

    # ---------- 电源 ----------
    def power_query(self, vmx_path: str) -> str:
        """查询电源状态（vmrun 无此能力，list 只能看到运行中的 VM）"""
        return self.run("Power", "query", vmx=vmx_path)

    # ---------- VM 创建 / 模板 ----------
    def vm_create(
        self, name: str, dirpath: str, guest_type: int | None = None, custom_guest_type: str = ""
    ) -> str:
        args = ["VM", "Create", "-n", name, "-d", dirpath]
        if custom_guest_type:
            args.extend(["-c", custom_guest_type])
        elif guest_type is not None:
            args.extend(["-g", str(guest_type)])
        return self.run(*args)

    def vmtemplate_create(self, vmx_path: str, template_path: str, name: str) -> str:
        return self.run("VMTemplate", "Create", "-p", template_path, "-n", name, vmx=vmx_path)

    def vmtemplate_deploy(self, template_path: str) -> str:
        return self.run("VMTemplate", "Deploy", "-p", template_path)

    # ---------- 芯片组（CPU / 内存） ----------
    def chipset_query(self, vmx_path: str) -> str:
        return self.run("Chipset", "query", vmx=vmx_path)

    def chipset_set_vcpu_count(self, vmx_path: str, vcpus: int) -> str:
        return self.run("Chipset", "SetVCpuCount", str(vcpus), vmx=vmx_path)

    def chipset_set_mem_size(self, vmx_path: str, size_mb: int) -> str:
        return self.run("Chipset", "SetMemSize", str(size_mb), vmx=vmx_path)

    def chipset_set_cores_per_socket(self, vmx_path: str, cores: int) -> str:
        return self.run("Chipset", "SetCoresPerSocket", str(cores), vmx=vmx_path)

    def chipset_set_simultaneous_threads(self, vmx_path: str, threads: int) -> str:
        return self.run("Chipset", "SetSimultaneousThreads", str(threads), vmx=vmx_path)

    # ---------- 磁盘 ----------
    def disk_query(self, vmx_path: str) -> str:
        return self.run("Disk", "query", vmx=vmx_path)

    def disk_create(self, filepath: str, adapter: str, size: str, disk_type: int) -> str:
        return self.run(
            "Disk", "Create", "-f", filepath, "-a", adapter, "-s", size, "-t", str(disk_type)
        )

    def disk_extend(self, vmx_path: str, disk_label: str, new_sectors: int) -> str:
        return self.run("Disk", "Extend", disk_label, str(new_sectors), vmx=vmx_path)

    def disk_connection_control(self, vmx_path: str, disk_label: str, connect_op: str) -> str:
        return self.run("Disk", "ConnectionControl", disk_label, connect_op, vmx=vmx_path)

    def disk_set_present(self, vmx_path: str, disk_label: str, present: bool) -> str:
        return self.run("Disk", "SetPresent", disk_label, _bool_str(present), vmx=vmx_path)

    def disk_set_backing_info(
        self,
        vmx_path: str,
        disk_label: str,
        backing_type: str,
        backing_path: str,
        client_device: str = "false",
    ) -> str:
        return self.run(
            "Disk",
            "SetBackingInfo",
            disk_label,
            backing_type,
            backing_path,
            client_device,
            vmx=vmx_path,
        )

    def disk_set_start_connected(self, vmx_path: str, disk_label: str, start_connected: bool) -> str:
        return self.run(
            "Disk", "SetStartConnected", disk_label, _bool_str(start_connected), vmx=vmx_path
        )

    def disk_is_present(self, vmx_path: str, disk_label: str) -> str:
        return self.run("Disk", "IsPresent", disk_label, vmx=vmx_path)

    def disk_move(self, vmx_path: str, from_label: str, to_label: str) -> str:
        return self.run("Disk", "Move", from_label, to_label, vmx=vmx_path)

    def disk_purge(self, vmx_path: str, disk_label: str) -> str:
        return self.run("Disk", "Purge", disk_label, vmx=vmx_path)

    def disk_set_mode(self, vmx_path: str, disk_label: str, mode: str) -> str:
        return self.run("Disk", "SetMode", disk_label, mode, vmx=vmx_path)

    # ---------- 配置项（直接读写 vmx 条目） ----------
    def config_query(self, vmx_path: str) -> str:
        return self.run("ConfigParams", "query", vmx=vmx_path)

    def config_set_entry(self, vmx_path: str, name: str, value: str) -> str:
        return self.run("ConfigParams", "SetEntry", name, value, vmx=vmx_path)

    # ---------- MKS（键鼠 / 屏幕） ----------
    def mks_query(self, vmx_path: str) -> str:
        return self.run("MKS", "query", vmx=vmx_path)

    def mks_capture_screenshot(self, vmx_path: str, filename: str) -> str:
        return self.run("MKS", "captureScreenshot", filename, vmx=vmx_path)

    def mks_send_key_sequence(self, vmx_path: str, sequence: str) -> str:
        return self.run("MKS", "sendKeySequence", sequence, vmx=vmx_path)

    def mks_send_key_event(self, vmx_path: str, hidcode: int, modifier: int) -> str:
        return self.run("MKS", "sendKeyEvent", str(hidcode), str(modifier), vmx=vmx_path)

    def mks_set_guest_resolution(self, vmx_path: str, width: int, height: int) -> str:
        return self.run("MKS", "SetGuestResolution", str(width), str(height), vmx=vmx_path)

    def mks_set_accel3d(self, vmx_path: str, enable: bool) -> str:
        return self.run("MKS", "SetAccel3d", _bool_str(enable), vmx=vmx_path)

    def mks_set_graphics_memory_kb(self, vmx_path: str, size_kb: int) -> str:
        return self.run("MKS", "SetGraphicsMemoryKB", str(size_kb), vmx=vmx_path)

    def mks_set_num_displays(self, vmx_path: str, count: int) -> str:
        return self.run("MKS", "SetNumDisplays", str(count), vmx=vmx_path)

    def mks_set_vram_size(self, vmx_path: str, size: str) -> str:
        return self.run("MKS", "SetVramSize", size, vmx=vmx_path)

    def mks_set_renderer_3d(self, vmx_path: str, renderer: str) -> str:
        return self.run("MKS", "SetRenderer3d", renderer, vmx=vmx_path)

    def mks_set_fullscreen_at_power_on(self, vmx_path: str, enable: bool) -> str:
        return self.run("MKS", "SetFullscreenAtPowerOn", _bool_str(enable), vmx=vmx_path)

    # ---------- Tools ----------
    def tools_query(self, vmx_path: str) -> str:
        return self.run("Tools", "Query", vmx=vmx_path)

    def tools_install(self, vmx_path: str, cmdline: str = "") -> str:
        args = ["Tools", "Install"]
        if cmdline:
            args.extend(["-c", cmdline])
        return self.run(*args, vmx=vmx_path)

    def tools_upgrade(self, vmx_path: str, cmdline: str = "") -> str:
        args = ["Tools", "Upgrade"]
        if cmdline:
            args.extend(["-c", cmdline])
        return self.run(*args, vmx=vmx_path)

    # ---------- 网卡 ----------
    def ethernet_query(self, vmx_path: str) -> str:
        return self.run("Ethernet", "query", vmx=vmx_path)

    def ethernet_set_connection_type(self, vmx_path: str, device_label: str, connection_type: str) -> str:
        return self.run("Ethernet", "SetConnectionType", device_label, connection_type, vmx=vmx_path)

    def ethernet_connection_control(
        self, vmx_path: str, connect_op: str, device_label: str = ""
    ) -> str:
        args = ["Ethernet", "ConnectionControl"]
        if device_label:
            args.append(device_label)
        args.append(connect_op)
        return self.run(*args, vmx=vmx_path)

    def ethernet_set_present(self, vmx_path: str, device_label: str, present: bool) -> str:
        return self.run("Ethernet", "SetPresent", device_label, _bool_str(present), vmx=vmx_path)

    def ethernet_set_start_connected(
        self, vmx_path: str, device_label: str, start_connected: bool
    ) -> str:
        return self.run(
            "Ethernet", "SetStartConnected", device_label, _bool_str(start_connected), vmx=vmx_path
        )

    def ethernet_set_virtual_device(
        self, vmx_path: str, device_label: str, virtual_device: str
    ) -> str:
        return self.run(
            "Ethernet", "SetVirtualDevice", device_label, virtual_device, vmx=vmx_path
        )

    # ---------- NVMe / SATA / 串口 ----------
    def nvme_query(self, vmx_path: str) -> str:
        return self.run("Nvme", "query", vmx=vmx_path)

    def nvme_set_present(self, vmx_path: str, device_label: str, enabled: bool) -> str:
        return self.run("Nvme", "SetPresent", device_label, _bool_str(enabled), vmx=vmx_path)

    def nvme_find_first_free(self, vmx_path: str, device_label: str) -> str:
        return self.run("Nvme", "FindFirstFree", device_label, vmx=vmx_path)

    def nvme_purge(self, vmx_path: str, device_label: str) -> str:
        return self.run("Nvme", "Purge", device_label, vmx=vmx_path)

    def sata_query(self, vmx_path: str) -> str:
        return self.run("Sata", "query", vmx=vmx_path)

    def sata_set_present(self, vmx_path: str, device_label: str, enabled: bool) -> str:
        return self.run("Sata", "SetPresent", device_label, _bool_str(enabled), vmx=vmx_path)

    def sata_find_first_free(self, vmx_path: str, device_label: str) -> str:
        return self.run("Sata", "FindFirstFree", device_label, vmx=vmx_path)

    def sata_purge(self, vmx_path: str, device_label: str) -> str:
        return self.run("Sata", "Purge", device_label, vmx=vmx_path)

    def serial_query(self, vmx_path: str) -> str:
        return self.run("Serial", "Query", vmx=vmx_path)

    def serial_connection_control(self, vmx_path: str, device_label: str, op_type: str) -> str:
        return self.run("Serial", "ConnectionControl", device_label, op_type, vmx=vmx_path)

    def serial_set_present(self, vmx_path: str, device_label: str, enabled: bool) -> str:
        return self.run("Serial", "SetPresent", device_label, _bool_str(enabled), vmx=vmx_path)

    def serial_purge(self, vmx_path: str, device_label: str) -> str:
        return self.run("Serial", "Purge", device_label, vmx=vmx_path)

    # ---------- HGFS 共享文件夹 ----------
    def hgfs_query(self, vmx_path: str) -> str:
        return self.run("HGFS", "query", vmx=vmx_path)

    def hgfs_set_enabled(self, vmx_path: str, share_label: str, enabled: bool) -> str:
        return self.run("HGFS", "SetEnabled", share_label, _bool_str(enabled), vmx=vmx_path)

    def hgfs_set_host_path(self, vmx_path: str, share_label: str, host_path: str) -> str:
        return self.run("HGFS", "SetHostPath", share_label, host_path, vmx=vmx_path)

    def hgfs_set_write_access(self, vmx_path: str, share_label: str, writable: bool) -> str:
        return self.run("HGFS", "SetWriteAccess", share_label, _bool_str(writable), vmx=vmx_path)

    def hgfs_set_present(self, vmx_path: str, share_label: str, present: bool) -> str:
        return self.run("HGFS", "SetPresent", share_label, _bool_str(present), vmx=vmx_path)

    # ---------- 快照（vmcli 可带描述/内存，query 返回 uid） ----------
    def snapshot_query(self, vmx_path: str) -> str:
        return self.run("Snapshot", "query", vmx=vmx_path)

    def snapshot_take(
        self,
        vmx_path: str,
        name: str,
        description: str = "",
        include_memory: bool = False,
    ) -> str:
        args = ["Snapshot", "Take"]
        if include_memory:
            args.append("-m")
        if description:
            args.extend(["-d", description])
        args.append(name)
        return self.run(*args, vmx=vmx_path)

    # ---------- 客户机 ----------
    def guest_query(self, vmx_path: str) -> str:
        return self.run("Guest", "query", vmx=vmx_path)

    def guest_tools_properties(self, vmx_path: str) -> str:
        return self.run("Guest", "toolsproperties", vmx=vmx_path)

    def guest_env(self, vmx_path: str, guest_user: str = "", guest_password: str = "") -> str:
        return self.run("Guest", "env", vmx=vmx_path, guest_user=guest_user, guest_password=guest_password)

    def guest_create_temp_dir(
        self, vmx_path: str, prefix: str, suffix: str, directory: str,
        guest_user: str = "", guest_password: str = "",
    ) -> str:
        return self.run(
            "Guest", "createTempDir", prefix, suffix, directory,
            vmx=vmx_path, guest_user=guest_user, guest_password=guest_password,
        )

    def guest_create_temp_file(
        self, vmx_path: str, prefix: str, suffix: str, directory: str,
        guest_user: str = "", guest_password: str = "",
    ) -> str:
        return self.run(
            "Guest", "createTempFile", prefix, suffix, directory,
            vmx=vmx_path, guest_user=guest_user, guest_password=guest_password,
        )

    def command(
        self,
        module: str,
        command: str,
        extra_args: str = "",
        vmx: str | None = None,
        guest_user: str = "",
        guest_password: str = "",
        timeout: float | None = None,
    ) -> str:
        args = [module, command, *self._split(extra_args)]
        return self.run(
            *args,
            vmx=vmx or None,
            guest_user=guest_user,
            guest_password=guest_password,
            timeout=timeout,
        )

    # ---------- 底层执行 ----------
    def run(
        self,
        *args: str,
        vmx: str | None = None,
        guest_user: str | None = None,
        guest_password: str | None = None,
        timeout: float | None = None,
    ) -> str:
        cmd = [self.vmcli_path]
        if vmx:
            # vmx 位置参数允许放在命令行最前
            cmd.append(vmx)
        cmd.extend(args)
        user = guest_user or self._default_guest_user
        password = guest_password if guest_password else self._default_guest_password
        if user:
            # Guest 模块命令要求 -u 与 -p 成对出现，空密码也必须传 -p ""
            cmd.extend(["-u", user, "-p", password or ""])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout if timeout is not None else self.timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return f"vmcli 超时: {' '.join(cmd)}"

        output = (result.stdout or "").strip()
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            return f"vmcli 失败({result.returncode}): {err or output}"
        return output or "OK"

    @staticmethod
    def _split(extra_args: str) -> list[str]:
        if not extra_args.strip():
            return []
        return shlex.split(extra_args, posix=False)
