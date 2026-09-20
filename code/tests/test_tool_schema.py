# coding: gbk

"""检查 MCP 工具的 inputSchema：确认参数是否有描述信息。"""

import asyncio
import json
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
            await session.initialize()
            tools = await session.list_tools()
            for name in ("start", "set_port_forwarding", "run_program_in_guest", "list_disks"):
                t = next(t for t in tools.tools if t.name == name)
                print(f"===== {name} =====")
                print(f"description: {t.description}")
                print(json.dumps(t.input_schema, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
