#!/usr/bin/env python3
"""
Easy cookie renewal script for Glean MCP Server.

This script helps you quickly update expired cookies without manually editing files.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

def update_env_file(cookies: str, env_path: str = ".env"):
    """Update the .env file with new cookies."""
    env_file = Path(env_path)
    
    if not env_file.exists():
        print(f"Creating new .env file at {env_file}")
        with open(env_file, 'w') as f:
            f.write("# Glean MCP Server Configuration\n")
            f.write("GLEAN_BASE_URL=https://your-company.glean.com\n")
            f.write(f"GLEAN_COOKIES={cookies}\n")
        return
    
    # Read existing file
    lines = []
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add cookies line
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('GLEAN_COOKIES='):
            lines[i] = f"GLEAN_COOKIES={cookies}\n"
            updated = True
            break
    
    if not updated:
        lines.append(f"GLEAN_COOKIES={cookies}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated cookies in {env_file}")

def update_docker_compose(cookies: str, compose_path: str = "docker-compose.yml"):
    """Update docker-compose.yml environment variables."""
    compose_file = Path(compose_path)
    
    if not compose_file.exists():
        print(f"❌ Docker compose file not found at {compose_file}")
        return
    
    # For docker-compose, we typically use .env file
    # So just update the .env file
    print("💡 Docker Compose uses .env file - cookies updated there")

def restart_docker_container():
    """Restart the docker container to pick up new cookies."""
    try:
        # Check if container is running
        result = subprocess.run(['docker', 'ps', '--filter', 'name=glean-mcp-server', '--format', '{{.Names}}'], 
                              capture_output=True, text=True)
        
        if 'glean-mcp-server' in result.stdout:
            print("🔄 Restarting Docker container...")
            subprocess.run(['docker-compose', 'restart', 'glean-mcp-server'], check=True)
            print("✅ Container restarted")
        else:
            print("💡 Container not running - start it with: docker-compose up -d")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restart container: {e}")
    except FileNotFoundError:
        print("❌ Docker or docker-compose not found")

def test_connection():
    """Test the connection with new cookies."""
    try:
        print("🧪 Testing connection...")
        result = subprocess.run([sys.executable, 'scripts/test_and_filter.py', 'test', '--no-save'], 
                              capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Connection test successful!")
        else:
            print(f"❌ Connection test failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Could not run test: {e}")

def main():
    parser = argparse.ArgumentParser(description='Update Glean MCP Server cookies')
    parser.add_argument('cookies', help='New cookie string from browser')
    parser.add_argument('--env-file', default='.env', help='Path to .env file (default: .env)')
    parser.add_argument('--no-restart', action='store_true', help='Don\'t restart Docker container')
    parser.add_argument('--no-test', action='store_true', help='Don\'t test connection')
    
    args = parser.parse_args()
    
    print("🍪 Updating Glean MCP Server cookies...")
    print(f"Cookie length: {len(args.cookies)} characters")
    
    # Update .env file
    update_env_file(args.cookies, args.env_file)
    
    # Update docker-compose reference
    update_docker_compose(args.cookies)
    
    # Restart container if requested
    if not args.no_restart:
        restart_docker_container()
    
    # Test connection if requested
    if not args.no_test:
        test_connection()
    
    print("\n🎉 Cookie update complete!")
    print("\n📝 Next steps:")
    print("1. If using Docker: Container should restart automatically")
    print("2. If using local installation: Restart your MCP client (Cursor/VS Code)")
    print("3. Test with a search query in your editor")
    print("\n💡 To get new cookies in the future:")
    print("1. Go to your Glean instance in browser")
    print("2. Open Developer Tools (F12) → Network tab")
    print("3. Perform a search in Glean")
    print("4. Right-click any search API request → Copy as cURL")
    print("5. Extract Cookie header and run this script again")

if __name__ == "__main__":
    main()
