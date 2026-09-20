# vmware_mcp

通过 MCP（Model Context Protocol）管理本机 VMware Workstation 虚拟机的 server。面向 **Workstation 26H1**（26.0.0），封装官方命令行工具 **vmrun** 和 **vmcli**，供 Cursor 等 MCP 客户端中的 AI Agent 调用。

- 48 个工具、4 个 resource、0 个 prompt

- 电源、快照、客户机命令与文件传输、共享文件夹、宿主网络与端口转发
- 建机/模板、CPU/内存/磁盘/NVMe/SATA/串口、vmx 配置读写
- MKS 键鼠屏幕（26H1 的 vmcli MKS 没有鼠标事件命令）
- 虚拟机库清单（含关机虚拟机）、产品版本查询
- 未单独封装的命令可通过 `vmrun_command` / `vmcli_command` 直接调用

## 环境要求

- Windows，已安装 VMware Workstation 26H1（默认路径 `C:\Program Files\VMware\VMware Workstation`，需含 `vmrun.exe`、`vmcli.exe`）
- Python >= 3.10
- 客户机内操作依赖 VMware Tools；登录信息在启动时通过环境变量传入

未设置 `VMWARE_HOME` 时，会自动尝试默认安装目录。加密虚拟机可另设 `VMWARE_VM_PASSWORD`。

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
# 列出全部工具/资源/提示词并做真实调用（模拟 Cursor 连接流程）
python code/tests/test_stdio_client.py
# 检查工具参数的 schema 描述
python code/tests/test_tool_schema.py
```

## 项目结构

```
code/vmware_mcp/   MCP server 包（server.py 注册层，vmrun.py / vmcli.py 封装层，mcp.json 配置模板）
code/tests/        stdio 客户端验证脚本
code/guest-config/ 客户机侧辅助脚本
document/          Workstation 26H1 命令对照说明
```

本地工作区目录（`blocker/`、`conclusion/`、`data/`、`picture/` 等）按 AGENTS.md 分类保留在本机，不上传本仓库。
