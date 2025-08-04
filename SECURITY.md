# 🔒 Security Guide - Glean MCP Server

Simple security guidance for the Glean MCP Server.

## 🔐 Security Features

The Glean MCP Server includes essential security features:

### ✅ HTTPS Enforcement
- **Secure Communication**: All connections to Glean servers use HTTPS
- **Automatic Validation**: Server rejects non-HTTPS URLs  
- **Industry Standard**: Follows security best practices

### 📋 MCP Configuration Security
- **Industry Standard**: Plaintext credentials in local MCP configs (like other MCP servers)
- **Local Security**: Protected by your system's user account security
- **Simple Setup**: No complex encryption for local development use

## 🛠️ Configuration

### Environment Variables

**Required:**
- `GLEAN_BASE_URL`: Your Glean instance URL (must use HTTPS)
- `GLEAN_COOKIES`: Authentication cookies from your browser

**Optional:**
- `GLEAN_TOOL_DESCRIPTION`: Custom tool description
- `GLEAN_AUTO_OPEN_BROWSER`: Browser auto-open setting

### MCP Configuration Example

```json
{
  "mcp": {
    "mcpServers": {
      "glean": {
        "command": "docker",
        "args": [
          "run", "--rm", "-i", "--pull", "always",
          "-e", "GLEAN_BASE_URL",
          "-e", "GLEAN_COOKIES",
          "ghcr.io/alankyshum/glean-mcp-server:latest"
        ],
        "env": {
          "GLEAN_BASE_URL": "https://your-company-be.glean.com",
          "GLEAN_COOKIES": "your_cookies_here"
        }
      }
    }
  }
}
```

## 🚨 Incident Response

### If Credentials Are Compromised

1. **Immediately revoke** the compromised credentials in Glean admin panel
2. **Generate new** credentials from your browser
3. **Update** all MCP configurations with new credentials
4. **Restart** your editor to pick up the new configuration

## ✅ Security Checklist

Before deploying:

- [ ] Valid Glean credentials are configured
- [ ] HTTPS-only URLs are configured (enforced automatically)
- [ ] Regular security updates are scheduled

## 📞 Security Support

For security questions:

1. **Check** this documentation first
2. **Open an issue** on GitHub for questions
3. **Contact** maintainers for sensitive security issues

---

*This security guide covers the essential security features of the Glean MCP Server.*
