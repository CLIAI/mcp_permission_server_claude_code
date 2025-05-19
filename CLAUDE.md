# MCP Permission Server - Claude Code Environment Guide

## Repository Overview

This repository contains experimental code for implementing custom security policies for Claude Code MCP (Model Control Panel) tools, along with a Docker environment for testing and development.

## MCP Servers

### Key Features

1. **Transport Layer**: MCP servers in this repository are designed to use stdio as the transport layer. This means they can communicate with Claude Code directly through standard input/output.

2. **Permission Implementation**: All MCP servers implement permission handling logic, with implementations ranging from simple "always allow" to more complex policies.

3. **FastMCP Framework**: Most servers use the FastMCP framework which provides a simple API for creating MCP servers.

### Example Servers

- `mcp_permission_server_allow_always_fastmcp`: A simple FastAPI implementation that always returns "allow" for permission checks.
- Other implementations explore different frameworks and approaches to permission handling.

## Docker Environment

The repository provides a Docker environment for isolated testing of Claude Code with MCP tools:

### Running With Docker

1. **Build the Docker Image**: 
   ```bash
   make build
   ```

2. **Run the Container**: 
   ```bash
   make run
   ```

3. **Test a Script**: 
   ```bash
   ./test_in_docker.py <script_path> [prompt] [options]
   ```

   The script accepts an optional prompt that will be passed to Claude Code. If not provided, it defaults to "write and compile and run helloworld in c++".

### Direct Execution

For development and testing, you can also run scripts directly:

```bash
./test_in_docker.py <script_path> --run-directly
```

## MCP Server Development

When developing MCP servers:

1. **Script Structure**: Each MCP server should be an executable script that implements the required permission-checking API.

2. **Tool Registration**: Use the `--prompt-permission-tool` flag with Claude Code to register a server.

3. **Debugging**: Use the `--debug` flag with test_in_docker.py for verbose output.

## Environment Variables

- **ANTHROPIC_API_KEY**: Required for Claude Code to function. Set this in your environment before running scripts.

## Best Practices

1. **Server Naming**: Follow the convention of prefixing server names with `mcp_permission_server_`.

2. **Docker Isolation**: Use the Docker environment for testing with `--dangerously-skip-permissions` to provide proper isolation.

3. **Script Dependencies**: Use the uv package manager as shown in the script headers.

4. **Testing Flow**: 
   - Start with direct execution for quick testing
   - Move to Docker testing for more realistic environments
   - Use the `--interactive` flag for debugging inside the container

## Known Issues

1. **Flag Behavior**: The `--prompt-permission-tool` flag may require the tool name to include both the server name and tool name (e.g., `mcp__server_name__tool_name`). Check server error messages for the expected format.

2. **Docker Build**: Building the Docker image can be slow the first time. Use `--skip-build` for subsequent runs.

3. **Transport Layer**: These MCP servers use stdio as the transport layer, which must be properly handled when running in different environments.

## Commands Cheatsheet

```bash
# Build Docker image
make build

# Run interactive container
make run

# Test a script in Docker with default prompt
./test_in_docker.py <script_path>

# Test with a custom prompt
./test_in_docker.py <script_path> "create a flask web server"

# Test with a custom tool name
./test_in_docker.py <script_path> --tool-name custom_tool

# Test with custom prompt and tool name
./test_in_docker.py <script_path> "implement a sorting algorithm" --tool-name custom_tool

# Run a script directly (without Docker)
./test_in_docker.py <script_path> --run-directly

# Debug mode with verbose output
./test_in_docker.py <script_path> --debug

# Skip Docker image building
./test_in_docker.py <script_path> --skip-build

# Show Docker build logs
./test_in_docker.py <script_path> --show-docker-logs
```