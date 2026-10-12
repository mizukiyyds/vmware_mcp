# VMware Workstation 26H1 命令与 MCP 对照

本机产品：VMware Workstation 26.0.0 build-25388281，安装目录 `C:\Program Files\VMware\VMware Workstation`。
MCP 已去掉 OVF/OVA 导入导出工具（backup/ovftool.py），以及脱机磁盘整理/转换/修复工具（backup/vdisk.py）。
0.4.0 起参照 HexRays ida-mcp 的 Code Mode 设计重构：48 个一对一工具精简为 6 个
（list_vms / select_vm / execute / reference / set_guest_credentials / get_product_info），
所有命令一律经 `execute` 调用，用法用 `reference` 检索。

## 命令行工具

| 工具 | 版本线索 | 用途 |
|------|----------|------|
| vmrun.exe | 1.17.0.25388281 | 电源、快照、客户机操作、共享文件夹、宿主网络 |
| vmcli.exe | 0.1.25388281 | 建机、芯片组、磁盘/网卡/NVMe/SATA/串口、MKS、HGFS、模板 |
| vmrest.exe | 1.3.1 25388281 | REST API（需先 `-C` 配置凭据并常驻监听，本 MCP 未封装为服务） |

vmrun 调用时固定加上 `-T ws`。加密虚拟机通过环境变量 `VMWARE_VM_PASSWORD` 传 `-vp`。

## vmrun：命令覆盖情况

电源、快照、全部客户机文件/进程命令、共享文件夹、端口转发、clone/deleteVM 均可直接经 `execute` 调用，包括 26H1 帮助里较晚补上的：

- `typeKeystrokesInGuest`
- `connectNamedDevice` / `disconnectNamedDevice`
- `downloadPhotonVM`
- `runProgramInGuest` / `runScriptInGuest` 的 `-activeWindow`（以及脚本侧的 `-interactive` / `-noWait`）
- `CreateTempfileInGuest`（更完整的临时文件也可用 vmcli Guest createTempFile/createTempDir）

## vmcli 模块

26H1 提供：Chipset、ConfigParams、Disk、Ethernet、Guest、HGFS、MKS、Nvme、Power、Sata、Serial、Snapshot、Tools、VM、VMTemplate、VProbes。

全部模块命令都可经 `execute` 调用（形如 `execute("vmcli", "{vm} Disk query")`）。低频选项不再一一说明，用 `reference("模块名")` 查实时帮助，例如：

- Disk：SetBandwidthCap、SetShares、ConvertAllocType、Branch 等
- Ethernet：SetAddressType、SetSecurityPolicy、SetWakeOnPcktRcv 等
- VProbes 全套（调试探针）

注意：26H1 的 **MKS 模块没有 sendMouseEvent**。无 Tools 时只能发键盘和截屏，不能发鼠标。

## REST API（vmrest）未做成 MCP 工具的原因

`swagger_WS.json` 中的路径包括：虚拟机库列表/注册、电源、共享文件夹、网卡、IP、端口转发、MAC-to-IP、创建 vmnet。与 vmrun/vmcli 能力大量重叠，且必须先配置凭据并保持 `vmrest` 进程监听。清单列表已改为直接读 `%APPDATA%\VMware\inventory.vmls`。

若以后要接 REST，可单独加一层，不要替换现有 CLI 工具。

## 建机与挂盘顺序

1. `vmcli VM Create` 只生成 vmx，不含磁盘
2. `vmcli Disk Create` 只生成 vmdk 文件
3. `vmcli Disk SetPresent` 启用槽位（如 `scsi0:0` 或 `nvme0:0`）
4. `vmcli Disk SetBackingInfo` 把槽位绑到 vmdk
5. 需要 NVMe/SATA 控制器时先 `vmcli Nvme query` / `vmcli Sata query`，必要时 `SetPresent`
