# Generic Setup Guide for Glean MCP Server

This document outlines the changes made to make the Glean MCP Server repository generic and reusable for any organization.

## Changes Made

### 1. Repository References
- **Kept**: `github.com/alankyshum/glean-mcp-server` (original author's repository)

### 2. Container Registry References
- **Kept**: `ghcr.io/alankyshum/glean-mcp-server` (original author's registry)

### 3. Example URLs
- **Before**: `https://linkedin-be.glean.com`
- **After**: `https://your-company.glean.com`

### 4. File Paths
- **Before**: `/Users/kshum/Documents/gitproj/glean-mcp-server`
- **After**: `/path/to/your/glean-mcp-server`

### 5. Copyright
- **Kept**: `Copyright (c) 2025 Alan Shum` (original author)

## Files Modified

1. **README.md** - Updated all repository URLs and container registry references
2. **src/glean_client.py** - Updated example URL in documentation
3. **.env.example** - Updated example Glean URL
4. **docker-compose.yml** - Updated container registry reference in comments
5. **scripts/run-glean-mcp.sh** - Updated hardcoded path to generic placeholder
6. **glean-mcp-server.code-workspace** - Updated Docker registry path
7. **LICENSE** - Updated copyright to be generic

## Setup Instructions for New Users

### 1. Fork or Clone the Repository
```bash
git clone https://github.com/your-username/glean-mcp-server.git
cd glean-mcp-server
```

### 2. Use the Original Repository
This repository is maintained by alankyshum and can be used directly:
- Fork the repository if you want to make modifications
- Use the pre-built images from `ghcr.io/alankyshum/glean-mcp-server`
- Or build your own images using the provided Dockerfile

### 3. Configure Your Glean Instance
```bash
cp .env.example .env
# Edit .env with your Glean instance details
```

### 4. Update GitHub Actions (if using)
The GitHub Actions workflow will automatically use your repository name via `${{ github.repository }}`, so no changes needed there.

### 5. Update Script Paths
Edit `scripts/run-glean-mcp.sh` and update the `GLEAN_MCP_DIR` variable to point to your actual installation path.

## Environment Variables to Configure

| Variable | Example | Description |
|----------|---------|-------------|
| `GLEAN_BASE_URL` | `https://acme.glean.com` | Your organization's Glean instance URL |
| `GLEAN_COOKIES` | `session=abc123...` | Authentication cookies from your browser |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `GLEAN_DEFAULT_PAGE_SIZE` | `14` | Default number of search results |
| `GLEAN_DEFAULT_SNIPPET_SIZE` | `215` | Default snippet length |

## Getting Authentication Cookies

1. Open your browser and navigate to your Glean instance
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Perform a search in Glean
5. Find a search API request (usually to `/api/v1/search`)
6. Copy the entire `Cookie` header value
7. Paste it as the `GLEAN_COOKIES` value in your `.env` file

## Container Registry Setup

If you want to publish to your own GitHub Container Registry:

1. Fork the repository to your GitHub account
2. Ensure GitHub Actions has write permissions to packages
3. The workflow will automatically publish to `ghcr.io/your-username/glean-mcp-server`
4. Update any references in your documentation to use your registry path

## Security Considerations

- Never commit your `.env` file with real credentials
- Rotate your authentication cookies regularly
- Use GitHub secrets for sensitive values in CI/CD
- Consider implementing token refresh mechanisms for production use

## Support

This is now a generic template. For support:
- Check the original repository for updates
- Create issues in your forked repository
- Refer to Glean's official API documentation
- Test thoroughly with your specific Glean instance
