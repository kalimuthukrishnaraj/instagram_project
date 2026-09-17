"""
Diagnostic script — checks what IG_ACCESS_TOKEN and IG_USER_ID actually
look like once loaded, WITHOUT printing the full secret values.

Run this from inside the instagram_service/ folder (same place as .env):
    python3 diagnose_env.py

Tip: run it in a fresh terminal window/tab, so any IG_ACCESS_TOKEN or
IG_USER_ID you `export`ed earlier in another session doesn't silently
override what's in your .env file.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    dotenv_loaded = True
except ImportError:
    dotenv_loaded = False
    print("(python-dotenv not installed — only checking already-exported "
          "env vars, not .env file. Run: pip install python-dotenv)\n")

if dotenv_loaded:
    print("python-dotenv loaded — checking for a .env file in this folder "
          "or parent folders.\n")


def inspect(name):
    value = os.environ.get(name, "")
    print(f"--- {name} ---")
    if not value:
        print("  NOT SET (empty or missing)\n")
        return

    print(f"  Length: {len(value)}")
    print(f"  First 6 chars: {value[:6]!r}")
    print(f"  Last 6 chars: {value[-6:]!r}")
    print(f"  Contains a double-quote character: {chr(34) in value}")
    print(f"  Contains a single-quote character: {chr(39) in value}")
    print(f"  Has leading/trailing whitespace: {value != value.strip()}")
    print(f"  Contains a newline: {chr(10) in value}")
    print()


inspect("IG_ACCESS_TOKEN")
inspect("IG_USER_ID")

print("Expected shape for reference:")
print("  IG_ACCESS_TOKEN: usually 150+ characters, starts with 'EAA'")
print("  IG_USER_ID: a plain numeric string, e.g. '17841400000000000'")
