# TDPilot

AI copilot for TouchDesigner — 27 tools for full live control via MCP.

## Quick start

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "npx",
      "args": ["-y", "tdpilot"]
    }
  }
}
```

That's it. On first run it installs `uv` and downloads the server automatically.

For full docs, setup guides, and the .tox component: **[github.com/dreamrec/touchdesigner-mcp](https://github.com/dreamrec/touchdesigner-mcp)**
