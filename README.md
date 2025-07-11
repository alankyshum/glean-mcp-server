# Glean MCP Server

A Model Context Protocol (MCP) server that provides search functionality for Glean knowledge bases in Cursor and VS Code.

## ✨ Key Features

- **Optimized Responses**: Advanced filtering reduces response size by 85-98% while preserving all useful information
- **Fast Search**: Efficient search across your company's knowledge base
- **Easy Setup**: Simple Docker-based deployment with environment variable configuration
- **Flexible Configuration**: Customizable page sizes, snippet lengths, and tool descriptions

## Quick Setup for Cursor/VS Code

### 1. Get Authentication Cookies

1. Open your browser and navigate to your Glean instance (e.g., `https://company.glean.com`)
2. Make sure you're logged in
3. Open Developer Tools (F12) → Network tab
4. Perform a search in Glean to trigger API requests
5. Find any search API request in the Network tab
6. Right-click the request → Copy → Copy as cURL
7. Extract the entire `Cookie` header value from the cURL command

### 2. Configure MCP in Cursor/VS Code

Add this to your MCP settings file (see `mcp-settings-example.json` for reference):

**For Cursor:** `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`

**For VS Code:** `~/.vscode/settings.json` (add to existing file)

```json
{
  "mcp": {
    "mcpServers": {
      "glean": {
        "command": "docker",
        "args": [
          "run", "--rm", "-i",
          "--pull", "always",
          "-e", "GLEAN_BASE_URL=https://your-company.glean.com",
          "-e", "GLEAN_COOKIES=your_cookie_string_here",
          "ghcr.io/alankyshum/glean-mcp-server:latest"
        ]
      }
    }
  }
}
```

**Replace:**
- `your-company.glean.com` with your actual Glean instance URL
- `your_cookie_string_here` with the cookies from step 1

### 3. Alternative: Local Installation

If you prefer not to use Docker:

```bash
# Install the server
pip install -r requirements.txt

# Set environment variables
export GLEAN_BASE_URL=https://your-company.glean.com
export GLEAN_COOKIES="your_cookie_string"

# Configure MCP to use local installation
```

```json
{
  "mcp": {
    "mcpServers": {
      "glean": {
        "command": "python",
        "args": ["/path/to/glean-mcp-server/src/glean_mcp_server.py"],
        "env": {
          "GLEAN_BASE_URL": "https://your-company.glean.com",
          "GLEAN_COOKIES": "your_cookie_string_here"
        }
      }
    }
  }
}
```

## 🔄 Upgrading to Latest Version

The configuration above uses `--pull always` to automatically get the latest container release. To upgrade:

1. **Restart Cursor/VS Code** - The next search will automatically pull the latest image
2. **Manual update** (optional): `docker pull ghcr.io/alankyshum/glean-mcp-server:latest`

For specific versions, replace `:latest` with `:v1.1.0` or your desired version tag.

## Usage

Once configured, you can search your Glean knowledge base directly from Cursor/VS Code:

- **Tool name:** `glean_search`
- **Parameters:**
  - `query` (required): Your search query
  - `page_size` (optional): Number of results (default: 14)
  - `max_snippet_size` (optional): Snippet size (default: 215)

## Configuration Options

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `GLEAN_BASE_URL` | **Yes** | - | Your Glean instance URL |
| `GLEAN_COOKIES` | **Yes** | - | Authentication cookies from browser |
| `GLEAN_TOOL_DESCRIPTION` | No | `"Search for internal company information"` | Custom description for the search tool |
| `GLEAN_DEFAULT_PAGE_SIZE` | No | `14` | Default number of search results |
| `GLEAN_DEFAULT_SNIPPET_SIZE` | No | `215` | Default snippet size for results |
| `GLEAN_AUTO_OPEN_BROWSER` | No | `true` | Automatically open browser when cookies expire |

### Example with Custom Description
```json
{
  "mcp": {
    "mcpServers": {
      "glean": {
        "command": "docker",
        "args": [
          "run", "--rm", "-i",
          "-e", "GLEAN_BASE_URL=https://acme.glean.com",
          "-e", "GLEAN_COOKIES=your_cookie_string_here",
          "-e", "GLEAN_TOOL_DESCRIPTION=Search ACME Corp's internal knowledge base",
          "-e", "GLEAN_DEFAULT_PAGE_SIZE=20",
          "ghcr.io/alankyshum/glean-mcp-server:latest"
        ]
      }
    }
  }
}
```

## Testing Your Setup

Before using in Cursor/VS Code, test your configuration:

```bash
# Copy and edit the environment file
cp .env.example .env
# Edit .env with your Glean URL and cookies

# Test the connection
python test_server.py
```

## 🍪 Cookie Management

Glean cookies expire weekly. Here are tools to make renewal easier:

### Quick Cookie Renewal

```bash
# 1. Check if cookies are still valid
python scripts/check-cookies.py

# 2. Extract new cookies from browser
# - Go to your Glean instance in browser
# - Open Developer Tools (F12) → Network tab
# - Perform a search → Right-click API request → Copy as cURL
# - Extract Cookie header value

# 3. Update cookies automatically
python scripts/update-cookies.py "your_new_cookie_string_here"
```

### Automated Monitoring

Set up automatic cookie health checks:

```bash
# Check cookie status manually
python scripts/cookie-reminder.py

# Set up daily automatic checks (optional)
python scripts/cookie-reminder.py --setup-cron
```



## Troubleshooting

### Authentication Issues
- **Cookies expired**: Run `python scripts/check-cookies.py` to verify
- **Quick renewal**: Use `python scripts/update-cookies.py "new_cookies"`
- Verify your Glean URL is correct
- Check that you have access to the Glean instance

### Docker Issues
- Make sure Docker is running
- Pull the latest image: `docker pull ghcr.io/alankyshum/glean-mcp-server:latest`

### MCP Configuration Issues
- Restart Cursor/VS Code after configuration changes
- Check the MCP settings file path is correct for your OS
- Verify JSON syntax is valid

## 🚀 Performance Optimization

This server includes advanced response filtering that dramatically improves performance:

- **85-98% smaller responses** compared to raw Glean API
- **Faster search results** with reduced data transfer
- **Clean, focused data** with only relevant information
- **Preserved functionality** - all useful content and metadata retained

Example compression:
```
Query: "documentation"
Raw response: 195,593 characters → Filtered: 2,994 characters (98.5% reduction)
```

For more details, see [FILTERING.md](FILTERING.md).

## 🧪 Testing and Development

Test the filtering and API functionality:

```bash
# Test with default queries
python3 scripts/test_and_filter.py

# Test specific queries
python3 scripts/test_and_filter.py "machine learning" "kubernetes"

# Customize result size
python3 scripts/test_and_filter.py "query" --page-size 10 --snippet-size 300
```
