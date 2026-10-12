# vmware_mcp

一个 MCP server：让 AI Agent 通过 **vmrun** / **vmcli** 命令行管理本机 VMware Workstation 虚拟机。

参照 [HexRays ida-mcp](https://github.com/HexRaysSA/ida-mcp) 的 Code Mode 设计，只暴露 **6 个工具**（0 resource、0 prompt），不为一一操作各配一个工具，减少上下文占用；agent 用 `reference` 查命令用法，用 `execute` 组合执行任意 vmrun/vmcli 命令。

## 工具

| 工具 | 说明 |
|------|------|
| `list_vms` | 列出虚拟机（运行中的 + 虚拟机库全部），标注当前选中 |
| `select_vm` | 选中当前虚拟机（vmx 路径），之后 `execute` 里用 `{vm}` 指代 |
| `execute` | 执行任意 vmrun/vmcli 命令；`-T ws`、加密 VM 密码、客户机登录信息自动注入 |
| `reference` | 关键词检索 vmrun/vmcli 命令用法与注意事项 |
| `set_guest_credentials` | 设置客户机登录用户名/密码 |
| `get_product_info` | 查看 Workstation 版本与 vmrun/vmcli 是否可用 |

示例：

```
execute("vmrun", "start {vm} nogui")
execute("vmrun", "listSnapshots {vm} showTree")
execute("vmrun", "runProgramInGuest {vm} -noWait C:\Windows\System32\cmd.exe /c whoami")
execute("vmcli", "{vm} Power query")        # vmcli 形态：[<vmx>] <模块> <命令> [参数]
execute("vmrun", "listHostNetworks")         # 无需 VM 的命令不用占位符
```

不确定命令写法先查：`reference("快照")`、`reference("runProgramInGuest")`。

## 环境要求

- Windows + VMware Workstation（需含 `vmrun.exe`；`vmcli.exe` 为 17.6+ 自带，部分功能依赖它）
- Python ≥ 3.10
- 客户机内操作需要客户机已装 VMware Tools

## 安装

```bash
pip install -e ./code
```

## 配置 MCP 客户端

在客户端的 MCP 配置中加入（stdio 方式，客户端按需自动拉起，无需常驻进程）：

```json
{
  "mcpServers": {
    "vmware": {
      "command": "C:\\path\\to\\python.exe",
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

适用于任何支持 stdio MCP 的客户端（Cursor、Claude Code、Kimi Code 等），配置字段相同。

环境变量：

| 变量 | 必填 | 说明 |
|------|------|------|
| `VMWARE_HOME` | 否 | VMware 安装目录；不填则尝试 `C:\Program Files\VMware\VMware Workstation` |
| `VMWARE_GUEST_USER` / `VMWARE_GUEST_PASSWORD` | 客户机操作时要 | 客户机登录信息；空密码账户填 `""`，也可运行时用 `set_guest_credentials` 设置 |
| `VMWARE_VM_PASSWORD` | 否 | 加密虚拟机的密码（对应 vmrun `-vp`） |
| `VMWARE_HOST_TYPE` | 否 | vmrun `-T` 类型，默认 `ws` |
| `VMWARE_INVENTORY` | 否 | 虚拟机库清单路径，默认 `%APPDATA%\VMware\inventory.vmls` |

密码以明文写在配置里，介意就留空，改用 `set_guest_credentials`。修改代码或配置后需重启客户端（或刷新该 MCP server）才生效。

## 验证

```bash
python code/tests/test_stdio_client.py   # 列出工具并做真实调用
python code/tests/test_tool_schema.py    # 检查工具 schema
```

## 项目结构

```
code/vmware_mcp/   server.py     6 个工具的注册层
                   reference.py  reference 工具实现
                   vmrun.py      vmrun 封装（库层，含全部命令方法）
                   vmcli.py      vmcli 封装（库层，含全部模块方法）
code/tests/        验证脚本与手工场景脚本
document/          命令对照说明
```
