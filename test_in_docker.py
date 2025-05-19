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
    parser.add_argument('script_file', help='Script file or directory to run in the container')
    parser.add_argument('--tool-name', help='Custom name for the MCP tool (default: derived from filename)')
    parser.add_argument('--server-name', default='mcp_permission_server', 
                        help='Server name for the MCP tool (default: mcp_permission_server)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--skip-build', action='store_true', help='Skip building the Docker image')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--claude-args', default='', help='Additional arguments to pass to Claude Code')
    parser.add_argument('--skip-tool-setup', action='store_true', 
                        help='Skip MCP tool setup and just run Claude Code with the script')
    parser.add_argument('--show-docker-logs', action='store_true',
                        help='Show Docker build logs (can be verbose)')
    parser.add_argument('--run-directly', action='store_true',
                        help='Run the script directly without Docker')
    
    return parser.parse_args()

def check_api_key():
    """Check if the ANTHROPIC_API_KEY environment variable is set."""
    if 'ANTHROPIC_API_KEY' not in os.environ or not os.environ['ANTHROPIC_API_KEY'].strip():
        print("Error: ANTHROPIC_API_KEY environment variable is not set")
        print("You must set your Anthropic API key to use Claude Code")
        print("Example: export ANTHROPIC_API_KEY=your_api_key_here")
        return False
    
    # Don't print the actual key, just confirm it's set
    print("API key is set and ready to use")
    return True

def build_docker_image(debug=False, show_logs=False):
    """Build the Docker image using make."""
    cmd = ["make", "build"]
    if debug:
        print(f"Running: {' '.join(cmd)}")
    
    try:
        if show_logs:
            # Show full output
            subprocess.run(cmd, check=True)
        else:
            # Suppress output unless there's an error
            print("Building Docker image (this may take a while)...")
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error building Docker image: {result.stderr}")
                return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")
        return False

def run_in_docker(script_file, tool_name=None, server_name='mcp_permission_server', 
                  debug=False, interactive=False, claude_args='', skip_tool_setup=False):
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
    if skip_tool_setup:
        # Skip tool setup and just run Claude Code with the script
        cmd_in_container = f"claude-code {claude_args} --dangerously-skip-permissions {target_path}"
    elif tool_name or server_name != 'mcp_permission_server':
        # If custom tool or server name is specified, use the setup script
        tool_args = []
        if tool_name:
            tool_args.extend(["--tool-name", tool_name])
        if server_name:
            tool_args.extend(["--server-name", server_name])
        
        setup_cmd = f"python /opt/claude-code/setup_mcp_tool.py {target_path} {' '.join(tool_args)} --debug"
        full_tool_name = f"{server_name}__{tool_name or Path(script_file).stem.lower().replace(' ', '_')}"
        run_cmd = f"claude-code {claude_args} --dangerously-skip-permissions --prompt-permission-tool={full_tool_name}"
        cmd_in_container = f"{setup_cmd} && {run_cmd}"
    else:
        # Just run the script with Claude Code
        cmd_in_container = f"claude-code {claude_args} --dangerously-skip-permissions {target_path}"
    
    # Check if the Docker image exists
    check_image_cmd = ["docker", "image", "inspect", "claude-code-container"]
    image_exists = subprocess.run(check_image_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    
    if not image_exists:
        print("Docker image 'claude-code-container' does not exist. Building it now...")
        if not build_docker_image(debug, False):
            print("Failed to build Docker image. Please check the error messages above.")
            return False
    
    # Build the docker run command
    docker_cmd = [
        "docker", "run", 
        "--rm",
        "-v", mount_arg,
        "-e", f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}",
    ]
    
    if interactive:
        # Make sure we're in a TTY
        if sys.stdin.isatty() and sys.stdout.isatty():
            docker_cmd.extend(["-it"])
        else:
            print("Warning: Not running in a TTY, disabling interactive mode")
    
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

def run_directly(script_file, debug=False):
    """Run the script directly with Bash as a fallback."""
    script_path = os.path.abspath(script_file)
    
    if not os.path.exists(script_path):
        print(f"Error: Path not found: {script_path}")
        return False
    
    if os.path.isfile(script_path):
        # Make sure it's executable
        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)
                if debug:
                    print(f"Made script executable: {script_path}")
            except Exception as e:
                print(f"Warning: Could not make script executable: {e}")
        
        # Run the script directly
        print(f"Running script directly: {script_path}")
        try:
            subprocess.run([script_path], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running script: {e}")
            return False
    elif os.path.isdir(script_path):
        print(f"The path is a directory: {script_path}")
        print("Please specify a single executable file to run directly.")
        return False
    else:
        print(f"Error: Path is neither a file nor a directory: {script_path}")
        return False

def main():
    args = parse_args()
    
    if not check_api_key():
        return 1
    
    if args.run_directly:
        if run_directly(args.script_file, args.debug):
            return 0
        else:
            return 1
    
    if not args.skip_build:
        if not build_docker_image(args.debug, args.show_docker_logs):
            return 1
    
    if not run_in_docker(
        args.script_file, 
        args.tool_name, 
        args.server_name, 
        args.debug,
        args.interactive,
        args.claude_args,
        skip_tool_setup=args.skip_tool_setup
    ):
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())