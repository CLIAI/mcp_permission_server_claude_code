#!/usr/bin/env python3
"""
Script to set up an MCP tool for Claude Code from a specified script file.
This script is used inside the Docker container to register a Python script as an MCP tool.

Note: The '--prompt-permission-tool' flag might be buggy and may require the tool name 
to include both the server name and tool name (e.g., 'mcp__server_name__tool_name'). 
If you encounter errors, check the server error messages for the expected format.
"""

import argparse
import os
import sys
import tempfile
import json
import subprocess
import shutil
from pathlib import Path

def create_parser():
    parser = argparse.ArgumentParser(description='Set up a script as an MCP tool for Claude Code')
    parser.add_argument('script_path', type=str, help='Path to the script to register as an MCP tool')
    parser.add_argument('--tool-name', type=str, help='Name for the MCP tool (default: derived from filename)')
    parser.add_argument('--server-name', type=str, default='mcp_permission_server', 
                        help='Name for the MCP server (default: mcp_permission_server)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    return parser

def derive_tool_name(script_path):
    """Derive a tool name from the script filename."""
    return Path(script_path).stem.lower().replace(' ', '_')

def create_mcp_tool(script_path, tool_name, server_name, debug=False):
    """Create an MCP tool from the given script."""
    # Ensure the script exists
    script_path = os.path.abspath(script_path)
    if not os.path.isfile(script_path):
        print(f"Error: Script not found: {script_path}")
        return False
    
    # Make script executable if it's not already
    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, 0o755)
    
    # Derive tool name if not provided
    if not tool_name:
        tool_name = derive_tool_name(script_path)
    
    # The full tool name for registration
    full_tool_name = f"{server_name}__{tool_name}"
    
    if debug:
        print(f"Registering script: {script_path}")
        print(f"Tool name: {full_tool_name}")
    
    # Create symlink to the script in a predictable location
    home_dir = os.path.expanduser("~")
    mcp_tools_dir = os.path.join(home_dir, ".claude-code", "mcp_tools")
    os.makedirs(mcp_tools_dir, exist_ok=True)
    
    # The target path for the symlink
    target_path = os.path.join(mcp_tools_dir, full_tool_name)
    
    # Remove existing symlink if it exists
    if os.path.exists(target_path):
        if os.path.islink(target_path):
            os.unlink(target_path)
        else:
            print(f"Error: {target_path} exists and is not a symlink")
            return False
    
    # Create the symlink
    os.symlink(script_path, target_path)
    
    print(f"Successfully registered MCP tool: {full_tool_name}")
    print(f"To use in Claude Code: '--prompt-permission-tool={full_tool_name}'")
    
    # Note about potential issues
    print("\nNote: If you encounter errors with the '--prompt-permission-tool' flag, check if:")
    print("1. The server name in the error message matches what you provided")
    print("2. The tool name format needs adjustment (e.g., with or without server name prefix)")
    
    return True

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    success = create_mcp_tool(
        args.script_path, 
        args.tool_name, 
        args.server_name,
        args.debug
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())