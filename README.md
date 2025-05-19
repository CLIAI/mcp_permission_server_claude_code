# MCP Permission Server - Claude Code in Docker

**WORK IN PROGRESS**: This repository contains experimental code for implementing custom security policies for Claude Code MCP (Model Control Panel) tools, along with a Docker environment for testing and development.

## Purpose

This project aims to:
1. Develop minimal working examples for MCP tool approval/denial servers that could serve as a foundation for implementing security policies
2. Provide a Docker-based environment for safely testing Claude Code with MCP tools
3. Allow isolated testing with the `--dangerously-skip-permissions` flag in a controlled environment

## Docker Environment

The repository now includes a fully configured Docker environment for running Claude Code with MCP tools:

### Requirements

- Docker installed on your system
- Anthropic API key (set as environment variable `ANTHROPIC_API_KEY`)

### Quick Start

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_api_key_here

# Build the Docker image
make build

# Run an interactive container with the current directory mounted
make run

# Test a specific script
make test-script SCRIPT=path/to/your/script.py
```

### Using the test_in_docker.py Script

The `test_in_docker.py` script provides a convenient way to run a file inside the Docker container:

```bash
# Basic usage
./test_in_docker.py your_script.py

# Run with a custom tool name
./test_in_docker.py your_script.py --tool-name custom_tool

# Run with a custom server name
./test_in_docker.py your_script.py --server-name my_server
```

### Important Note on `--prompt-permission-tool` Flag

The `--prompt-permission-tool` flag may require the tool name to include both the server name and tool name (e.g., `mcp__server_name__tool_name`). If you encounter errors, check the server error messages for the expected format.

## Directory Structure

The repository contains:

- `docker_configs/`: Configuration files for the Docker environment
  - `dot_bashrc`: Bash configuration for the container
  - `setup_mcp_tool.py`: Script to set up MCP tools in the container
- `specs/`: Specification documents
  - `how_we_do_dockerfiles.md`: Docker best practices documentation
- `Dockerfile`: Defines the Claude Code Docker environment
- `Makefile`: Provides targets for building and running the Docker environment
- `test_in_docker.py`: Helper script for testing files in the Docker environment
- MCP server implementations:
  - `mcp_permission_server_allow_always_fastmcp`: Simple FastAPI implementation intended to always allow tool use
  - `mcp_permission_server_fastmcp_another`: Alternative FastAPI implementation
  - `mcp_permission_server_fastmcp_with_typing`: FastAPI with explicit type definitions
  - `mcp_permission_server_genai_by_gemini`: Implementation using Gemini
  - `mcp_permission_server_genai_by_gemini_another`: Alternative Gemini implementation
  - `mcp_permission_server_genai_by_perplexity`: Implementation using Perplexity
  - `mcp_permission_server_return_json_string`: Simple server returning JSON strings

## Current Status

The Docker environment is ready for testing Claude Code with MCP tools. The MCP server implementations are still works in progress.

⚠️ **NOTE**: Some MCP server implementations might be non-functional due to lack of clear documentation and examples.

## Usage Examples

### Running an Interactive Session

```bash
# Start an interactive session with the current directory mounted
make run

# Inside the container
claude-code --dangerously-skip-permissions
```

### Testing an MCP Tool

```bash
# Create a simple MCP tool script
echo '#!/bin/bash
echo "This is a test MCP tool"
' > test_tool.sh
chmod +x test_tool.sh

# Test it in the Docker container
./test_in_docker.py test_tool.sh --tool-name test_tool
```

## Future Work

Plans for future development:
- Add more comprehensive MCP server implementations
- Improve error handling and debugging
- Add automated testing
- Enhance documentation based on findings

## Contributing

If you have insights on how to make these examples work or have successfully implemented an MCP permission server, please open an issue or submit a pull request with your findings.

## License

See the [LICENSE](LICENSE) file for details.