# Glean MCP Server

A Docker-based Model Context Protocol (MCP) server that provides search functionality for Glean knowledge bases.

## Features

- 🔍 **Search Integration**: Full-featured search against Glean API
- 🐳 **Docker Support**: Containerized deployment with multi-architecture support
- 🚀 **GitHub Actions**: Automated CI/CD pipeline for Docker image publishing
- 🔧 **Environment Configuration**: Easy setup with environment variables
- 📊 **MCP Protocol**: Standard MCP interface for AI assistant integration

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Access to a Glean instance
- Valid authentication cookies

### 1. Clone and Setup

```bash
git clone https://github.com/alankyshum/glean-mcp-server.git
cd glean-mcp-server
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your Glean instance details:

```bash
# Your Glean instance base URL
GLEAN_BASE_URL=https://your-company.glean.com

# Authentication cookies from browser
GLEAN_COOKIES=your_cookie_string_here
```

### 3. Get Authentication Cookies

1. Open your browser and navigate to your Glean instance
2. Open Developer Tools (F12)
3. Go to Network tab
4. Perform a search in Glean
5. Find the search API request
6. Copy the entire `Cookie` header value
7. Paste it as the `GLEAN_COOKIES` value in your `.env` file

### 4. Run with Docker Compose

Using the pre-built image (recommended):
```bash
docker-compose up -d
```

For local development with source code mounting:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 5. Use Pre-built Image from GitHub Container Registry

The easiest way to use this server is with the pre-built image:

```bash
docker run -d \
  --name glean-mcp-server \
  -e GLEAN_BASE_URL=https://your-company.glean.com \
  -e GLEAN_COOKIES="your_cookie_string" \
  ghcr.io/alankyshum/glean-mcp-server:latest
```

Available tags:
- `latest` - Latest stable release from main branch
- `develop` - Latest development build
- `v1.0.0` - Specific version tags

## Usage

### MCP Tools

The server provides the following MCP tool:

#### `glean_search`

Search the Glean knowledge base.

**Parameters:**
- `query` (required): Search query string
- `page_size` (optional): Number of results (default: 14, max: 50)
- `max_snippet_size` (optional): Snippet size (default: 215, max: 1000)

**Example:**
```json
{
  "name": "glean_search",
  "arguments": {
    "query": "API documentation",
    "page_size": 10,
    "max_snippet_size": 300
  }
}
```

### MCP Resources

- `glean://search`: Information about search capabilities

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GLEAN_BASE_URL=https://your-company.glean.com
export GLEAN_COOKIES="your_cookie_string"

# Run the server
python src/glean_mcp_server.py
```

### Building Docker Image

```bash
docker build -t glean-mcp-server .
```

### Testing

```bash
# Test the server locally
python test_server.py

# Test with Docker
docker-compose up
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GLEAN_BASE_URL` | Yes | Base URL of your Glean instance |
| `GLEAN_COOKIES` | Yes | Authentication cookies |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

### Docker Configuration

The Docker image supports:
- Multi-architecture builds (amd64, arm64)
- Non-root user execution
- Health checks
- Proper signal handling

## GitHub Actions & Container Registry

The repository includes automated CI/CD that:
- ✅ Builds Docker images on push to main/develop branches
- ✅ Publishes to GitHub Container Registry (`ghcr.io/alankyshum/glean-mcp-server`)
- ✅ Multi-architecture support (amd64, arm64)
- ✅ Semantic versioning with tags (v1.0.0, v1.1.0, etc.)
- ✅ Build attestations for security
- ✅ Automated testing on pull requests

### Using the Container Registry

Pull the latest image:
```bash
docker pull ghcr.io/alankyshum/glean-mcp-server:latest
```

Run with your configuration:
```bash
docker run -d \
  --name glean-mcp-server \
  -e GLEAN_BASE_URL=https://your-company.glean.com \
  -e GLEAN_COOKIES="your_cookie_string" \
  ghcr.io/alankyshum/glean-mcp-server:latest
```

## Security Notes

⚠️ **Important**: Keep your authentication cookies secure and rotate them regularly.

- Cookies contain sensitive authentication information
- Use environment variables or secure secret management
- Never commit cookies to version control
- Consider implementing token refresh mechanisms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in this repository
- Check existing issues for solutions
- Provide detailed error messages and logs
