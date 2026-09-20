# coding: gbk

__all__ = ["Vmrun"]

import os
import shlex
import subprocess

from .paths import require_exe, resolve_vmware_home

_ENV_GUEST_USER = "VMWARE_GUEST_USER"
_ENV_GUEST_PASSWORD = "VMWARE_GUEST_PASSWORD"
_ENV_VM_PASSWORD = "VMWARE_VM_PASSWORD"
_ENV_HOST_TYPE = "VMWARE_HOST_TYPE"

# vmrun 认证参数必须出现在命令之前，形如: vmrun -T ws -gu user -gp pass <command> ...


class Vmrun:
    timeout: float = 60

    def __init__(self) -> None:
        home = resolve_vmware_home()
        self.vmrun_path: str = str(require_exe(home, "vmrun.exe"))
        self.host_type = (os.environ.get(_ENV_HOST_TYPE) or "ws").strip() or "ws"
        self._default_guest_user = os.environ.get(_ENV_GUEST_USER)
        self._default_guest_password = os.environ.get(_ENV_GUEST_PASSWORD)
        self._vm_password = os.environ.get(_ENV_VM_PASSWORD) or ""

    def set_guest_credentials(self, username: str, password: str = "") -> None:
        self._default_guest_user = username
        self._default_guest_password = password

    # ---------- 电源 ----------
    def list(self) -> str:
        return self.run("list")

    def start(self, vmx_path: str, gui: bool = False) -> str:
        return self.run("start", vmx_path, "gui" if gui else "nogui")

    def stop(self, vmx_path: str, hard: bool = False) -> str:
        return self.run("stop", vmx_path, "hard" if hard else "soft")

    def reset(self, vmx_path: str, hard: bool = False) -> str:
        return self.run("reset", vmx_path, "hard" if hard else "soft")

    def suspend(self, vmx_path: str, hard: bool = False) -> str:
        return self.run("suspend", vmx_path, "hard" if hard else "soft")

    def pause(self, vmx_path: str) -> str:
        return self.run("pause", vmx_path)

    def unpause(self, vmx_path: str) -> str:
        return self.run("unpause", vmx_path)

    # ---------- 快照 ----------
    def list_snapshots(self, vmx_path: str, show_tree: bool = False) -> str:
        args = ["listSnapshots", vmx_path]
        if show_tree:
            args.append("showTree")
        return self.run(*args)

    def create_snapshot(self, vmx_path: str, name: str) -> str:
        return self.run("snapshot", vmx_path, name)

    def delete_snapshot(self, vmx_path: str, name: str, delete_children: bool = False) -> str:
        args = ["deleteSnapshot", vmx_path, name]
        if delete_children:
            args.append("andDeleteChildren")
        return self.run(*args)

    def revert_to_snapshot(self, vmx_path: str, name: str) -> str:
        return self.run("revertToSnapshot", vmx_path, name)

    # ---------- 客户机 OS ----------
    def run_program_in_guest(
        self,
        vmx_path: str,
        program: str,
        program_args: str = "",
        no_wait: bool = False,
        interactive: bool = False,
        active_window: bool = False,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        args = ["runProgramInGuest", vmx_path]
        if no_wait:
            args.append("-noWait")
        if active_window:
            args.append("-activeWindow")
        if interactive:
            args.append("-interactive")
        args.append(program)
        if program_args:
            # 整串作为单个参数传递，不能按空格拆分：
            # cmd 场景需要 '/c "whoami > file"' 这样的完整引号串，拆开会让 cmd 退出码 1
            args.append(program_args)
        return self.run(*args, guest_user=guest_user, guest_password=guest_password)

    def run_script_in_guest(
        self,
        vmx_path: str,
        interpreter: str,
        script_text: str,
        no_wait: bool = False,
        interactive: bool = False,
        active_window: bool = False,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        args = ["runScriptInGuest", vmx_path]
        if no_wait:
            args.append("-noWait")
        if active_window:
            args.append("-activeWindow")
        if interactive:
            args.append("-interactive")
        args.extend([interpreter, script_text])
        return self.run(*args, guest_user=guest_user, guest_password=guest_password)

    def list_processes_in_guest(
        self, vmx_path: str, guest_user: str | None = None, guest_password: str | None = None
    ) -> str:
        return self.run(
            "listProcessesInGuest", vmx_path, guest_user=guest_user, guest_password=guest_password
        )

    def kill_process_in_guest(
        self,
        vmx_path: str,
        pid: int,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "killProcessInGuest",
            vmx_path,
            str(pid),
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def file_exists_in_guest(
        self,
        vmx_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "fileExistsInGuest",
            vmx_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def directory_exists_in_guest(
        self,
        vmx_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "directoryExistsInGuest",
            vmx_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def list_directory_in_guest(
        self,
        vmx_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "listDirectoryInGuest",
            vmx_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def create_directory_in_guest(
        self,
        vmx_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "createDirectoryInGuest",
            vmx_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def delete_file_in_guest(
        self,
        vmx_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "deleteFileInGuest",
            vmx_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def delete_directory_in_guest(
        self,
        vmx_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "deleteDirectoryInGuest",
            vmx_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def copy_file_to_guest(
        self,
        vmx_path: str,
        host_path: str,
        guest_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "CopyFileFromHostToGuest",
            vmx_path,
            host_path,
            guest_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def copy_file_from_guest(
        self,
        vmx_path: str,
        guest_path: str,
        host_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "CopyFileFromGuestToHost",
            vmx_path,
            guest_path,
            host_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def rename_file_in_guest(
        self,
        vmx_path: str,
        original: str,
        new: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "renameFileInGuest",
            vmx_path,
            original,
            new,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def capture_screen(
        self,
        vmx_path: str,
        host_path: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "captureScreen",
            vmx_path,
            host_path,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def type_keystrokes_in_guest(
        self,
        vmx_path: str,
        keystrokes: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "typeKeystrokesInGuest",
            vmx_path,
            keystrokes,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def connect_named_device(self, vmx_path: str, device_name: str) -> str:
        return self.run("connectNamedDevice", vmx_path, device_name)

    def disconnect_named_device(self, vmx_path: str, device_name: str) -> str:
        return self.run("disconnectNamedDevice", vmx_path, device_name)

    def read_variable(
        self,
        vmx_path: str,
        name: str,
        kind: str = "runtimeConfig",
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "readVariable",
            vmx_path,
            kind,
            name,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def write_variable(
        self,
        vmx_path: str,
        name: str,
        value: str,
        kind: str = "runtimeConfig",
        guest_user: str | None = None,
        guest_password: str | None = None,
    ) -> str:
        return self.run(
            "writeVariable",
            vmx_path,
            kind,
            name,
            value,
            guest_user=guest_user,
            guest_password=guest_password,
        )

    def get_guest_ip(self, vmx_path: str, wait: bool = False) -> str:
        args = ["getGuestIPAddress", vmx_path]
        if wait:
            args.append("-wait")
        return self.run(*args)

    # ---------- 宿主网络 ----------
    def list_host_networks(self) -> str:
        return self.run("listHostNetworks")

    def list_port_forwardings(self, network: str) -> str:
        return self.run("listPortForwardings", network)

    def set_port_forwarding(
        self,
        network: str,
        protocol: str,
        host_port: int,
        guest_ip: str,
        guest_port: int,
        description: str = "",
    ) -> str:
        args = [
            "setPortForwarding",
            network,
            protocol,
            str(host_port),
            guest_ip,
            str(guest_port),
        ]
        if description:
            args.append(description)
        return self.run(*args)

    def delete_port_forwarding(self, network: str, protocol: str, host_port: int) -> str:
        return self.run("deletePortForwarding", network, protocol, str(host_port))

    # ---------- 共享文件夹 ----------
    def enable_shared_folders(self, vmx_path: str, runtime: bool = False) -> str:
        args = ["enableSharedFolders", vmx_path]
        if runtime:
            args.append("runtime")
        return self.run(*args)

    def disable_shared_folders(self, vmx_path: str, runtime: bool = False) -> str:
        args = ["disableSharedFolders", vmx_path]
        if runtime:
            args.append("runtime")
        return self.run(*args)

    def add_shared_folder(self, vmx_path: str, share_name: str, host_path: str) -> str:
        return self.run("addSharedFolder", vmx_path, share_name, host_path)

    def remove_shared_folder(self, vmx_path: str, share_name: str) -> str:
        return self.run("removeSharedFolder", vmx_path, share_name)

    def set_shared_folder_state(
        self, vmx_path: str, share_name: str, host_path: str, writable: bool = True
    ) -> str:
        return self.run(
            "setSharedFolderState",
            vmx_path,
            share_name,
            host_path,
            "writable" if writable else "readonly",
        )

    # ---------- 通用 ----------
    def check_tools_state(self, vmx_path: str) -> str:
        return self.run("checkToolsState", vmx_path)

    def install_tools(self, vmx_path: str) -> str:
        return self.run("installTools", vmx_path)

    def upgrade_vm(self, vmx_path: str) -> str:
        return self.run("upgradevm", vmx_path)

    def clone_vm(
        self,
        vmx_path: str,
        dest_vmx_path: str,
        linked: bool = False,
        snapshot_name: str = "",
        clone_name: str = "",
    ) -> str:
        args = ["clone", vmx_path, dest_vmx_path, "linked" if linked else "full"]
        if snapshot_name:
            args.append(f"-snapshot={snapshot_name}")
        if clone_name:
            args.append(f"-cloneName={clone_name}")
        return self.run(*args, timeout=600)

    def delete_vm(self, vmx_path: str) -> str:
        return self.run("deleteVM", vmx_path)

    def download_photon_vm(self, dest_dir: str) -> str:
        return self.run("downloadPhotonVM", dest_dir, timeout=600)

    def command(
        self,
        extra_args: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
        timeout: float | None = None,
    ) -> str:
        args = shlex.split(extra_args, posix=False)
        if not args:
            return "vmrun 失败: extra_args 为空"
        return self.run(*args, guest_user=guest_user, guest_password=guest_password, timeout=timeout)

    # ---------- 底层执行 ----------
    def run(
        self,
        *args: str,
        guest_user: str | None = None,
        guest_password: str | None = None,
        timeout: float | None = None,
    ) -> str:
        cmd = [self.vmrun_path, "-T", self.host_type]
        if self._vm_password:
            cmd.extend(["-vp", self._vm_password])
        user = guest_user or self._default_guest_user
        password = guest_password or self._default_guest_password
        if user:
            # vmrun 要求 -gu 与 -gp 成对出现；空密码账户也必须传 -gp ""，否则报凭据无效
            cmd.extend(["-gu", user, "-gp", password or ""])
        cmd.extend(args)
        try:
            # vmrun 输出非纯 GBK（含 UTF-8/二进制字节），固定 utf-8 + replace 防止解码崩溃
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout if timeout is not None else self.timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return f"vmrun 超时: {' '.join(cmd)}"

        output = (result.stdout or "").strip()
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            return f"vmrun 失败({result.returncode}): {err or output}"
        return output or "OK"
