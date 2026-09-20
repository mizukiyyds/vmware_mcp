# coding: gbk

"""定位本机 VMware Workstation 安装目录与常用可执行文件。"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_ENV_HOME = "VMWARE_HOME"

_DEFAULT_HOMES = (
    Path(r"C:\Program Files\VMware\VMware Workstation"),
)


def resolve_vmware_home() -> Path:
    """优先使用环境变量 VMWARE_HOME；未设置时再试 Workstation 默认安装路径。"""
    env = (os.environ.get(_ENV_HOME) or "").strip()
    if env:
        home = Path(env)
        if (home / "vmrun.exe").is_file():
            return home
        raise RuntimeError(
            f"vmrun.exe 不存在: {home / 'vmrun.exe'}（检查 {_ENV_HOME} 配置）"
        )
    for home in _DEFAULT_HOMES:
        if (home / "vmrun.exe").is_file():
            return home
    raise RuntimeError(
        f"未设置环境变量 {_ENV_HOME}，且未在常见安装路径找到 vmrun.exe。"
        "请在 mcp.json 的 env 中配置 VMware 安装目录，例如 "
        r"C:\Program Files\VMware\VMware Workstation"
    )


def require_exe(home: Path, name: str) -> Path:
    path = home / name
    if not path.is_file():
        raise RuntimeError(f"{name} 不存在: {path}（检查 {_ENV_HOME} 配置）")
    return path


def product_info() -> str:
    """汇总本机 Workstation 版本与命令行工具是否可用。"""
    home = resolve_vmware_home()
    lines = [f"VMWARE_HOME={home}"]

    vmware_exe = home / "vmware.exe"
    if vmware_exe.is_file():
        ver = _file_version(vmware_exe)
        if ver:
            lines.append(f"vmware.exe={ver}")
        else:
            lines.append(f"vmware.exe={vmware_exe}")

    for name, args in (
        ("vmrun.exe", []),
        ("vmcli.exe", ["--version"]),
        ("vmrest.exe", ["-v"]),
    ):
        path = home / name
        if not path.is_file():
            lines.append(f"{name}=未找到")
            continue
        text = _run_version(path, args)
        lines.append(f"{name}={text or '已安装'}")

    return "\n".join(lines)


def _file_version(path: Path) -> str:
    try:
        import win32api

        trans = win32api.GetFileVersionInfo(str(path), "\\VarFileInfo\\Translation")
        lang, codepage = trans[0]
        key = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileVersion"
        value = win32api.GetFileVersionInfo(str(path), key)
        return str(value).strip() if value else ""
    except Exception:
        return ""


def _run_version(path: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            [str(path), *args],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        return f"调用失败: {exc}"
    text = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first[:200]
