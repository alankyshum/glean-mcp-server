#!/usr/bin/env python3
"""
Extract cookies from a cURL command for easy MCP server configuration.

This script helps users extract the Cookie header from a cURL command
copied from browser Developer Tools.
"""
import re
import sys
import argparse

def extract_cookies_from_curl(curl_command):
    """Extract cookies from a cURL command."""
    # Look for -H 'Cookie: ...' or -H "Cookie: ..." patterns
    cookie_patterns = [
        r"-H\s+['\"]Cookie:\s*([^'\"]+)['\"]",
        r"--header\s+['\"]Cookie:\s*([^'\"]+)['\"]",
        r"-b\s+['\"]([^'\"]+)['\"]",
        r"--cookie\s+['\"]([^'\"]+)['\"]"
    ]
    
    for pattern in cookie_patterns:
        match = re.search(pattern, curl_command, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Extract cookies from cURL command for Glean MCP server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from cURL command
  python scripts/extract-cookies-from-curl.py "curl 'https://...' -H 'Cookie: abc=123; def=456'"
  
  # Read from file
  python scripts/extract-cookies-from-curl.py --file curl_command.txt
  
  # Interactive mode
  python scripts/extract-cookies-from-curl.py --interactive
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('curl_command', nargs='?', help='cURL command string')
    group.add_argument('--file', '-f', help='Read cURL command from file')
    group.add_argument('--interactive', '-i', action='store_true', 
                      help='Interactive mode - paste cURL command')
    
    args = parser.parse_args()
    
    # Get cURL command from different sources
    if args.curl_command:
        curl_text = args.curl_command
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                curl_text = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return 1
    elif args.interactive:
        print("🍪 Glean Cookie Extractor")
        print("=" * 30)
        print("Paste your cURL command below (press Ctrl+D when done):")
        print()
        try:
            curl_text = sys.stdin.read()
        except KeyboardInterrupt:
            print("\n👋 Cancelled by user")
            return 0
    
    # Extract cookies
    cookies = extract_cookies_from_curl(curl_text)
    
    if cookies:
        print("✅ Cookies extracted successfully!")
        print()
        print("📋 Cookie string:")
        print("-" * 50)
        print(cookies)
        print("-" * 50)
        print()
        print("💡 Usage:")
        print(f'python scripts/update-cookies.py "{cookies}"')
        print()
        print("Or manually update your .env file:")
        print(f'GLEAN_COOKIES={cookies}')
        
        # Try to copy to clipboard if possible
        try:
            import pyperclip
            pyperclip.copy(cookies)
            print("\n📋 Cookies copied to clipboard!")
        except ImportError:
            print("\n💡 Install pyperclip for automatic clipboard copying:")
            print("pip install pyperclip")
        
        return 0
    else:
        print("❌ No cookies found in the cURL command")
        print()
        print("💡 Make sure your cURL command includes:")
        print("   -H 'Cookie: ...' or -b '...'")
        print()
        print("🔍 How to get the correct cURL command:")
        print("1. Go to your Glean instance in browser")
        print("2. Open Developer Tools (F12) → Network tab")
        print("3. Perform a search in Glean")
        print("4. Find any search API request")
        print("5. Right-click → Copy → Copy as cURL")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
