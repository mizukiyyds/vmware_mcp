# vmware_mcp

通过 MCP（Model Context Protocol）管理本机 VMware Workstation 虚拟机的 server。面向 **Workstation 26H1**（26.0.0），封装官方命令行工具 **vmrun** 和 **vmcli**，供 Cursor 等 MCP 客户端中的 AI Agent 调用。

- **6 个工具**、0 个 resource、0 个 prompt
- 参照 [HexRays ida-mcp](https://github.com/HexRaysSA/ida-mcp) 的 **Code Mode** 设计（[博客说明](https://hex-rays.com/blog/hex-rays-ida-mcp-server)）：不给每个操作配一个工具（旧版 48 个工具的 schema 会大量占用上下文窗口，且工具间不可组合），而是让 agent 用 `reference` 按需查命令用法、用 `execute` 组合任意 vmrun/vmcli 命令

## 工具一览

| 工具 | 说明 |
|------|------|
| `list_vms` | 列出虚拟机：运行中的 + 虚拟机库全部（含关机/暂停），标注当前选中 VM |
| `select_vm` | 选中当前虚拟机（vmx 路径），之后 `execute` 里用 `{vm}` 指代；传空串取消选中 |
| `execute` | 执行任意 vmrun/vmcli 命令。`-T ws`、加密 VM 密码、客户机登录信息自动注入 |
| `reference` | 关键词检索 vmrun/vmcli 命令用法与注意事项（内置笔记 + 实时帮助） |
| `set_guest_credentials` | 设置客户机登录用户名/密码（也可在 mcp.json 的 env 一次配好） |
| `get_product_info` | 查看本机 Workstation 版本与 vmrun/vmcli 是否可用 |

`execute` 示例：

```
execute("vmrun", "listSnapshots {vm} showTree")
execute("vmrun", "start {vm} nogui")
execute("vmrun", "runProgramInGuest {vm} -noWait C:\Windows\System32\cmd.exe /c ""whoami > C:\t.txt""")
execute("vmrun", "CopyFileFromGuestToHost {vm} C:\t.txt D:\t.txt")
execute("vmcli", "{vm} Power query")          # vmcli 形态：vmcli.exe [<vmx>] <模块> <命令> [参数]
execute("vmcli", "{vm} Disk query")
execute("vmrun", "listHostNetworks")           # 无需 vm 的命令不用占位符
execute("vmrun", "clone {vm} D:\vm\copy.vmx full", timeout=600)
```

不确定命令写法时先查：`reference("快照")`、`reference("runProgramInGuest")`、`reference("Disk")`。

## 环境要求

- Windows，已安装 VMware Workstation 26H1（需含 `vmrun.exe`、`vmcli.exe`）
- Python >= 3.10
- 客户机内操作依赖 VMware Tools；登录信息在启动时通过环境变量传入

未设置 `VMWARE_HOME` 时，会自动尝试默认安装目录 `C:\Program Files\VMware\VMware Workstation`。加密虚拟机可另设 `VMWARE_VM_PASSWORD`。

## 安装

```bash
pip install -e ./code
```

## 在 Cursor 中使用

Cursor 启动时会按 `mcp.json` 自动拉起本 server（stdio 方式），无需常驻进程。

编辑全局配置 `%USERPROFILE%\.cursor\mcp.json`（`command` 必须用 python.exe 的绝对路径），参考 `code/vmware_mcp/mcp.json`：

```json
{
  "mcpServers": {
    "vmware": {
      "command": "C:\\Users\\<用户名>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["-m", "vmware_mcp.server"],
      "env": {
        "VMWARE_HOME": "C:\\Program Files\\VMware\\VMware Workstation",
        "VMWARE_GUEST_USER": "<客户机用户名，可选>",
        "VMWARE_GUEST_PASSWORD": "<客户机密码，可选>"
      }
    }
  }
}
```

环境变量说明：

| 变量 | 必填 | 说明 |
|------|------|------|
| `VMWARE_HOME` | 否 | VMware 安装目录；不填则尝试 `C:\Program Files\VMware\VMware Workstation` |
| `VMWARE_GUEST_USER` | 客户机操作时要 | 客户机登录用户名，启动时一次传入 |
| `VMWARE_GUEST_PASSWORD` | 客户机操作时要 | 客户机登录密码；空密码账户填 `""` |
| `VMWARE_VM_PASSWORD` | 否 | 加密虚拟机的密码（对应 vmrun `-vp`） |
| `VMWARE_HOST_TYPE` | 否 | vmrun `-T` 类型，默认 `ws` |
| `VMWARE_INVENTORY` | 否 | 虚拟机库清单路径，默认 `%APPDATA%\VMware\inventory.vmls` |

客户机登录信息只在启动时传入（mcp.json 的 env）。要换账号调 `set_guest_credentials`。密码以明文放在 mcp.json 中，介意请留空并改用 `set_guest_credentials`。

**修改代码或配置后需重启 Cursor（或在 MCP 设置中刷新该 server）才生效。**

## 验证

```bash
# 列出全部工具并做真实调用（模拟 Cursor 连接流程）
python code/tests/test_stdio_client.py
# 检查工具参数的 schema 描述
python code/tests/test_tool_schema.py
```

## 项目结构

```
code/vmware_mcp/   MCP server 包
                   server.py     注册层（6 个工具，Code Mode 工具面）
                   reference.py  reference 工具：内置笔记 + vmrun/vmcli 实时帮助检索
                   vmrun.py      vmrun 封装层（库层，含全部命令方法与底层 run）
                   vmcli.py      vmcli 封装层（库层，含全部模块方法与底层 run）
                   mcp.json      配置模板
code/tests/        stdio 客户端验证脚本与手工场景脚本
code/guest-config/ 客户机侧辅助脚本
document/          Workstation 26H1 命令对照说明
```

旧版 48 个一对一工具的注册层已移除；vmrun.py / vmcli.py 库层保留全部命令方法，`execute` 与手工脚本（`tests/test_guest_cmd.py` 等）直接复用。

本地工作区目录（`blocker/`、`conclusion/`、`data/`、`picture/` 等）保留在本机，不上传本仓库。
