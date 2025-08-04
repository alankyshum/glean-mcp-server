# 🚀 Introducing Glean MCP Server for VS Code/Cursor!

Hey team! I've been working with a Glean MCP (Model Context Protocol) server that lets you search our company knowledge base directly from VS Code/Cursor. Here are two ways to get it running:

## Option 1: Official Glean MCP Server 🏢

- Use the official `@gleanwork/glean-mcp-server` package with API token authentication
- Requires admin rights through the `#glean-support` Slack channel to enable the Remote MCP Server feature and get API tokens
- **Setup command**: `npx -y @gleanwork/configure-mcp-server --client vscode --instance <your-instance> --token <your-token>`
- **Documentation**: [Glean Remote MCP Server - Customer FAQs](https://docs.google.com/document/d/1AgALuyqwfUPBcjCNHRjmfZ-YktgimzuP3pe4aHFJt0U/edit?tab=t.0#heading=h.qcxcq2l17l8e)

**Sample Configuration** (for manual setup in `~/.cursor/mcp.json` or VS Code settings):
```json
{
  "mcpServers": {
    "glean-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@gleanwork/glean-mcp-server",
        "--instance", "your-company-name",
        "--token", "your-api-token-here"
      ]
    }
  }
}
```

- **Pros**: Much longer session TTL (no frequent renewals needed), official support, access to Glean agents
- **Cons**: Need to wait for admin approval and API token provisioning

## Option 2: This Unofficial MCP Server ⚡

- Uses cookies from your current Glean session - no admin rights needed!
- **Documentation**: [Glean MCP Server Setup Guide](https://github.com/alankyshum/glean-mcp-server/blob/main/README.md)
- **Pros**: Get up and running in minutes, perfect for trying out MCP today
- **Cons**: Need to renew cookies weekly (~60 seconds using the included scripts)

## What You Get with Both Options

- Direct search of company docs, wikis, and internal resources
- AI-powered research queries using Glean's chat functionality
- Seamless integration with your coding workflow

## Getting Started

This unofficial version is great for getting your first taste of MCP and seeing how powerful it is to have our company knowledge right in your coding environment. The server includes helpful cookie renewal scripts and clear error messages to guide you through the process.

Ready to try it? The unofficial version is perfect for a quick start - you can literally be searching our knowledge base from VS Code in under 5 minutes! 🎯

---

*Need help getting started? Check out the [setup documentation](https://github.com/alankyshum/glean-mcp-server/blob/main/README.md) or reach out in the team chat!*
