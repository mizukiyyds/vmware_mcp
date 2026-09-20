# coding: gbk

"""通过 stdio 真实启动 vmware_mcp 服务器，列出并调用工具/资源/提示词，模拟 Cursor 的连接流程。"""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    env = dict(os.environ)
    env["VMWARE_HOME"] = r"C:\Program Files\VMware\VMware Workstation"
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

            tools = await session.list_tools()
            print(f"--- tools ({len(tools.tools)}) ---")
            for t in tools.tools:
                print(f"tool: {t.name} - {t.description}")

            resources = await session.list_resources()
            print(f"--- resources ({len(resources.resources)}) ---")
            for r in resources.resources:
                print(f"resource: {r.uri} - {r.description}")

            prompts = await session.list_prompts()
            print(f"--- prompts ({len(prompts.prompts)}) ---")
            for p in prompts.prompts:
                print(f"prompt: {p.name} - {p.description}")

            result = await session.call_tool("list", {})
            for content in result.content:
                print(f"list result: {content.text!r}")

            result = await session.call_tool("list_host_networks", {})
            for content in result.content:
                print(f"list_host_networks result: {content.text!r}")

            result = await session.call_tool("get_product_info", {})
            for content in result.content:
                print(f"get_product_info result: {content.text!r}")

            result = await session.call_tool("list_registered_vms", {})
            for content in result.content:
                print(f"list_registered_vms result: {content.text!r}")

            res = await session.read_resource("vmware://vms/running")
            for content in res.contents:
                print(f"resource vmware://vms/running: {content.text!r}")

if __name__ == "__main__":
    asyncio.run(main())
