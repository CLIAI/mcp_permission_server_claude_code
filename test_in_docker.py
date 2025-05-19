#!/usr/bin/env python3
"""
Script to run a file inside the Claude Code Docker container.
This script mounts a single file into the container and runs it with Claude Code.

Usage:
    python test_in_docker.py script_file [--tool-name NAME] [--server-name NAME] [--debug] [--skip-build]

Example:
    python test_in_docker.py my_mcp_server.py --tool-name custom_tool
"""

import argparse
import os
import sys
import subprocess
import tempfile
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Run a script in the Claude Code Docker container')
    parser.add_argument('script_file', help='Script file to run in the container')
    parser.add_argument('--tool-name', help='Custom name for the MCP tool (default: derived from filename)')
    parser.add_argument('--server-name', default='mcp_permission_server', 
                        help='Server name for the MCP tool (default: mcp_permission_server)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--skip-build', action='store_true', help='Skip building the Docker image')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--claude-args', default='', help='Additional arguments to pass to Claude Code')
    
    return parser.parse_args()

def check_api_key():
    """Check if the ANTHROPIC_API_KEY environment variable is set."""
    if 'ANTHROPIC_API_KEY' not in os.environ:
        print("Error: ANTHROPIC_API_KEY environment variable is not set")
        print("You must set your Anthropic API key to use Claude Code")
        print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
        return False
    return True

def build_docker_image(debug=False):
    """Build the Docker image using make."""
    cmd = ["make", "build"]
    if debug:
        print(f"Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")
        return False

def run_in_docker(script_file, tool_name=None, server_name='mcp_permission_server', 
                  debug=False, interactive=False, claude_args=''):
    """Run the script in the Docker container."""
    script_path = os.path.abspath(script_file)
    
    # Check if the script path exists
    if not os.path.exists(script_path):
        print(f"Error: Path not found: {script_path}")
        return False
    
    # Get the script filename
    script_filename = os.path.basename(script_path)
    
    # Handle different paths based on file or directory
    if os.path.isfile(script_path):
        # For regular files, mount the file directly
        mount_arg = f"{script_path}:/home/coder/workspace/{script_filename}"
        target_path = f"/home/coder/workspace/{script_filename}"
    elif os.path.isdir(script_path):
        # For directories, mount the entire directory
        mount_arg = f"{script_path}:/home/coder/workspace/{script_filename}"
        
        # Find executable files in the directory
        executable_files = []
        for root, _, files in os.walk(script_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.access(file_path, os.X_OK):
                    # Get path relative to script_path
                    rel_path = os.path.relpath(file_path, script_path)
                    executable_files.append(rel_path)
        
        if not executable_files:
            print(f"Error: No executable files found in directory: {script_path}")
            print("Make sure at least one file has executable permissions.")
            return False
            
        # Use the first executable file found
        if len(executable_files) > 1:
            print(f"Multiple executable files found in {script_path}. Using {executable_files[0]}")
        
        target_path = f"/home/coder/workspace/{script_filename}/{executable_files[0]}"
    else:
        print(f"Error: Path is neither a file nor a directory: {script_path}")
        return False
    
    if debug:
        print(f"Using target path in container: {target_path}")
    
    # Construct the command to run inside Docker
    if tool_name or server_name != 'mcp_permission_server':
        # If custom tool or server name is specified, use the setup script
        tool_args = []
        if tool_name:
            tool_args.extend(["--tool-name", tool_name])
        if server_name:
            tool_args.extend(["--server-name", server_name])
        
        setup_cmd = f"python /opt/claude-code/setup_mcp_tool.py {target_path} {' '.join(tool_args)}"
        full_tool_name = f"{server_name}__{tool_name or Path(script_file).stem.lower().replace(' ', '_')}"
        run_cmd = f"claude-code {claude_args} --dangerously-skip-permissions --prompt-permission-tool={full_tool_name}"
        cmd_in_container = f"{setup_cmd} && {run_cmd}"
    else:
        # Just run the script with Claude Code
        cmd_in_container = f"claude-code {claude_args} --dangerously-skip-permissions {target_path}"
    
    # Build the docker run command
    docker_cmd = [
        "docker", "run", 
        "--rm",
        "-v", mount_arg,
        "-e", f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}",
    ]
    
    if interactive:
        docker_cmd.extend(["-it"])
    
    docker_cmd.extend(["claude-code-container", "/bin/bash", "-c", cmd_in_container])
    
    if debug:
        print(f"Running command: {' '.join(docker_cmd)}")
    
    try:
        subprocess.run(docker_cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Docker container: {e}")
        return False
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return False

def main():
    args = parse_args()
    
    if not check_api_key():
        return 1
    
    if not args.skip_build:
        if not build_docker_image(args.debug):
            return 1
    
    if not run_in_docker(
        args.script_file, 
        args.tool_name, 
        args.server_name, 
        args.debug,
        args.interactive,
        args.claude_args
    ):
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())