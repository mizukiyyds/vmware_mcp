# coding: gbk

"""读取 Workstation 虚拟机库清单（inventory.vmls）。"""

from __future__ import annotations

import os
import re
from pathlib import Path

_ENV_INVENTORY = "VMWARE_INVENTORY"
_VM_KEY = re.compile(r"^vmlist(\d+)\.(\w+)\s*=\s*\"(.*)\"\s*$")


def inventory_path() -> Path:
    override = (os.environ.get(_ENV_INVENTORY) or "").strip()
    if override:
        return Path(override)
    appdata = os.environ.get("APPDATA") or ""
    if not appdata:
        raise RuntimeError("无法定位 APPDATA，无法读取虚拟机库清单")
    return Path(appdata) / "VMware" / "inventory.vmls"


def list_registered_vms() -> str:
    path = inventory_path()
    if not path.is_file():
        return f"未找到虚拟机库清单: {path}"

    encoding = _detect_encoding(path)
    text = path.read_text(encoding=encoding, errors="replace")
    records: dict[str, dict[str, str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        match = _VM_KEY.match(line)
        if not match:
            continue
        index, field, value = match.group(1), match.group(2), match.group(3)
        records.setdefault(index, {})[field] = value

    items = []
    for index in sorted(records, key=lambda x: int(x)):
        rec = records[index]
        vmx = rec.get("config", "")
        if not vmx:
            continue
        name = rec.get("DisplayName") or Path(vmx).stem
        state = rec.get("State") or "unknown"
        items.append(f"name={name}\tstate={state}\tvmx={vmx}")

    if not items:
        return f"虚拟机库为空: {path}"
    return f"{len(items)} registered VM(s) ({path})\n" + "\n".join(items)


def _detect_encoding(path: Path) -> str:
    head = path.read_bytes()[:200]
    try:
        preview = head.decode("utf-8")
    except UnicodeDecodeError:
        preview = head.decode("gbk", errors="ignore")
    match = re.search(r'\.encoding\s*=\s*"([^"]+)"', preview)
    if match:
        declared = match.group(1).strip()
        if declared.upper() in {"GBK", "GB2312", "GB18030", "CP936"}:
            return "gbk"
        if declared.upper() in {"UTF-8", "UTF8"}:
            return "utf-8"
        return declared
    return "gbk"
