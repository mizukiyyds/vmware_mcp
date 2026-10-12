"""通过 stdio 真实启动 vmware_mcp 服务器，列出并调用工具，模拟 Cursor 的连接流程。"""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    env = dict(os.environ)
    env.setdefault("VMWARE_HOME", r"D:\software\VMware")
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])

    params = StdioServerParameters(
        command="python",
        args=["-m", "vmware_mcp.server"],
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            print(f"server: {init_result.server_info.name} {init_result.server_info.version}")
            print(f"instructions: {init_result.instructions}")

            tools = await session.list_tools()
            print(f"--- tools ({len(tools.tools)}) ---")
            for t in tools.tools:
                print(f"tool: {t.name} - {t.description}")
            assert len(tools.tools) == 6, f"应为 6 个工具，实际 {len(tools.tools)}"

            result = await session.call_tool("get_product_info", {})
            for content in result.content:
                print(f"get_product_info result:\n{content.text}")

            result = await session.call_tool("list_vms", {})
            for content in result.content:
                print(f"list_vms result:\n{content.text}")

            result = await session.call_tool("reference", {"query": "快照"})
            for content in result.content:
                print(f"reference(快照) result:\n{content.text}")

            result = await session.call_tool("execute", {"tool": "vmrun", "args": "list"})
            for content in result.content:
                print(f"execute(vmrun list) result:\n{content.text}")

            result = await session.call_tool("execute", {"tool": "vmrun", "args": "listSnapshots {vm}"})
            for content in result.content:
                print(f"execute(未选中 VM) result:\n{content.text}")


if __name__ == "__main__":
    asyncio.run(main())
