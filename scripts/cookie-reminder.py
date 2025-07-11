#!/usr/bin/env python3
"""
Cookie reminder script for Glean MCP Server.

This script can be scheduled (via cron/Task Scheduler) to remind you
when cookies need renewal.
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def load_dotenv():
    """Simple .env file loader."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    except FileNotFoundError:
        return False



def send_desktop_notification(title: str, message: str):
    """Send desktop notification."""
    try:
        if sys.platform == 'darwin':  # macOS
            os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
        elif sys.platform == 'linux':  # Linux
            os.system(f'notify-send "{title}" "{message}"')
        elif sys.platform == 'win32':  # Windows
            import subprocess
            subprocess.run(['powershell', '-Command', f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'])
        return True
    except Exception:
        return False

async def check_and_notify():
    """Check cookie status and send notifications if needed."""
    load_dotenv()

    # Check if .env file exists and get its age
    env_file = Path('.env')
    if not env_file.exists():
        print("No .env file found - nothing to check")
        return

    mtime = datetime.fromtimestamp(env_file.stat().st_mtime)
    age = datetime.now() - mtime

    # Check if cookies are likely expired (>7 days)
    if age.days >= 7:
        title = "🚨 Glean Cookies Expired"
        message = f"Your Glean MCP cookies are {age.days} days old and likely expired. Please renew them."

        print(f"ALERT: {message}")
        send_desktop_notification(title, message)

    elif age.days >= 6:  # Warn 1 day before expiry
        title = "⚠️ Glean Cookies Expiring Soon"
        message = f"Your Glean MCP cookies are {age.days} days old and will expire soon."

        print(f"WARNING: {message}")
        send_desktop_notification(title, message)

    else:
        print(f"Cookies are {age.days} days old - still valid")

    # Also test actual connectivity
    try:
        from glean_client import GleanClient

        base_url = os.getenv("GLEAN_BASE_URL")
        cookies = os.getenv("GLEAN_COOKIES")

        if base_url and cookies:
            client = GleanClient(base_url=base_url, cookies=cookies)
            result = await client.search("test", page_size=1, max_snippet_size=50)
            await client.close()

            if not result or 'results' not in result:
                title = "🚨 Glean Connection Failed"
                message = "Glean MCP cookies appear to be invalid - connection test failed."
                print(f"ERROR: {message}")
                send_desktop_notification(title, message)
    except Exception as e:
        if 'unauthorized' in str(e).lower() or '401' in str(e) or '403' in str(e):
            title = "🚨 Glean Authentication Failed"
            message = "Glean MCP authentication failed - cookies need renewal."
            print(f"ERROR: {message}")
            send_desktop_notification(title, message)

def setup_cron_job():
    """Help set up a cron job for automatic checking."""
    script_path = Path(__file__).absolute()
    python_path = sys.executable

    cron_command = f"0 9 * * * {python_path} {script_path}"

    print("To set up automatic daily checking, add this to your crontab:")
    print(f"  {cron_command}")
    print("\nRun 'crontab -e' and add the line above.")
    print("This will check cookies every day at 9 AM.")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--setup-cron':
        setup_cron_job()
        return

    print(f"🍪 Cookie reminder check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        asyncio.run(check_and_notify())
    except Exception as e:
        print(f"Error during check: {e}")

if __name__ == "__main__":
    main()
