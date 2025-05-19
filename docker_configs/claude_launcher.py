#!/usr/bin/env python3
"""
Claude Launcher Script

A wrapper for Claude CLI that provides detailed debugging information,
ensures MCP servers are properly registered, and handles error codes.

Usage:
    claude_launcher.py [--debug] [--add-mcp] <script_path> [prompt]

Example:
    claude_launcher.py --debug --add-mcp my_script.py "generate a hello world"
"""

import os
import sys
import subprocess
import argparse
import time
import shutil
import textwrap
from pathlib import Path


class Logger:
    """Simple logger that prefixes messages with their level."""
    
    # ANSI color codes for terminal output
    COLORS = {
        "INFO": "\033[94m",     # Blue
        "DEBUG": "\033[96m",    # Cyan
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",    # Red
        "SUCCESS": "\033[92m",  # Green
        "RESET": "\033[0m"      # Reset
    }
    
    def __init__(self, debug=False):
        self.debug_enabled = debug
    
    def _log(self, level, message):
        """Log a message with the specified level prefix."""
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]
        
        # Handle multi-line messages by prefixing each line
        lines = message.split('\n')
        for line in lines:
            if line.strip():  # Skip empty lines
                print(f"{color}{level}:{reset} {line}")
    
    def info(self, message):
        """Log an informational message."""
        self._log("INFO", message)
    
    def debug(self, message):
        """Log a debug message if debug mode is enabled."""
        if self.debug_enabled:
            self._log("DEBUG", message)
    
    def warning(self, message):
        """Log a warning message."""
        self._log("WARNING", message)
    
    def error(self, message):
        """Log an error message."""
        self._log("ERROR", message)
    
    def success(self, message):
        """Log a success message."""
        self._log("SUCCESS", message)


def run_command(cmd, logger, cwd=None):
    """
    Execute a shell command, print it prefixed with '$', and stream
    both stdout and stderr to the current terminal in real-time.
    Returns the subprocess return code.
    """
    logger.info(f"$ {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,         # line-buffered
        universal_newlines=True
    )

    # Stream output live
    while True:
        out_line = process.stdout.readline()
        err_line = process.stderr.readline()

        if out_line:
            print(out_line, end="")
        if err_line:
            logger.error(err_line.rstrip())

        if process.poll() is not None:
            # flush remaining
            for line in process.stdout:
                print(line, end="")
            for line in process.stderr:
                logger.error(line.rstrip())
            break

    return process.returncode


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Claude CLI Launcher with verbose debugging")
    parser.add_argument("script_path", help="Path to the script to run")
    parser.add_argument("prompt", nargs='?', default="write and compile and run helloworld in c++",
                        help="Prompt to send to Claude (default: write and compile and run helloworld in c++)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--add-mcp", action="store_true", help="Add script as MCP tool before running")
    parser.add_argument("--tool-name", help="Custom name for the MCP tool (default: derived from filename)")
    parser.add_argument("--server-name", default="mcp_permission_server", 
                     help="Server name for the MCP tool (default: mcp_permission_server)")
    parser.add_argument("--claude-path", default="claude", help="Path to the Claude executable")
    parser.add_argument("--claude-args", default="", help="Additional arguments to pass to Claude")
    return parser.parse_args()


def validate_script(script_path, logger):
    """Validate that the script exists, is readable, and has the proper permissions."""
    path = Path(script_path)
    
    # Check if file exists
    if not path.exists():
        logger.error(f"Script does not exist: {script_path}")
        return False
    
    # Check if it's a file (not a directory)
    if not path.is_file():
        logger.error(f"Script path is not a file: {script_path}")
        return False
    
    # Check if the file is readable
    if not os.access(script_path, os.R_OK):
        logger.error(f"Script is not readable: {script_path}")
        return False
    
    # Check if the file is executable
    if not os.access(script_path, os.X_OK):
        logger.warning(f"Script is not executable: {script_path}")
        try:
            os.chmod(script_path, 0o755)
            logger.info(f"Made script executable: {script_path}")
        except Exception as e:
            logger.error(f"Failed to make script executable: {e}")
            return False
    
    # Check if file is non-zero size
    if path.stat().st_size == 0:
        logger.error(f"Script file is empty: {script_path}")
        return False
    
    logger.success(f"Script validation successful: {script_path}")
    return True


def add_mcp_tool(script_path, tool_name, server_name, logger):
    """Add the script as an MCP tool."""
    # Derive tool name if not provided
    if not tool_name:
        tool_name = Path(script_path).stem.lower().replace(' ', '_')
    
    # The full tool name for registration
    full_tool_name = f"{server_name}__{tool_name}"
    
    # Create symlink to the script in a predictable location
    home_dir = os.path.expanduser("~")
    mcp_tools_dir = os.path.join(home_dir, ".claude-code", "mcp_tools")
    
    try:
        os.makedirs(mcp_tools_dir, exist_ok=True)
        logger.debug(f"MCP tools directory: {mcp_tools_dir}")
    except Exception as e:
        logger.error(f"Failed to create MCP tools directory: {e}")
        return False
    
    # The target path for the symlink
    target_path = os.path.join(mcp_tools_dir, full_tool_name)
    
    # Remove existing symlink if it exists
    if os.path.exists(target_path):
        if os.path.islink(target_path):
            try:
                os.unlink(target_path)
                logger.debug(f"Removed existing symlink: {target_path}")
            except Exception as e:
                logger.error(f"Failed to remove existing symlink: {e}")
                return False
        else:
            logger.error(f"Path exists and is not a symlink: {target_path}")
            return False
    
    # Create the symlink
    try:
        os.symlink(os.path.abspath(script_path), target_path)
        logger.debug(f"Created symlink: {target_path} -> {script_path}")
        
        if os.path.exists(target_path):
            logger.debug(f"Symlink verification passed: {os.readlink(target_path)}")
        else:
            logger.error("Symlink creation failed")
            return False
    except Exception as e:
        logger.error(f"Failed to create symlink: {e}")
        return False
    
    logger.success(f"Successfully registered MCP tool: {full_tool_name}")
    return True


def run_claude(script_path, prompt, add_mcp, tool_name, server_name, logger, 
               claude_path="claude", claude_args=""):
    """Run Claude with the specified script and prompt."""
    # Determine tool name and full MCP identifier
    if not tool_name:
        derived_tool_name = Path(script_path).stem.lower().replace(' ', '_')
    else:
        derived_tool_name = tool_name
    full_tool_name = f"{server_name}__{derived_tool_name}"

    #
    # 1. When requested, register the script as MCP tool
    #
    if add_mcp:
        add_cmd = [
            claude_path, "mcp", "add",
            "--transport", "stdio",
            full_tool_name,
            script_path,
        ]
        if run_command(add_cmd, logger) != 0:
            logger.error("Failed to add MCP tool")
            return 1

        #
        # 2. Show MCP tool list to verify registration
        #
        list_cmd = [claude_path, "mcp", "list"]
        if run_command(list_cmd, logger) != 0:
            logger.error("Failed to list MCP tools")
            return 1

    #
    # 3. Build the final Claude invocation
    #
    if add_mcp:
        cmd = [
            claude_path,
            "--dangerously-skip-permissions",
            "--prompt-permission-tool", full_tool_name,
            "--print", prompt,
        ]
    else:
        cmd = [
            claude_path,
            "--dangerously-skip-permissions",
            "--print", prompt,
            script_path,
        ]

    # Append extra CLI args if any
    if claude_args:
        cmd.extend(claude_args.split())

    logger.info(f"Executing Claude with {len(prompt)}-character prompt")
    logger.debug(f"Final command: {' '.join(cmd)}")

    # Run and stream output
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line buffered
        universal_newlines=True
    )
    
    # Track stdout and stderr separately
    stdout_lines = []
    stderr_lines = []
    
    # Read stdout and stderr in real-time
    while True:
        stdout_line = process.stdout.readline()
        stderr_line = process.stderr.readline()
        
        if stdout_line:
            stdout_lines.append(stdout_line.rstrip())
            print(stdout_line, end='')
        if stderr_line:
            stderr_lines.append(stderr_line.rstrip())
            logger.error(stderr_line.rstrip())
            
        # Check if process has finished
        if process.poll() is not None:
            # Get any remaining output
            for line in process.stdout:
                stdout_lines.append(line.rstrip())
                print(line, end='')
            for line in process.stderr:
                stderr_lines.append(line.rstrip())
                logger.error(line.rstrip())
            break
    
    # Get the return code
    return_code = process.returncode
    
    # Log execution results
    if return_code == 0:
        logger.success(f"Claude execution completed successfully")
    else:
        logger.error(f"Claude execution failed with code: {return_code}")
    
    # Return non-zero exit code if Claude failed
    return return_code


def main():
    """Main function."""
    args = parse_args()
    
    # Initialize logger
    logger = Logger(debug=args.debug)
    logger.info(f"Claude Launcher starting")
    
    # Check if ANTHROPIC_API_KEY is set
    if 'ANTHROPIC_API_KEY' not in os.environ or not os.environ['ANTHROPIC_API_KEY'].strip():
        logger.error("ANTHROPIC_API_KEY environment variable is not set")
        return 1
    else:
        logger.info("ANTHROPIC_API_KEY is set")
    
    # Check if Claude is in the PATH
    claude_executable = shutil.which(args.claude_path)
    if not claude_executable:
        logger.error(f"Claude executable not found: {args.claude_path}")
        return 1
    else:
        logger.debug(f"Found Claude executable: {claude_executable}")
    
    # Validate the script
    if not validate_script(args.script_path, logger):
        return 1
    
    # Add as MCP tool if requested
    if args.add_mcp:
        logger.info(f"Adding script as MCP tool: {args.script_path}")
        if not add_mcp_tool(args.script_path, args.tool_name, args.server_name, logger):
            return 1
    
    # Run Claude with the script
    return_code = run_claude(
        args.script_path, 
        args.prompt, 
        args.add_mcp, 
        args.tool_name, 
        args.server_name,
        logger,
        args.claude_path,
        args.claude_args
    )
    
    # Return Claude's exit code
    return return_code


if __name__ == "__main__":
    sys.exit(main())
