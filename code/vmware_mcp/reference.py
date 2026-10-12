"""vmrun/vmcli 用法参考：内置注意事项 + 实时帮助缓存 + 关键词检索。

对应 ida-mcp 的 reference 工具：agent 不需要每个命令一个工具，
按需用关键词查文档，再用 execute 组合调用。
"""

from __future__ import annotations

import subprocess

from .paths import resolve_vmware_home

_TIMEOUT = 15

# 内置注意事项（从 document/vmware-26h1-cli.md 与实测经验提炼，按空行分块便于检索）
_NOTES = """【客户机认证】
客户机操作（runProgramInGuest、文件复制、listProcessesInGuest 等 Guest 类命令）需要客户机登录信息。
在 mcp.json 的 env 里配置 VMWARE_GUEST_USER / VMWARE_GUEST_PASSWORD，或调用 set_guest_credentials。
vmrun 的 -gu 与 -gp 必须成对出现；空密码账户也要传 -gp ""（已由本 server 自动处理）。
vmcli 的 Guest 模块认证是 -u/-p，跟在命令参数之后（同样自动处理）。

【runProgramInGuest 取回输出】
vmrun runProgramInGuest 不返回程序 stdout。让程序把输出写到客户机文件，
再用 CopyFileFromGuestToHost 捞回宿主机读取。
cmd 场景参数整串传递：/c "whoami > C:\\mcp_test\\out.txt"（引号是参数的一部分，不要拆开）。

【GUI 程序】
客户机里运行 GUI 程序必须加 -interactive 才会显示在用户桌面，program 直接给完整路径
（如 C:\\Windows\\System32\\calc.exe）。不要用 cmd /c start 启动 GUI（引号会被错误切分）。

【截屏与键盘鼠标】
vmrun captureScreen 保存屏幕截图到宿主机文件。vmrun typeKeystrokesInGuest 发送按键。
vmcli MKS 模块可 captureScreenshot / sendKeySequence / sendKeyEvent。
注意：26H1 的 MKS 模块没有 sendMouseEvent，无 Tools 时不能发送鼠标事件。

【建机与挂盘顺序】
1. vmcli VM Create 只生成 vmx，不含磁盘
2. vmcli Disk Create 只生成 vmdk 文件
3. vmcli Disk SetPresent 启用槽位（如 scsi0:0 或 nvme0:0）
4. vmcli Disk SetBackingInfo 把槽位绑到 vmdk
5. 需要 NVMe/SATA 控制器时先 Nvme query / Sata query，必要时 SetPresent

【电源与快照】
vmrun start/stop/reset/suspend 带 [gui|nogui]、[hard|soft] 参数；soft 依赖 VMware Tools。
vmrun list 只能看到运行中的 VM；查关机/暂停状态用 vmcli Power query。
vmrun snapshot/deleteSnapshot/revertToSnapshot/listSnapshots；需要快照说明或保存内存时用
vmcli Snapshot Take -m -d "说明" <名称>。revertToSnapshot 后 VM 处于关机状态，需重新 start。

【共享文件夹】
vmrun addSharedFolder/removeSharedFolder/enableSharedFolders。
客户机中经 \\\\vmware-host\\Shared Folders\\<名称> 访问。
运行时状态查询用 vmcli HGFS query（需要 VM 处于运行状态）。

【宿主网络与端口转发】
vmrun listHostNetworks 列出 vmnet0/vmnet1/vmnet8 等。
listPortForwardings/setPortForwarding/deletePortForwarding 管理 NAT 端口转发。
客户机 IP 用 vmrun getGuestIPAddress（-wait 阻塞等待）。

【加密虚拟机与其他】
加密虚拟机密码通过环境变量 VMWARE_VM_PASSWORD 传入（对应 vmrun -vp）。
克隆：vmrun clone <源vmx> <目标vmx> linked|full [-snapshot=名称] [-cloneName=名称]（较慢，建议 timeout 600）。
vmrest 提供 REST API，但需先 -C 配置凭据并常驻监听，本 server 未封装。
低频 vmcli 选项（Disk SetBandwidthCap、Ethernet SetSecurityPolicy、VProbes 全套等）都可直接经 execute 调用。"""

_cache: dict[str, str] = {}


def _run_exe(exe: str, args: list[str]) -> str:
    try:
        home = resolve_vmware_home()
    except RuntimeError as exc:
        return f"（无法定位 VMware 安装目录: {exc}）"
    try:
        result = subprocess.run(
            [str(home / exe), *args],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        return f"（调用 {exe} 失败: {exc}）"
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def _cached(key: str, exe: str, args: list[str]) -> str:
    if key not in _cache:
        _cache[key] = _run_exe(exe, args)
    return _cache[key]


def _vmrun_help() -> str:
    return _cached("vmrun", "vmrun.exe", [])


def _vmcli_modules() -> str:
    return _cached("vmcli-modules", "vmcli.exe", ["--help"])


def _vmcli_module_help(module: str) -> str:
    return _cached(f"vmcli-{module.lower()}", "vmcli.exe", [module, "--help"])


def _vmcli_module_names() -> list[str]:
    text = _vmcli_modules()
    marker = "Available modules:"
    if marker not in text:
        return []
    names = []
    for line in text.split(marker, 1)[1].splitlines():
        line = line.strip()
        if line and not line.startswith("-") and " " not in line and line[0].isupper():
            names.append(line)
    return names


def _blocks(text: str) -> list[str]:
    return [b.strip() for b in text.split("\n\n") if b.strip()]


def _search(text: str, terms: list[str]) -> list[str]:
    hits = []
    for block in _blocks(text):
        low = block.lower()
        if any(t in low for t in terms):
            hits.append(block)
    return hits


def search_reference(query: str) -> str:
    """按关键词检索内置注意事项、vmrun 用法、vmcli 模块帮助。"""
    query = (query or "").strip()
    if not query:
        modules = "、".join(_vmcli_module_names()) or "（未能获取）"
        return (
            "reference(query) 用法：输入关键词（中英文均可），返回相关的命令用法与注意事项。\n"
            "可检索的内容：\n"
            "1. 内置注意事项：客户机认证、runProgramInGuest、GUI 程序、截屏键盘、"
            "建机挂盘、电源快照、共享文件夹、端口转发、加密虚拟机、克隆\n"
            "2. vmrun 全部命令用法（POWER / SNAPSHOT / GUEST / 网络 / 共享文件夹等）\n"
            f"3. vmcli 模块帮助：{modules}\n"
            "示例：reference(\"快照\")、reference(\"runProgramInGuest\")、reference(\"Disk\")"
        )

    terms = [t.lower() for t in query.split() if t.strip()]
    sections: list[str] = []

    notes_hits = _search(_NOTES, terms)
    if notes_hits:
        sections.append("===== 内置注意事项 =====\n" + "\n\n".join(notes_hits))

    vmrun_hits = _search(_vmrun_help(), terms)
    if vmrun_hits:
        sections.append("===== vmrun 用法 =====\n" + "\n\n".join(vmrun_hits))

    cli_hits = _search(_vmcli_modules(), terms)
    for module in _vmcli_module_names():
        help_text = _vmcli_module_help(module)
        hits = _search(help_text, terms)
        if hits:
            cli_hits.extend(hits)
    if cli_hits:
        # 去重并保持顺序
        seen: set[str] = set()
        unique = [b for b in cli_hits if not (b in seen or seen.add(b))]
        sections.append("===== vmcli 帮助 =====\n" + "\n\n".join(unique))

    if not sections:
        return f"未找到与 {query!r} 相关的内容。试试更短的关键词，或空调用 reference() 查看可检索主题。"
    return "\n\n".join(sections)
