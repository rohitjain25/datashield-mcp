#!/usr/bin/env python3
"""
DataShield MCP Command Line Interface
"""
import argparse
import sys
import os
from .server import main

def cli():
    parser = argparse.ArgumentParser(
        description="DataShield MCP - Local data cleaning and privacy toolkit"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="DataShield MCP v0.1.0",
    )
    parser.add_argument(
        "--help-mcp",
        action="store_true",
        help="Show MCP server help and start the server",
    )
    args = parser.parse_args()
    if args.help_mcp:
        print("Starting DataShield MCP server...")
        print("Use with Claude Desktop, Claude Code, or other MCP clients.")
        print("Server will run on stdio.")
        print()
    # Run the MCP server
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down DataShield MCP...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()